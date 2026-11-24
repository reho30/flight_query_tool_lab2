
"""Flight Schedule Parser and Query Tool - command-line entry point."""

import argparse
import json
import logging
import os
import sys
from datetime import datetime

from csv_loader import parse_files
from query import run_queries
from validator import load_airports


STUDENT_ID = "251ADB236"
FIRST_NAME = "Rahman"
LAST_NAME = "Gasimov"


def create_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""

    parser = argparse.ArgumentParser(
        description="Flight Schedule Parser and Query Tool"
    )

    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("-i", "--input", help="Input CSV file")
    source.add_argument("-d", "--directory", help="Directory containing CSV files")
    source.add_argument("-j", "--json", help="Existing JSON database")

    parser.add_argument("-a", "--airports", help="Airport codes file")
    parser.add_argument(
        "-o",
        "--output",
        default="db.json",
        help="Output database JSON file (default: db.json)",
    )
    parser.add_argument("-q", "--query", help="Query JSON file")
    parser.add_argument(
        "-r",
        "--response",
        default=".",
        help="Response output directory (default: current directory)",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the program and return an exit code."""

    parser = create_parser()

    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return exc.code

    if args.input and not args.airports:
        print("Error: -a is required when using -i", file=sys.stderr)
        return 2

    if args.directory and not args.airports:
        print("Error: -a is required when using -d", file=sys.stderr)
        return 2

    if args.json and args.output != "db.json":
        print("Error: -o cannot be used with -j", file=sys.stderr)
        return 2

    records = []
    logger = logging.getLogger("flight_parser")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    handler = None

    try:
        if args.input or args.directory:
            try:
                airports = load_airports(args.airports)
            except (OSError, UnicodeError) as exc:
                print(f"Error: Could not read airport file: {exc}", file=sys.stderr)
                return 1

            if args.input:
                paths = [args.input]
            else:
                try:
                    if not os.path.isdir(args.directory):
                        print(
                            f"Error: Directory does not exist: {args.directory}",
                            file=sys.stderr,
                        )
                        return 1

                    paths = sorted(
                        os.path.join(args.directory, filename)
                        for filename in os.listdir(args.directory)
                        if filename.lower().endswith(".csv")
                        and os.path.isfile(
                            os.path.join(args.directory, filename)
                        )
                    )

                except OSError as exc:
                    print(f"Error: Could not read directory: {exc}", file=sys.stderr)
                    return 1

                if not paths:
                    print(
                        "Error: No CSV files found in directory",
                        file=sys.stderr,
                    )
                    return 1

            log_path = os.path.join(
                os.path.dirname(os.path.abspath(args.output)),
                "errors.log",
            )

            handler = logging.FileHandler(
                log_path,
                mode="w",
                encoding="utf-8",
            )

            formatter = logging.Formatter(
                "%(asctime)s WARNING %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )

            handler.setFormatter(formatter)
            logger.addHandler(handler)

            records, errors = parse_files(paths, airports)

            for error in errors:
                logger.warning(error)

            file_errors = [
                error for error in errors
                if ":0: FILE_ERROR" in error
            ]

            if file_errors:
                for error in file_errors:
                    print(f"Error: {error}", file=sys.stderr)
                return 1

            try:
                with open(args.output, "w", encoding="utf-8") as file:
                    json.dump(records, file, indent=4)

            except (OSError, TypeError, ValueError) as exc:
                print(
                    f"Error: Could not write database file: {exc}",
                    file=sys.stderr,
                )
                return 1

        elif args.json:
            try:
                with open(args.json, "r", encoding="utf-8") as file:
                    records = json.load(file)

            except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                print(
                    f"Error: Could not read JSON database: {exc}",
                    file=sys.stderr,
                )
                return 1

            if not isinstance(records, list):
                print(
                    "Error: JSON database must contain an array",
                    file=sys.stderr,
                )
                return 1

            if not all(isinstance(record, dict) for record in records):
                print(
                    "Error: JSON database must contain objects",
                    file=sys.stderr,
                )
                return 1

        if args.query:
            try:
                with open(args.query, "r", encoding="utf-8") as file:
                    queries = json.load(file)

            except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                print(f"Error: Could not read query file: {exc}", file=sys.stderr)
                return 1

            if not isinstance(queries, (dict, list)):
                print(
                    "Error: Query file must contain an object or an array",
                    file=sys.stderr,
                )
                return 1

            responses = run_queries(records, queries)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M")

            response_filename = (
                f"response_{STUDENT_ID}_{FIRST_NAME}_{LAST_NAME}_"
                f"{timestamp}.json"
            )

            response_path = os.path.join(
                args.response,
                response_filename,
            )

            try:
                with open(response_path, "w", encoding="utf-8") as file:
                    json.dump(responses, file, indent=4)

            except (OSError, TypeError, ValueError) as exc:
                print(
                    f"Error: Could not write response file: {exc}",
                    file=sys.stderr,
                )
                return 1

        return 0

    finally:
        if handler is not None:
            logger.removeHandler(handler)
            handler.close()


if __name__ == "__main__":
    sys.exit(main())
