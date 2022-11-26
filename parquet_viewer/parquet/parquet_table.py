import os.path
from typing import Dict

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
        self._pyarrow_filters = None
        self._filters = ""
        self._filtered_table = None

    @property
    def lazy_table(self) -> pa.Table:
        if self._table is None:
            self._table = pq.read_table(self.parquet_file)
        return self._table

    @property
    def lazy_filtered_table(self) -> pa.Table:
        if self._filtered_table is None:
            if not self._pyarrow_filters:
                self._filtered_table = self.lazy_table
            else:
                self._filtered_table = self.lazy_table.filter(self._pyarrow_filters)
        return self._filtered_table

    @property
    def filter_builder(self) -> PyArrowFilterBuilder:
        if self._filter_builder is None:
            self._filter_builder = PyArrowFilterBuilder(table=self.lazy_table)
        return self._filter_builder

    @property
    def filters(self) -> str:
        return self._filters

    @filters.setter
    def filters(self, filters: str) -> None:
        filters = filters.strip()
        if not filters:
            self._pyarrow_filters = None
        else:
            filters_tree = filter_parser.parse(filters)
            self._pyarrow_filters = self.filter_builder.transform(filters_tree)

        self.reset_batches()
        self._filters = filters

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
    def schema(self) -> str:
        return self.lazy_table.schema.to_string()

    def get_data(self, batch: int) -> list:
        if batch < 0 or batch >= self.num_batches:
            return []

        return self.lazy_batches[batch].to_pylist()

    def get_batch_first_row_number(self, batch: int) -> int:
        if batch <= 0 or batch >= self.num_batches:
            return 0

        return sum(self.lazy_batches[b].num_rows for b in range(0, batch))

    @property
    def info(self) -> Dict[str, str]:
        return {
            "File": str(self.parquet_file),
            "Columns": str(self.lazy_table.num_columns),
            "Total Rows": str(self.num_rows),
            "Total Size": f"{self.lazy_table.nbytes} Bytes",
            "Filters": str(self.filters),
            "Filtered Rows": str(self.num_filtered_rows),
            "Filtered Size": f"{self.lazy_filtered_table.nbytes} Bytes"
        }

    def __str__(self) -> str:
        return "Parquet Table\r\n" + "\r\n".join(f"{k}:{v}" for k, v in self.info.items())
