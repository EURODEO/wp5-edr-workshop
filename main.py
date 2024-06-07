# For developing:    uvicorn main:app --reload
import logging

import uvicorn
from brotli_asgi import BrotliMiddleware
from edr_pydantic.capabilities import ConformanceModel
from edr_pydantic.capabilities import Contact
from edr_pydantic.capabilities import LandingPageModel
from edr_pydantic.capabilities import Provider
from edr_pydantic.collections import Collection
from edr_pydantic.collections import Collections
from edr_pydantic.link import Link
from fastapi import FastAPI
from fastapi import Request

from api import observations


def setup_logging():
    logger = logging.getLogger()
    syslog = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s ; edr-api ; %(process)s ; %(levelname)s ; %(name)s ; %(message)s")

    syslog.setFormatter(formatter)
    logger.addHandler(syslog)


setup_logging()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


app = FastAPI(
    title="RODEO WP5 EDR workshop", swagger_ui_parameters={"defaultModelsExpandDepth": -1, "tryItOutEnabled": True}
)
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
            Link(href=f"{request.url}conformance", rel="data", title="Conformance Declaration in JSON"),
            Link(href=f"{request.url}collections", rel="data", title="Collections metadata in JSON"),
        ],
    )


@app.get(
    "/conformance",
    tags=["Capabilities"],
    response_model=ConformanceModel,
    response_model_exclude_none=True,
)
async def get_conformance(request: Request) -> ConformanceModel:
    return ConformanceModel(
        conformsTo=[
            "http://www.opengis.net/spec/ogcapi-edr-1/1.1/conf/core",
            "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/core",
            "http://www.opengis.net/spec/ogcapi-common-2/1.0/conf/collections",
            "http://www.opengis.net/spec/ogcapi-edr-1/1.1/conf/oas30",
            # "http://www.opengis.net/spec/ogcapi-edr-1/1.1/conf/html",
            "http://www.opengis.net/spec/ogcapi-edr-1/1.1/conf/edr-geojson",
            "http://www.opengis.net/spec/ogcapi-edr-1/1.1/conf/covjson",
        ]
    )


@app.get(
    "/collections",
    tags=["Capabilities"],
    response_model=Collections,
    response_model_exclude_none=True,
)
async def get_collections(request: Request) -> Collections:
    pass


@app.get(
    "/collections/observations",
    tags=["Collection metadata"],
    response_model=Collection,
    response_model_exclude_none=True,
)
async def get_collection_metadata(request: Request) -> Collection:
    pass


# Include other routes
app.include_router(observations.router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
