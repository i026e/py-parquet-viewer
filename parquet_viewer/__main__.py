import argparse
import multiprocessing
from typing import Tuple, Any, List


def parse_args() -> Tuple[Any, List]:
    parser = argparse.ArgumentParser()
    parser.add_argument('parquet_file', action='store', nargs='?', default=None, type=str)  # positional argument

    parsed_args, unparsed_args = parser.parse_known_args()
    return parsed_args, unparsed_args


def main():
    from parquet_viewer.qt.qt_window import run_app
    parsed_args, unparsed_args = parse_args()
    run_app(unparsed_args, parsed_args.parquet_file)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
