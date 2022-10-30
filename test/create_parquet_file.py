#!/usr/bin/env python3
import io
import os

from pyarrow import json
import pyarrow.parquet as pq


TEST_DATA = """
{"a": 1, "b": 2.0, "c": "foo", "d": false, "e": [1, 2], "f": {"g": true, "h": "1991-02-03"}}
{"a": 4, "b": -5.5, "c": null, "d": true, "e": [3, 4, 5]}
"""


def create_parquet_file(parquet_path: str, jsonl_data: str = TEST_DATA) -> str:
    table = json.read_json(io.BytesIO(jsonl_data.encode("utf-8")))
    print(table)
    pq.write_table(table, parquet_path)
    return os.path.abspath(parquet_path)


if __name__ == "__main__":
    create_parquet_file("file.parquet")
