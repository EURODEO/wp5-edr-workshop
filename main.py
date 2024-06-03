# For developing:    uvicorn main:app --reload
import logging

from brotli_asgi import BrotliMiddleware
from edr_pydantic.capabilities import Contact
from edr_pydantic.capabilities import LandingPageModel
from edr_pydantic.capabilities import Provider
from edr_pydantic.collections import Collection
from edr_pydantic.collections import Collections
from edr_pydantic.link import Link
from fastapi import FastAPI
from fastapi import Request

from api import collection
from api import observations
from api.util import create_url_from_request


def setup_logging():
    logger = logging.getLogger()
    syslog = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s ; e-soh-api ; %(process)s ; %(levelname)s ; %(name)s ; %(message)s")

    syslog.setFormatter(formatter)
    logger.addHandler(syslog)


setup_logging()
logger = logging.getLogger(__name__)


app = FastAPI(swagger_ui_parameters={"defaultModelsExpandDepth": -1, "tryItOutEnabled": True})
app.add_middleware(BrotliMiddleware)


@app.get(
    "/",
    tags=["Capabilities"],
    response_model=LandingPageModel,
    response_model_exclude_none=True,
)
async def landing_page(request: Request) -> LandingPageModel:
    return LandingPageModel(
        title="EDR tutorial",
        description="A simple example EDR implementation",
        keywords=["weather", "temperature", "wind", "humidity", "pressure", "clouds", "radiation"],
        provider=Provider(name="RODEO", url="https://rodeo-project.eu/"),
        contact=Contact(email="rodeoproject@fmi.fi"),
        links=[
            Link(href=f"{request.url}", rel="self", title="Landing Page in JSON"),
            Link(href=f"{request.url}docs", rel="service-desc", title="API description in HTML"),
            Link(href=f"{request.url}openapi.json", rel="service-desc", title="API description in JSON"),
            # Link(href=f"{request.url}conformance", rel="data", title="Conformance Declaration in JSON"),
            Link(href=f"{request.url}collections", rel="data", title="Collections metadata in JSON"),
        ],
    )


@app.get(
    "/collections",
    tags=["Capabilities"],
    response_model=Collections,
    response_model_exclude_none=True,
)
async def get_collections(request: Request) -> Collections:
    base_url = create_url_from_request(request)
    return Collections(
        links=[
            Link(href=f"{base_url}", rel="self"),
        ],
        collections=[await collection.get_collection_metadata(base_url, is_self=False)],
    )


@app.get(
    "/collections/observations",
    tags=["Collection metadata"],
    response_model=Collection,
    response_model_exclude_none=True,
)
async def get_collection_metadata(request: Request) -> Collection:
    base_url = create_url_from_request(request)
    return await collection.get_collection_metadata(base_url, is_self=True)


# Include other routes
app.include_router(observations.router)
