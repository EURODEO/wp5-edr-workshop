from functools import cache

from edr_pydantic.collections import Collection
from edr_pydantic.data_queries import DataQueries
from edr_pydantic.data_queries import EDRQuery
from edr_pydantic.extent import Extent
from edr_pydantic.extent import Spatial
from edr_pydantic.extent import Temporal
from edr_pydantic.link import EDRQueryLink
from edr_pydantic.link import Link
from edr_pydantic.observed_property import ObservedProperty
from edr_pydantic.parameter import Parameter
from edr_pydantic.unit import Unit
from edr_pydantic.variables import Variables

from api.util import datetime_to_iso_string
from data.data import get_data
from data.data import get_stations
from data.data import get_variables


@cache
def get_spatial_extent() -> tuple[float, float, float, float]:
    stations = get_stations()
    longs = list(map(lambda x: x.longitude, stations))
    lats = list(map(lambda x: x.latitude, stations))
    left = min(longs)
    right = max(longs)
    bottom = min(lats)
    top = max(lats)

    return left, bottom, right, top


# TODO: Very inefficient.
# TODO: This should not be cached in a real API
@cache
def get_temporal_extent():
    start_dates = []
    end_dates = []
    for station in get_stations():
        for variable in get_variables():
            data = get_data(station.id, variable.id)
            start_dates.append(data[0][0])
            end_dates.append(data[-1][0])
    start = min(start_dates)
    end = max(end_dates)

    return start, end


async def get_collection_metadata(base_url: str, is_self) -> Collection:
    start, end = get_temporal_extent()
    left, bottom, right, top = get_spatial_extent()

    parameters: dict[str, Parameter] = {}
    for var in get_variables():
        p = Parameter(
            id=var.id,
            # label=var.id,
            description=var.long_name,
            observedProperty=ObservedProperty(
                id=f"https://vocab.nerc.ac.uk/standard_name/{var.standard_name}",
                label=var.standard_name,
            ),
            unit=Unit(label=var.units),
        )
        parameters[var.id] = p

    collection = Collection(
        id="observations",
        links=[
            Link(href=f"{base_url}/observations", rel="self" if is_self else "data"),
        ],
        extent=Extent(
            spatial=Spatial(
                bbox=[[left, bottom, right, top]],
                crs="EPSG:4326",
            ),
            temporal=Temporal(
                interval=[[start, end]],
                values=[f"{datetime_to_iso_string(start)}/{datetime_to_iso_string(end)}"],
                trs="datetime",
            ),
        ),
        data_queries=DataQueries(
            locations=EDRQuery(
                link=EDRQueryLink(
                    href=f"{base_url}/observations/locations",
                    rel="data",
                    variables=Variables(query_type="locations", output_format=["CoverageJSON"]),
                )
            ),
            area=EDRQuery(
                link=EDRQueryLink(
                    href=f"{base_url}/observations/area",
                    rel="data",
                    variables=Variables(query_type="area", output_format=["CoverageJSON"]),
                )
            ),
        ),
        crs=["WGS84"],
        output_formats=["CoverageJSON"],
        parameter_names=parameters,
    )
    return collection
