import logging
from typing import Annotated

from covjson_pydantic.coverage import Coverage
from covjson_pydantic.coverage import CoverageCollection
from covjson_pydantic.domain import Axes
from covjson_pydantic.domain import Domain
from covjson_pydantic.domain import DomainType
from covjson_pydantic.domain import ValuesAxis
from covjson_pydantic.ndarray import NdArray
from covjson_pydantic.parameter import Parameter
from edr_pydantic.parameter import EdrBaseModel
from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import Path
from fastapi import Query
from geojson_pydantic import Feature
from geojson_pydantic import FeatureCollection
from geojson_pydantic import Point
from pydantic import AwareDatetime
from shapely import geometry
from shapely import wkt
from starlette.responses import JSONResponse

from api.util import get_covjson_parameter_from_variable
from api.util import get_reference_system
from api.util import split_raw_interval_into_start_end_datetime
from api.util import split_string_parameters_to_list
from data import data
from data.data import get_data
from data.data import get_station
from data.data import get_stations
from data.data import get_variables
from data.data import get_variables_for_station

router = APIRouter(prefix="/collections/observations")

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class CoverageJsonResponse(JSONResponse):
    media_type = "application/prs.coverage+json"


class GeoJsonResponse(JSONResponse):
    media_type = "application/geo+json"


class EDRFeatureCollection(EdrBaseModel, FeatureCollection):
    parameters: dict[str, Parameter]


def check_requested_parameters_exist(requested_parameters, all_parameters):
    if not set(requested_parameters).issubset(set(all_parameters)):
        unavailable_parameters = set(requested_parameters) - set(all_parameters)
        raise HTTPException(
            status_code=400, detail=f"The following parameters are not available: {unavailable_parameters}"
        )


@router.get(
    "/locations",
    tags=["Collection data queries"],
    response_model=EDRFeatureCollection,
    response_model_exclude_none=True,
    response_class=GeoJsonResponse,
)
async def get_locations(
    bbox: Annotated[str | None, Query(example="5.0,52.0,6.0,52.1")] = None,
    # datetime: Annotated[str | None, Query(example="2024-02-22T01:00:00Z/2024-02-22T02:00:00Z")] = None,
    parameter_name: Annotated[
        str | None,
        Query(
            alias="parameter-name",
            description="Comma seperated list of parameter names. "
            "Return only locations that have one of these parameter.",
            example="ff, dd",
        ),
    ] = None,
) -> EDRFeatureCollection:
    stations = data.get_stations()

    # Handle bounding box
    if bbox:
        bbox_values = list(map(lambda x: float(str.strip(x)), bbox.split(",")))
        if len(bbox_values) != 4:
            raise HTTPException(status_code=400, detail="If provided, the bbox should have 4 values")
        left, bottom, right, top = bbox_values
        stations = list(filter(lambda s: left <= s.longitude <= right and bottom <= s.latitude <= top, stations))

    # Handle parameters
    all_parameters: dict[str, Parameter] = {var.id: get_covjson_parameter_from_variable(var) for var in get_variables()}
    requested_parameters = None
    if parameter_name:
        requested_parameters = set(map(lambda x: str.strip(x), parameter_name.split(",")))
        check_requested_parameters_exist(requested_parameters, all_parameters.keys())

    # Build list of GeoJSON features
    features = []
    parameter_ids_returned_stations = set()
    for station in stations:
        variables_for_station = get_variables_for_station(station.id)
        parameter_names_for_station = list(map(lambda x: x.id, variables_for_station))

        # Filter out stations that have none of the requested parameters
        if requested_parameters and not requested_parameters.intersection(parameter_names_for_station):
            continue

        features.append(
            Feature(
                type="Feature",
                id=station.id,
                properties={
                    "name": station.name,
                    "detail": f"https://oscar.wmo.int/surface/rest/api/search/station?wigosId={station.wsi}",
                    "parameter-name": sorted(parameter_names_for_station),
                },
                geometry=Point(
                    type="Point",
                    coordinates=(station.longitude, station.latitude),
                ),
            )
        )
        parameter_ids_returned_stations.update(parameter_names_for_station)

    parameters_returned_stations = {key: all_parameters[key] for key in sorted(parameter_ids_returned_stations)}
    return EDRFeatureCollection(type="FeatureCollection", features=features, parameters=parameters_returned_stations)


