from typing import Annotated

from covjson_pydantic.coverage import Coverage
from fastapi import APIRouter
from fastapi import Path
from fastapi import Query
from starlette.responses import JSONResponse


router = APIRouter(prefix="/collections/observations")


class CoverageJsonResponse(JSONResponse):
    media_type = "application/prs.coverage+json"


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
    pass
