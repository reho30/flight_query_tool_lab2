"""Running queries against the flight database."""

from datetime import datetime
from math import isfinite


VALID_KEYS = {
    "flight_id",
    "origin",
    "destination",
    "departure_datetime",
    "arrival_datetime",
    "price",
    "min_price",
    "sort_by",
    "order",
    "limit",
}

SORT_KEYS = {
    "flight_id",
    "origin",
    "destination",
    "departure_datetime",
    "arrival_datetime",
    "price",
}


def valid_datetime(value: str) -> bool:
    """Check whether a datetime string has the required format."""
    if not isinstance(value, str):
        return False

    try:
        datetime.strptime(value, "%Y-%m-%d %H:%M")
    except ValueError:
        return False

    return True


def valid_query(query: dict) -> bool:
    """Check whether a query object is valid."""
    if not isinstance(query, dict):
        return False

    if any(key not in VALID_KEYS for key in query):
        return False

    for key in ("flight_id", "origin", "destination"):
        if key in query and not isinstance(query[key], str):
            return False

    for key in ("departure_datetime", "arrival_datetime"):
        if key in query and not valid_datetime(query[key]):
            return False

    for key in ("price", "min_price"):
        if key in query:
            value = query[key]

            if isinstance(value, bool) or not isinstance(value, (int, float)):
                return False

            if not isfinite(value):
                return False

    if "sort_by" in query:
        if query["sort_by"] not in SORT_KEYS:
            return False

    if "order" in query:
        if "sort_by" not in query:
            return False

        if query["order"] not in ("asc", "desc"):
            return False

    if "limit" in query:
        limit = query["limit"]

        if isinstance(limit, bool) or not isinstance(limit, int):
            return False

        if limit < 0:
            return False

    return True


def run_query(db: list[dict], query: dict) -> dict:
    """Return one response entry for one query object."""

    if not valid_query(query):
        return {
            "query": query,
            "error": "INVALID_QUERY",
            "matches": [],
        }

    matches = []

    for flight in db:
        matched = True

        if "flight_id" in query:
            if flight["flight_id"] != query["flight_id"]:
                matched = False

        if "origin" in query:
            if flight["origin"] != query["origin"]:
                matched = False

        if "destination" in query:
            if flight["destination"] != query["destination"]:
                matched = False

        if "departure_datetime" in query:
            if flight["departure_datetime"] < query["departure_datetime"]:
                matched = False

        if "arrival_datetime" in query:
            if flight["arrival_datetime"] > query["arrival_datetime"]:
                matched = False

        if "price" in query:
            if flight["price"] > query["price"]:
                matched = False

        if "min_price" in query:
            if flight["price"] < query["min_price"]:
                matched = False


        if matched:
            matches.append(flight)

    if "sort_by" in query:
        sort_key = query["sort_by"]
        reverse = query.get("order", "asc") == "desc"

        matches.sort(key=lambda flight: flight[sort_key], reverse=reverse)

    if "limit" in query:
        matches = matches[:query["limit"]]

    return {
        "query": query,
        "matches": matches,
    }


def run_queries(db: list[dict], queries: dict | list) -> list[dict]:
    """Accept one query object or a list of them; always return a list."""

    if isinstance(queries, list):
        return [run_query(db, query) for query in queries]

    return [run_query(db, queries)]
