"""Reading CSV files into flight records and error messages."""

import csv
import os

from validator import validate_row, to_record


def parse_files(paths: list[str], airports: set[str]) -> tuple[list[dict], list[str]]:
    """Process the CSV files in the order given.

    Return (records, errors):
        records - valid flight records, in input order
        errors  - one message per invalid row, in input order, formatted as
                  "<file name>:<line number>: <ERROR_CODE> | <free text>"
                  (base file name only, no timestamp or level, no newline)

    Also performs the DUPLICATE_FLIGHT check across all the files.
    Does not write any files and does not log anything itself.
    """

    records = []
    errors = []

    seen_flights = set()

    for path in paths:
        filename = os.path.basename(path)

        try:
            with open(path, "r", encoding="utf-8", newline="") as file:
                reader = csv.reader(file)

                # Skip the header
                next(reader, None)

                for line_number, fields in enumerate(reader, start=2):
                    # Skip blank rows
                    if not fields or all(field.strip() == "" for field in fields):
                        continue

                    # Skip comment rows
                    if fields[0].strip().startswith("#"):
                        continue

                    fields = [field.strip() for field in fields]

                    error_code = validate_row(fields, airports)

                    if error_code is not None:
                        errors.append(
                            f"{filename}:{line_number}: {error_code} | Invalid flight data"
                        )
                        continue

                    record = to_record(fields)

                    duplicate_key = (
                        record["flight_id"],
                        record["departure_datetime"],
                    )

                    if duplicate_key in seen_flights:
                        errors.append(
                            f"{filename}:{line_number}: DUPLICATE_FLIGHT | "
                            "Duplicate flight ID and departure datetime"
                        )
                        continue

                    seen_flights.add(duplicate_key)
                    records.append(record)

        except (OSError, UnicodeError, csv.Error):
            errors.append(f"{filename}:0: FILE_ERROR | Could not read file")

    return records, errors
