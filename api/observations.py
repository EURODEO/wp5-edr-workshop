from http.client import HTTPException
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
from edr_pydantic.parameter import EdrBaseModel
from fastapi import APIRouter
from fastapi import Path
from fastapi import Query
from geojson_pydantic import FeatureCollection
from pydantic import AwareDatetime
from starlette.responses import JSONResponse

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
    """
    Define static reference systems and return list.
    :param
    :return: Reference systems
    """
    geo_reference_system = ReferenceSystem(type="GeographicCRS", id="http://www.opengis.net/def/crs/EPSG/0/4326")
    geo_referencing = ReferenceSystemConnectionObject(system=geo_reference_system, coordinates=["y", "x"])

    temporal_reference_system = ReferenceSystem(type="TemporalRS", calendar="Gregorian")
    temporal_referencing = ReferenceSystemConnectionObject(system=temporal_reference_system, coordinates=["t"])

    return [geo_referencing, temporal_referencing]


def get_parameters() -> dict[str, Parameter]:
    variables = get_variables()

    parameters = {}
    for var in variables:
        parameters[var.id] = Parameter(id=var.id, observedProperty=ObservedProperty(label={"en": var.long_name}))

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
    station = get_station(location_id)

    if not station:
        raise HTTPException(status_code=404, detail="Location not found")

    data = get_data(location_id, parameter_name)
    t_values = [t[0] for t in data]
    r_values = [t[1] for t in data]

    domain = Domain(
        domainType=DomainType.point_series,
        axes=Axes(
            x=ValuesAxis[float](values=[station.longitude]),
            y=ValuesAxis[float](values=[station.latitude]),
            t=ValuesAxis[AwareDatetime](values=t_values),
        ),
        referencing=get_reference_system(),
    )
    parameters = get_parameters()

    ranges = {
        parameter_name: NdArray(
            axisNames=["t", "y", "x"],
            shape=[len(data), 1, 1],
            values=r_values,
        )
    }

    return Coverage(domain=domain, parameters=parameters, ranges=ranges)
