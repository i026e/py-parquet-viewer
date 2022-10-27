import argparse
from typing import Tuple, Any, List

from parquet_viewer.qt.qt_window import run_app


def parse_args() -> Tuple[Any, List]:

    parser = argparse.ArgumentParser()
    parser.add_argument('parquet_file', action='store', nargs='?', default=None, type=str)  # positional argument

    parsed_args, unparsed_args = parser.parse_known_args()
    return parsed_args, unparsed_args


def main():
    parsed_args, unparsed_args = parse_args()
    run_app(unparsed_args, parsed_args.parquet_file)


if __name__ == "__main__":
    main()
