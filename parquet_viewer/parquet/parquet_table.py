import os.path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from parquet_viewer.parquet.parquet_filters import PyArrowFilterBuilder, filter_parser


class ParquetTable:
    def __init__(self, parquet_file: str, batch_size: int):
        self.parquet_file = os.path.abspath(parquet_file)
        self._batch_size = batch_size

        self._table = None
        self._batches = None

        self._filter_builder = None
        self._filters = None
        self._filtered_table = None

    @property
    def lazy_table(self) -> pa.Table:
        if self._table is None:
            self._table = pq.read_table(self.parquet_file)
        return self._table

    @property
    def lazy_filtered_table(self) -> pa.Table:
        if self._filtered_table is None:
            if not self.filters:
                self._filtered_table = self.lazy_table
            else:
                self._filtered_table = self.lazy_table.filter(self.filters)
        return self._filtered_table

    @property
    def filter_builder(self) -> PyArrowFilterBuilder:
        if self._filter_builder is None:
            self._filter_builder = PyArrowFilterBuilder(table=self.lazy_table)
        return self._filter_builder

    @property
    def filters(self) -> Any:
        return self._filters

    @filters.setter
    def filters(self, filters: str) -> None:
        filters = filters.strip()
        if not filters:
            self._filters = None
        else:
            filters_tree = filter_parser.parse(filters)
            self._filters = self.filter_builder.transform(filters_tree)

        self.reset_batches()

    @property
    def lazy_batches(self) -> list:
        if self._batches is None:
            self._batches = self.lazy_filtered_table.to_batches(self._batch_size)
        return self._batches

    def reset_batches(self) -> None:
        self._filtered_table = None
        self._batches = None

    @property
    def batch_size(self) -> int:
        return self._batch_size

    @batch_size.setter
    def batch_size(self, batch_size: int) -> None:
        self._batch_size = batch_size
        self._batches = None

    @property
    def num_batches(self) -> int:
        return len(self.lazy_batches)

    @property
    def num_columns(self) -> int:
        return self.lazy_table.num_columns

    @property
    def column_names(self) -> list:
        return self.lazy_table.column_names

    @property
    def num_rows(self) -> int:
        return self.lazy_table.num_rows

    @property
    def num_filtered_rows(self) -> int:
        return self.lazy_filtered_table.num_rows

    @property
    def info(self) -> str:
        return f"File: {self.parquet_file}\r\n" \
               f"Size: {self.lazy_table.nbytes} Bytes\r\n" \
               f"Rows: {self.num_rows}\r\n" \
               f"Columns: {self.lazy_table.num_columns}"

    @property
    def schema(self) -> str:
        return self.lazy_table.schema.to_string()

    def get_data(self, batch: int) -> list:
        return self.lazy_batches[batch].to_pylist()

    def get_batch_first_row_number(self, batch: int) -> int:
        if batch == 0:
            return 0

        return sum(self.lazy_batches[b].num_rows for b in range(0, batch))
