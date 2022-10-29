import os
import sys
from typing import Optional, List, Any

import lark
import pyarrow as pa

from PyQt5 import uic
from PyQt5.QtCore import QEvent
from PyQt5.QtGui import QKeySequence

from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QMessageBox, QShortcut

from parquet_viewer.parquet.parquet_table import ParquetTable
from parquet_viewer._logger import log_error
from parquet_viewer.qt.qt_table_model import ParquetTableModel


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))


class ParquetViewerGUI(QMainWindow):
    UI_FILE = os.path.join(SCRIPT_DIR, "ui", "parquet_viewer.ui")
    PAGE_SIZES = [20, 40, 80]

    def __init__(self):
        super().__init__()
        uic.loadUi(self.UI_FILE, self)

        self.parquet_table: Optional[ParquetTable] = None
        self.parquet_model: Optional[ParquetTableModel] = None

        self.setupPageBox()
        self.setupSignals()
        self.setupShortCuts()

    def getPageSize(self) -> int:
        return self.PAGE_SIZES[self.pageSizeBox.currentIndex()]

    def setupShortCuts(self):
        filters_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        filters_shortcut.activated.connect(self.filtersEdit.setFocus)

    def setupSignals(self) -> None:
        self.actionOpen.triggered.connect(self.openFile)
        self.actionQuit.triggered.connect(self.close)
        self.actionAbout.triggered.connect(self.showAbout)

        self.filtersApplyButton.clicked.connect(self.applyFilters)
        self.filtersEdit.returnPressed.connect(self.applyFilters)

        self.tableView.installEventFilter(self)

    def setupPageBox(self) -> None:
        self.pageSizeBox.addItems(str(s) for s in self.PAGE_SIZES)
        self.pageSizeBox.setCurrentIndex(0)

        self.pageSizeBox.currentIndexChanged.connect(self.updatePageSize)
        self.pageBox.valueChanged.connect(self.loadCurrentPage)

    def updatePages(self) -> None:
        if self.parquet_table is not None:
            self.totalPages.setText(str(self.parquet_table.num_batches))
            self.pageBox.setMaximum(max(1, self.parquet_table.num_batches))

            self.pageBox.setValue(1)
            self.pageBox.setEnabled(True)
            self.loadCurrentPage()

    def updatePageSize(self) -> None:
        if self.parquet_table is not None:
            page_size = self.getPageSize()
            self.parquet_table.batch_size = page_size
            self.updatePages()

    def openFile(self) -> None:
        file_path = QFileDialog.getOpenFileName(self, "Open file", "","Parquet files (*.parquet)")[0]
        if file_path:
            self.loadData(file_path)

    def loadData(self, parquet_file: str) -> None:
        try:
            self.parquet_table = ParquetTable(parquet_file, self.getPageSize())
            self.parquet_model = ParquetTableModel(self.parquet_table)
            self.tableView.setModel(self.parquet_model)

            self.schemaEdit.clear()
            self.schemaEdit.appendPlainText(self.parquet_table.schema)

            self.infoEdit.clear()
            self.infoEdit.appendPlainText(self.parquet_table.info)

            self.updatePages()
            self.loadCurrentPage()

        except FileNotFoundError as e:
            log_error(e)
            self.showError(f"File not found: \n{parquet_file}")
        except pa.lib.ArrowInvalid as e:
            log_error(e)
            self.showError(f"Not a valid parquet file: \n{parquet_file}")
        except Exception as e:
            log_error(e)
            self.showError(f"Cannot load file \n{parquet_file}\n", e)

    def loadCurrentPage(self) -> None:
        page = self.pageBox.value()
        self.parquet_model.setPage(page - 1)

    def applyFilters(self) -> None:
        filters = self.filtersEdit.text().strip()
        try:
            self.parquet_table.filters = filters
            self.updatePages()
        except (lark.exceptions.UnexpectedInput, lark.exceptions.VisitError) as e:
            log_error(e)
            self.showError(e)
        except Exception as e:
            log_error(e)
            self.showError("Unexpected Error", detail=e)

    def showError(self, message: Any, detail: Any = None, error_from_show_error=False) -> None:
        try:
            error_msg = QMessageBox(self)
            error_msg.setIcon(QMessageBox.Critical)
            error_msg.setWindowTitle("Error")
            error_msg.setText(str(message))

            if detail:
                error_msg.setDetailedText(str(detail))

            error_msg.show()
        except Exception as e:
            log_error(e)
            if not error_from_show_error:
                self.showError("Unexpected error", e, error_from_show_error=True)

    def showAbout(self) -> None:
        from parquet_viewer._version import get_about, get_details

        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("About")
        msg.setText(get_about())
        msg.setDetailedText(get_details())

        msg.show()

    def eventFilter(self, source, event) -> bool:
        if (source == self.tableView) and (event.type() == QEvent.KeyPress) and event.matches(QKeySequence.Copy):
            self.copySelection()
            return True
        return super().eventFilter(source, event)

    def copySelection(self) -> None:
        selection =self.tableView.selectedIndexes()
        selected_data = self.parquet_model.getSelectionData(selection)
        QApplication.clipboard().setText(selected_data)


def run_app(qt_args: List[str], parquet_file: Optional[str] = None) -> None:
    app = QApplication(qt_args)
    window = ParquetViewerGUI()
    window.show()

    if parquet_file:
        window.loadData(parquet_file)

    sys.exit(app.exec_())
