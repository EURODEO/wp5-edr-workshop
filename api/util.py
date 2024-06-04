from datetime import datetime


def create_url_from_request(request):
    # The server root_path contains the path added by a reverse proxy
    base_path = request.scope.get("root_path")

    # The host will (should) be correctly set from X-Forwarded-Host and X-Forwarded-Scheme
    # headers by any proxy in front of it
    host = request.headers["host"]
    scheme = request.url.scheme

    return f"{scheme}://{host}{base_path}/collections"


def split_string_parameters_to_list(value: str | list[str]):
    if not value:
        return None
    elif isinstance(value, str):
        return list(map(str.strip, value.split(",")))
    else:
        return value


def datetime_to_iso_string(value: datetime) -> str:
    """Returns the datetime as ISO 8601 string.
    Changes timezone +00:00 to the military time zone indicator (Z).

    Keyword arguments:
    value -- A datetime

    Returns:
    datetime string -- Returns the datetime as an ISO 8601 string with the military indicator.
    """
    if value.tzinfo is None:
        # This sort of replicates the functionality of Pydantic's AwareDatetime type
        raise ValueError("Datetime object is not timezone aware")

    iso_8601_str = value.isoformat()
    tz_offset_utc = "+00:00"
    if iso_8601_str.endswith(tz_offset_utc):
        return f"{iso_8601_str[:-len(tz_offset_utc)]}Z"
    else:
        return iso_8601_str
