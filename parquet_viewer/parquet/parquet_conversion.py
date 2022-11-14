import os.path
from dataclasses import dataclass
from multiprocessing import Process, Pipe
import datetime
import enum
import json
import csv

import pyarrow as pa

from typing import Any, Callable, Optional, Generator, Dict, Union

from parquet_viewer._logger import LOGGER

ProgressCallback = Callable[[int, int], bool]


class ConversionStatus(str, enum.Enum):
    PENDING = "Pending"
    RUNNING = "Running"
    DONE = "Done"
    ABORTED = "Aborted"
    FAILED = "Failed"


@dataclass
class ProgressData:
    batch: int
    num_batches: int
    status: ConversionStatus
    context: Any = None


class OutputFormat(str, enum.Enum):
    JSON = "json"
    CSV = "csv"


class CsvDialect(str, enum.Enum):
    EXCEL = "excel"
    EXCEL_TAB = "excel-tab"


class ExtendedJSONEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> str:
        if isinstance(obj, (datetime.datetime, datetime.date, datetime.time)):
            return obj.isoformat()
        return str(obj)


class CSVEncoder:
    def __init__(self):
        self.json_encoder = ExtendedJSONEncoder(indent=None)

    def encode_value(self, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, bool):
            return self.json_encoder.encode(value)
        if isinstance(value, (int, float, str)):
            return value
        return self.json_encoder.encode(value)

    def encode(self, row: Dict[str, Any]) -> Dict[str, Any]:
        return {key: self.encode_value(value) for key, value in row.items()}


def convert_parquet_to_json(
        table: pa.Table,
        output_file: str,
        batch_size: int,
        progress_cb: ProgressCallback,
        **kwargs: Any
) -> bool:
    encoder = ExtendedJSONEncoder(indent=None, separators=(',', ':'))
    batches = table.to_batches(batch_size)
    num_batches = len(batches)
    output_file = os.path.abspath(output_file)

    abort = progress_cb(num_batches, 0)

    LOGGER.info("Writing %s batches to JSON file %s", num_batches, output_file)
    with open(output_file, "w", encoding="utf-8") as f:
        for i, batch in enumerate(batches):

            if abort:
                LOGGER.warning("Writing batch %s was aborted", i)
                return False

            LOGGER.info("Writing batch %s", i)

            for row in batch.to_pylist():
                line = encoder.encode(row)
                f.write(line)
                f.write("\n")

            LOGGER.info("Done writing batch %s", i)
            abort = progress_cb(num_batches, i + 1)

    return True


def convert_parquet_to_csv(
        table: pa.Table,
        output_file: str,
        batch_size: int,
        csv_dialect: CsvDialect,
        progress_cb: ProgressCallback,
        **kwargs: Any,
) -> bool:
    encoder = CSVEncoder()
    batches = table.to_batches(batch_size)
    num_batches = len(batches)
    fieldnames = table.column_names
    output_file = os.path.abspath(output_file)

    abort = progress_cb(num_batches, 0)

    LOGGER.info("Writing %s batches to CSV file %s", num_batches, output_file)

    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, dialect=str(csv_dialect.value))
        writer.writeheader()

        for i, batch in enumerate(batches):

            if abort:
                LOGGER.warning("Writing batch %s was aborted", i)
                return False

            LOGGER.info("Writing batch %s", i)

            for row in batch.to_pylist():
                writer.writerow(encoder.encode(row))
            LOGGER.info("Done writing batch %s", i)
            abort = progress_cb(num_batches, i + 1)

    return True


class ConversionProcess:
    CONV_FUNCTIONS = {
        OutputFormat.JSON: convert_parquet_to_json,
        OutputFormat.CSV: convert_parquet_to_csv
    }

    def __init__(self, output_format: OutputFormat, **kwargs: Any) -> None:
        self.parent_conn, self.child_conn = Pipe()

        self.conv_func = self.CONV_FUNCTIONS[output_format]
        self.kwargs = kwargs
        self.kwargs["progress_cb"] = self._child_progress_cb

        self.process = None

    def _child_process(self) -> None:
        try:
            self.child_conn.send(ProgressData(
                batch=0,
                num_batches=0,
                status=ConversionStatus.PENDING
            ))
            success = self.conv_func(**self.kwargs)
            self.child_conn.send(ProgressData(
                batch=0,
                num_batches=0,
                status=ConversionStatus.DONE if success else ConversionStatus.ABORTED
            ))

        except Exception as e:
            LOGGER.exception("Unexpected exception: %s", e)
            self.child_conn.send(ProgressData(
                batch=0,
                num_batches=0,
                status=ConversionStatus.FAILED,
                context=str(e)
            ))

    def _child_progress_cb(self, num_batches: int, batch: int) -> bool:
        self.child_conn.send(ProgressData(
            batch=batch,
            num_batches=num_batches,
            status=ConversionStatus.RUNNING
        ))

        abort = self.child_conn.poll(0.0) and bool(self.child_conn.recv())
        return abort

    def abort(self) -> None:
        self.parent_conn.send(True)

    def start(self) -> None:
        if self.process is None:
            self.parent_conn, self.child_conn = Pipe()
            self.process = Process(target=self._child_process, name="parquet-conversion")
        self.process.daemon = True
        self.process.start()

    def join(self) -> None:
        if self.process is not None:
            self.process.join()
            self.process = None

    def is_running(self) -> bool:
        return self.process is not None and self.process.is_alive()

    def get_progress(self, timeout: Optional[float] = 0.0) -> Generator[ProgressData, None, None]:
        while self.parent_conn.poll(timeout):
            yield self.parent_conn.recv()

    def __enter__(self) -> "ConversionProcess":
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.join()
