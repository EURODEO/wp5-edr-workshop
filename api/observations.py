import logging
from typing import Annotated

from covjson_pydantic.coverage import Coverage
from covjson_pydantic.coverage import CoverageCollection
from covjson_pydantic.parameter import Parameter
from edr_pydantic.parameter import EdrBaseModel
from fastapi import APIRouter
from fastapi import Path
from fastapi import Query
from geojson_pydantic import FeatureCollection
from starlette.responses import JSONResponse


router = APIRouter(prefix="/collections/observations")

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class CoverageJsonResponse(JSONResponse):
    media_type = "application/prs.coverage+json"


class GeoJsonResponse(JSONResponse):
    media_type = "application/geo+json"


class EDRFeatureCollection(EdrBaseModel, FeatureCollection):
    parameters: dict[str, Parameter]


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
    datetime: Annotated[str | None, Query(example="2024-02-22T01:00:00Z/2024-02-22T02:00:00Z")] = None,
) -> Coverage:
    pass


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
    pass
