from typing import Any
from PyQt5.QtCore import pyqtSlot, QAbstractTableModel, Qt, QVariant, QModelIndex, pyqtSignal


from parquet_viewer.parquet.parquet_table import ParquetTable


class ParquetTableModel(QAbstractTableModel):
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
                value = self.parquet_data[index.row()].get(self.column_headers[index.column()])
                if value is not None and not isinstance(value, (str, int, float)):
                    value = str(value)
                return value

    def flags(self, index) -> Any:
        return Qt.ItemIsSelectable|Qt.ItemIsEnabled|Qt.ItemIsEditable

    def setPage(self, page: int) -> int:
        self.beginResetModel()

        page = max(0, min(page, self.parquet_table.num_batches - 1))
        self.parquet_data = self.parquet_table.get_data(page)
        self.start_row_header = self.parquet_table.get_batch_first_row_number(page) + 1

        self.endResetModel()

        return page
