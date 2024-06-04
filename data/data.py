import os
from dataclasses import dataclass
from datetime import datetime
from datetime import timezone
from functools import cache

import pandas as pd
import xarray as xr

# Load the data
dirname = os.path.dirname(__file__)
filename = os.path.join(dirname, "20230101.nc")
ds = xr.open_dataset(filename, engine="netcdf4", chunks=None)


@dataclass
class Station:
    id: str
    name: str
    latitude: float
    longitude: float
    height: float


@dataclass
class Variable:
    id: str
    long_name: str
    standard_name: str | None
    units: str
    comment: str | None


@cache
def get_stations():
    stations = []
    for station_id, station_name, latitude, longitude, height in zip(
        ds["station"].values,
        ds["stationname"].values[0],
        ds["lat"].values[0],
        ds["lon"].values[0],
        ds["height"].values[0],
    ):
        station = Station(station_id, station_name, latitude, longitude, height)
        stations.append(station)
    return stations


def get_station(id: str):
    return list(filter(lambda x: x.id == id, get_stations()))[0]


@cache
def get_variables():
    variables = []
    for p in ds.data_vars:
        data_var = ds[p]
        if data_var.name in ["stationname", "lat", "lon", "height", "iso_dataset", "product", "projection"]:
            continue
        if "standard_name" not in data_var.attrs:
            # Don't handle these for now
            continue
        variable = Variable(
            id=data_var.name,
            long_name=data_var.long_name,
            standard_name=data_var.standard_name,
            units=data_var.units,
            comment=data_var.comment if "comment" in data_var.attrs else None,
        )
        variables.append(variable)
    return variables


def get_variable(id: str):
    return list(filter(lambda x: x.id == id, get_variables()))[0]


def get_data(station: str, variable: str) -> list[tuple[datetime, float | None]]:
    var = ds.sel(station=station)[variable].fillna(None)
    data = []
    for time, obs_value in zip(
        pd.to_datetime(var["time"].data).to_pydatetime(),
        var.data,
    ):
        data.append((time.replace(tzinfo=timezone.utc), obs_value))
    return data


@cache
def get_temporal_extent():
    times = pd.to_datetime(ds.time.data).to_pydatetime()
    return min(times).replace(tzinfo=timezone.utc), max(times).replace(tzinfo=timezone.utc)


if __name__ == "__main__":
    print(get_stations())
    print(get_variables())

    print(get_station("06260"))
    print(get_variable("ff"))
    print(get_data("06260", "ff"))

    print(get_temporal_extent())
