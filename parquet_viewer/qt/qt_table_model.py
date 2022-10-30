from collections import defaultdict
from typing import Any, Optional, List
from PyQt5.QtCore import QAbstractTableModel, Qt, QVariant, QModelIndex


from parquet_viewer.parquet.parquet_table import ParquetTable
from parquet_viewer.parquet.parquet_to_json import ExtendedJSONEncoder


class ParquetTableModel(QAbstractTableModel):
    MAX_STR_LEN = 256

    CONVERT_TO_STR = (bool,)
    NOT_CONVERT_TO_STR = (str, int, float)

    def __init__(self, parquet_table: ParquetTable) -> None:
        super().__init__()

        self.parquet_table = parquet_table
        self.column_headers = self.parquet_table.column_names

        self.parquet_data = []
        self.start_row_header = 1

    def columnCount(self, index=QModelIndex()) -> int:
        return len(self.column_headers)

    def rowCount(self, parent: QModelIndex = ...) -> int:
        return len(self.parquet_data)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return QVariant()

        if orientation == Qt.Horizontal:
            return QVariant(self.column_headers[section])

        return QVariant(int(section + self.start_row_header))

    def data(self, index: QModelIndex, role: int = ...) -> Any:
        if index.isValid():
            if role == Qt.DisplayRole or role == Qt.EditRole:
                return self.getCellData(
                    index.row(),
                    index.column(),
                    shorten=(role == Qt.DisplayRole)
                )

    def flags(self, index) -> Any:
        return Qt.ItemIsSelectable|Qt.ItemIsEnabled|Qt.ItemIsEditable

    def setPage(self, page: int) -> int:
        self.beginResetModel()

        self.parquet_data = self.parquet_table.get_data(page)
        self.start_row_header = self.parquet_table.get_batch_first_row_number(page) + 1

        self.endResetModel()

        return page

    def getCellData(self, row: int, col: int, shorten: bool) -> Optional[str]:
        value = self.parquet_data[row].get(self.column_headers[col])

        if value is None:
            return None

        value = str(value)

        if shorten and (len(value) > self.MAX_STR_LEN):
            value = value[:self.MAX_STR_LEN - 3] + "..."

        return value

    def getSelectionData(self, indices: List[QModelIndex]) -> Optional[str]:
        if not indices:
            return None

        json_encoder = ExtendedJSONEncoder(indent=2)

        # if len(indices) == 1:
        #     value = self.parquet_data[indices[0].row()].get(self.column_headers[indices[0].column()])
        #     return json_encoder.encode(value)

        data = defaultdict(dict)
        for index in sorted(indices, key=lambda i: (i.row(), i.column())):
            row = index.row()
            col = index.column()

            row_name = self.start_row_header + row
            col_name = self.column_headers[col]

            data[row_name][col_name] = self.parquet_data[row].get(col_name)

        return json_encoder.encode(data)
