import re
from datetime import datetime
from math import isfinite


def load_airports(path: str) -> set[str]:
    airports = set()

    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            code = line.strip()

            if code and not code.startswith("#"):
                airports.add(code)

    return airports


def validate_row(fields: list[str], airports: set[str]) -> str | None:
    fields = [field.strip() for field in fields]

    if len(fields) != 6:
        return "WRONG_FIELD_COUNT"

    if any(field == "" for field in fields):
        return "MISSING_FIELD"

    flight_id = fields[0]

    if not re.fullmatch(r"[A-Za-z0-9]{2,8}", flight_id):
        return "INVALID_FLIGHT_ID"

    origin = fields[1]

    if not re.fullmatch(r"[A-Z]{3}", origin) or origin not in airports:
        return "INVALID_ORIGIN"

    destination = fields[2]

    if not re.fullmatch(r"[A-Z]{3}", destination) or destination not in airports:
        return "INVALID_DESTINATION"

    if origin == destination:
        return "SAME_ORIGIN_DESTINATION"

    departure = fields[3]

    if not re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}", departure):
        return "INVALID_DEPARTURE"

    try:
        departure_time = datetime.strptime(departure, "%Y-%m-%d %H:%M")
    except ValueError:
        return "INVALID_DEPARTURE"

    arrival = fields[4]

    if not re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}", arrival):
        return "INVALID_ARRIVAL"

    try:
        arrival_time = datetime.strptime(arrival, "%Y-%m-%d %H:%M")
    except ValueError:
        return "INVALID_ARRIVAL"

    if arrival_time <= departure_time:
        return "ARRIVAL_NOT_AFTER_DEPARTURE"

    price = fields[5]

    try:
        price_value = float(price)
    except ValueError:
        return "INVALID_PRICE"

    if not isfinite(price_value):
        return "INVALID_PRICE"

    if price_value <= 0:
        return "NON_POSITIVE_PRICE"

    return None


def to_record(fields: list[str]) -> dict:
    fields = [field.strip() for field in fields]

    return {
        "flight_id": fields[0],
        "origin": fields[1],
        "destination": fields[2],
        "departure_datetime": fields[3],
        "arrival_datetime": fields[4],
        "price": float(fields[5]),
    }