def get_coverage_for_station(station, parameters, start_datetime, end_datetime) -> Coverage:
    # See if we have any data in this time interval by testing the first parameter
    # TODO: Making assumption here the time interval is the same for all parameters
    data = get_data(station.id, list(parameters)[0])
    t_axis_values = [t for t, v in data if (start_datetime <= t <= end_datetime)]
    if len(t_axis_values) == 0:
        raise HTTPException(status_code=400, detail="No data available")

    # Get parameter data
    ranges = {}
    for p in parameters:
        values = []
        for time, value in get_data(station.id, p):
            if start_datetime <= time <= end_datetime:
                values.append(value)

        ranges[p] = NdArray(
            axisNames=["t", "y", "x"],
            shape=[len(values), 1, 1],
            values=values,
        )

    # Add station code
    station_code = {"inspiregloss:Identifier": station.wsi}

    domain = Domain(
        domainType=DomainType.point_series,
        axes=Axes(
            x=ValuesAxis[float](values=[station.longitude]),
            y=ValuesAxis[float](values=[station.latitude]),
            t=ValuesAxis[AwareDatetime](values=t_axis_values),
        ),
        referencing=get_reference_system(),
    )

    return Coverage(domain=domain, parameters=parameters, ranges=ranges, **station_code)


def handle_datetime(datetime):
    start_datetime, end_datetime = split_raw_interval_into_start_end_datetime(datetime)
    if end_datetime < start_datetime:
        raise HTTPException(status_code=400, detail="The start datetime must be before end datetime")
    return start_datetime, end_datetime


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
    datetime: Annotated[str | None, Query(example="2024-02-22T01:00:00Z/2024-02-22T02:00:00Z")] = None,
) -> Coverage:
    # Location query parameter
    station = get_station(location_id)
    if not station:
        raise HTTPException(status_code=404, detail="Location not found")

    start_datetime, end_datetime = handle_datetime(datetime)

    # Parameter_name query parameter
    parameters: dict[str, Parameter] = {
        var.id: get_covjson_parameter_from_variable(var) for var in get_variables_for_station(location_id)
    }

    if parameter_name:
        requested_parameters = split_string_parameters_to_list(parameter_name)
        check_requested_parameters_exist(requested_parameters, parameters.keys())

        parameters = {p: parameters[p] for p in requested_parameters}

    return get_coverage_for_station(station, parameters, start_datetime, end_datetime)


@router.get(
    "/area",
    tags=["Collection data queries"],
    response_model=CoverageCollection,
    response_model_exclude_none=True,
    response_class=CoverageJsonResponse,
)
async def get_data_area(
    coords: Annotated[str, Query(example="POLYGON((5.0 52.0, 6.0 52.0,6.0 52.1,5.0 52.1, 5.0 52.0))")],
    parameter_name: Annotated[
        str | None,
        Query(alias="parameter-name", description="Comma seperated list of parameter names.", example="ff, dd"),
    ] = None,
    datetime: Annotated[str | None, Query(example="2024-02-22T01:00:00Z/2024-02-22T02:00:00Z")] = None,
):
    # No error handling!
    poly = wkt.loads(coords)
    stations_in_polygon = [s for s in get_stations() if geometry.Point(s.longitude, s.latitude).within(poly)]
    if not stations_in_polygon:
        raise HTTPException(status_code=400, detail="No stations in polygon")

    start_datetime, end_datetime = handle_datetime(datetime)

    # Check that the parameters requested exist in the store
    # NOTE: How do we define that a parameter exist? In all stations? In a specific station?
    # In the stations in the polygon?
    if parameter_name:
        all_parameter_ids = [var.id for var in get_variables()]
        requested_parameters = split_string_parameters_to_list(parameter_name)
        check_requested_parameters_exist(requested_parameters, all_parameter_ids)

    coverages = []
    coverage_parameters: dict[str, Parameter] = {}
    for station in stations_in_polygon:
        # Make sure we only return data for parameters that exist for each station
        parameters: dict[str, Parameter] = {
            var.id: get_covjson_parameter_from_variable(var) for var in get_variables_for_station(station.id)
        }
        if parameter_name:
            parameters = {p: parameters[p] for p in set(requested_parameters).intersection(set(parameters.keys()))}

        if parameters:  # Anything left?
            coverages.append(get_coverage_for_station(station, parameters, start_datetime, end_datetime))
            coverage_parameters.update(parameters)

    if len(coverages) == 0:
        raise HTTPException(status_code=400, detail="No data available for this query")
    else:
        return CoverageCollection(coverages=coverages, parameters=coverage_parameters)
