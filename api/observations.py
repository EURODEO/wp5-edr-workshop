from typing import Annotated

from covjson_pydantic.coverage import Coverage
from covjson_pydantic.domain import Axes
from covjson_pydantic.domain import Domain
from covjson_pydantic.domain import DomainType
from covjson_pydantic.domain import ValuesAxis
from covjson_pydantic.ndarray import NdArray
from covjson_pydantic.observed_property import ObservedProperty
from covjson_pydantic.parameter import Parameter
from covjson_pydantic.reference_system import ReferenceSystem
from covjson_pydantic.reference_system import ReferenceSystemConnectionObject
from covjson_pydantic.unit import Unit
from edr_pydantic.parameter import EdrBaseModel
from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import Path
from fastapi import Query
from geojson_pydantic import FeatureCollection
from pydantic import AwareDatetime
from starlette.responses import JSONResponse

from api.util import split_raw_interval_into_start_end_datetime
from api.util import split_string_parameters_to_list
from data.data import get_data
from data.data import get_station
from data.data import get_variables

router = APIRouter(prefix="/collections/observations")


class CoverageJsonResponse(JSONResponse):
    media_type = "application/prs.coverage+json"


class GeoJsonResponse(JSONResponse):
    media_type = "application/geo+json"


class EDRFeatureCollection(EdrBaseModel, FeatureCollection):
    parameters: dict[str, Parameter]


def get_reference_system() -> list[ReferenceSystemConnectionObject]:
    geo_reference_system = ReferenceSystem(type="GeographicCRS", id="http://www.opengis.net/def/crs/EPSG/0/4326")
    geo_referencing = ReferenceSystemConnectionObject(system=geo_reference_system, coordinates=["y", "x"])

    temporal_reference_system = ReferenceSystem(type="TemporalRS", calendar="Gregorian")
    temporal_referencing = ReferenceSystemConnectionObject(system=temporal_reference_system, coordinates=["t"])

    return [geo_referencing, temporal_referencing]


def get_parameters() -> dict[str, Parameter]:
    variables = get_variables()

    parameters = {}
    for var in variables:
        parameters[var.id] = Parameter(
            id=var.id,
            label={"en": var.id},
            description={"en": var.long_name},
            observedProperty=ObservedProperty(
                id=f"https://vocab.nerc.ac.uk/standard_name/{var.standard_name}",
                label={"en": var.standard_name},
            ),
            unit=Unit(label={"end": var.units}),
        )

    return parameters


@router.get(
    "/locations",
    tags=["Collection data queries"],
    response_model=EDRFeatureCollection,
    response_model_exclude_none=True,
    response_class=GeoJsonResponse,
)
async def get_locations(
    bbox: Annotated[str | None, Query(example="5.0,52.0,6.0,52.1")] = None,
    datetime: Annotated[str | None, Query(example="2022-12-31T00:00Z/2023-01-01T00:00Z")] = None,
    parameter_name: Annotated[
        str | None,
        Query(alias="parameter-name", description="Comma seperated list of parameter names.", example="ff, dd"),
    ] = None,
) -> EDRFeatureCollection:
    pass


@router.get(
    "/locations/{location_id}",
    tags=["Collection data queries"],
    response_model=Coverage,
    response_model_exclude_none=True,
    response_class=CoverageJsonResponse,
)
async def get_data_location_id(
    location_id: Annotated[str, Path(example="06260")],
    parameter_name: Annotated[
        str | None,
        Query(alias="parameter-name", description="Comma seperated list of parameter names.", example="ff, dd"),
    ] = None,
    datetime: Annotated[str | None, Query(example="2023-01-01T00:00Z/2023-01-02T00:00Z")] = None,
) -> Coverage:
    # Location query parameter
    station = get_station(location_id)
    if not station:
        raise HTTPException(status_code=404, detail="Location not found")

    # Parameter_name query parameter
    requested_parameters = split_string_parameters_to_list(parameter_name) if parameter_name else None
    available_parameters = get_parameters()

    if not requested_parameters:
        parameters = available_parameters
    elif not set(requested_parameters).issubset(set(available_parameters.keys())):
        unavailable_parameters = set(requested_parameters) - set(available_parameters.keys())
        raise HTTPException(
            status_code=400, detail=f"The following parameters are not available: {unavailable_parameters}"
        )
    else:
        parameters: dict[str, Parameter] = {p: available_parameters[p] for p in requested_parameters}

    # Datetime query parameter
    # TODO: Single datetime input doesn't work for me. Open ranges (datetime/.. and ../datetime) don't work.
    start_datetime, end_datetime = split_raw_interval_into_start_end_datetime(datetime)

    if end_datetime < start_datetime:
        raise HTTPException(status_code=422, detail="The start datetime must be before end datetime")

    # Get data
    ranges = {}
    t_values = []
    for p in parameters:
        data = get_data(location_id, p)

        t_values = []  # TODO: This code scares me.
        values = []
        for time, value in data:
            if start_datetime <= time < end_datetime:  # TOD: I think standard requires both sides to be closed.
                t_values.append(time)
                values.append(value)

        # TODO: Making assumption here len(t_values) is the same for all parameters
        ranges[p] = NdArray(
            axisNames=["t", "y", "x"],
            shape=[len(t_values), 1, 1],
            values=values,  # TODO: Code doesn't work with NaN (run with empty parameter_names to test)
        )

    if len(t_values) == 0:
        # TODO: Exact response needs further discussion
        raise HTTPException(status_code=400, detail="No data available")

    domain = Domain(
        domainType=DomainType.point_series,
        axes=Axes(
            x=ValuesAxis[float](values=[station.longitude]),
            y=ValuesAxis[float](values=[station.latitude]),
            t=ValuesAxis[AwareDatetime](values=t_values),
        ),
        referencing=get_reference_system(),
    )

    return Coverage(domain=domain, parameters=parameters, ranges=ranges)
