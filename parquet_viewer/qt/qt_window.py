import functools
import sys
from typing import Optional, List, Any

import lark
import pyarrow as pa

from PyQt5 import uic
from PyQt5.QtCore import QEvent
from PyQt5.QtGui import QKeySequence

from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QShortcut, QHeaderView

from parquet_viewer.parquet.parquet_conversion import OutputFormat
from parquet_viewer.parquet.parquet_table import ParquetTable
from parquet_viewer._logger import log_error
from parquet_viewer.qt.qt_utils import qt_show_error, qt_show_about, create_html_table
from parquet_viewer.qt.qt_export import ParquetExportDialog
from parquet_viewer.qt.qt_table_model import ParquetTableModel
from parquet_viewer.qt.ui import PARQUET_VIEWER_UI


class ParquetViewerGUI(QMainWindow):
    UI_FILE = PARQUET_VIEWER_UI
    PAGE_SIZES = [20, 40, 80]

    PARQUET_EXTENSION = ".parquet"

    def __init__(self):
        super().__init__()
        uic.loadUi(self.UI_FILE, self)

        self.parquet_table: Optional[ParquetTable] = None
        self.parquet_model: Optional[ParquetTableModel] = None

        self.setupPageBox()
        self.setupSignals()
        self.setupShortCuts()
        self.setupExport()

        self.setAcceptDrops(True)

    # Set up window
    def setupShortCuts(self):
        filters_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        filters_shortcut.activated.connect(self.filtersEdit.setFocus)

    def setupSignals(self) -> None:
        self.actionOpen.triggered.connect(self.openFile)
        self.actionQuit.triggered.connect(self.close)
        self.actionAbout.triggered.connect(self.showAbout)

        self.filtersApplyButton.clicked.connect(self.applyFilters)
        self.filtersEdit.returnPressed.connect(self.applyFilters)

        # allow copying cells
        self.tableView.installEventFilter(self)
        # table context menu
        self.tableView.addAction(self.actionCopyCell)
        self.actionCopyCell.triggered.connect(self.copySelection)

    def setupPageBox(self) -> None:
        self.pageSizeBox.addItems(str(s) for s in self.PAGE_SIZES)
        self.pageSizeBox.setCurrentIndex(0)

        self.pageSizeBox.currentIndexChanged.connect(self.updatePageSize)
        self.pageBox.valueChanged.connect(self.loadCurrentPage)

    # Update Window
    def updateTabs(self) -> None:
        if self.parquet_table is not None:
            self.schemaEdit.clear()
            self.schemaEdit.appendPlainText(self.parquet_table.schema)

            self.infoEdit.clear()
            self.infoEdit.setHtml(create_html_table(self.parquet_table.info, border=1, cell_spacing=4))

            self.updatePagesBox()

            # fix issue with horizontal headers width
            self.tableView.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
            # self.tableView.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

    def updatePagesBox(self) -> None:
        if self.parquet_table is not None:
            self.totalPages.setText(str(max(1, self.parquet_table.num_batches)))

            num_pages = self.parquet_table.num_batches

            self.pageBox.setMaximum(max(1, num_pages))
            self.pageBox.setValue(1)
            self.pageBox.setEnabled(True)
            self.loadCurrentPage()

    def updatePageSize(self) -> None:
        if self.parquet_table is not None:
            page_size = self.getPageSize()
            self.parquet_table.batch_size = page_size
            self.updatePagesBox()

    # Load data
    def loadCurrentPage(self) -> None:
        page = self.pageBox.value()
        self.parquet_model.setPage(page - 1)

    def openFile(self) -> None:
        file_path = QFileDialog.getOpenFileName(self, "Open file", "", f"Parquet files (*{self.PARQUET_EXTENSION})")[0]
        if file_path:
            self.loadData(file_path)

    def loadData(self, parquet_file: str) -> None:
        try:
            self.parquet_table = ParquetTable(parquet_file, self.getPageSize())
            self.parquet_model = ParquetTableModel(self.parquet_table)
            self.tableView.setModel(self.parquet_model)

            self.updateTabs()
            self.loadCurrentPage()
            self.enableExport()

        except FileNotFoundError as e:
            log_error(e)
            qt_show_error(self, f"File not found: \n{parquet_file}")
        except pa.lib.ArrowInvalid as e:
            log_error(e)
            qt_show_error(self, f"Not a valid parquet file: \n{parquet_file}")
        except Exception as e:
            log_error(e)
            qt_show_error(self, f"Cannot load file \n{parquet_file}\n", e)

    # Filters
    def applyFilters(self) -> None:
        filters = self.filtersEdit.text().strip()
        try:
            self.parquet_table.filters = filters
            self.updateTabs()
        except (lark.exceptions.UnexpectedInput, lark.exceptions.VisitError) as e:
            log_error(e)
            qt_show_error(self, e)
        except Exception as e:
            log_error(e)
            qt_show_error(self, "Unexpected Error", detail=e)

    # Copy data
    def eventFilter(self, source, event) -> bool:
        if (source == self.tableView) and (event.type() == QEvent.KeyPress) and event.matches(QKeySequence.Copy):
            self.copySelection()
            return True
        return super().eventFilter(source, event)

    def copySelection(self) -> None:
        selection = self.tableView.selectedIndexes()
        selected_data = self.parquet_model.getSelectionData(selection)
        QApplication.clipboard().setText(selected_data)

    # Export
    def setupExport(self) -> None:
        self.menuExport.setEnabled(False)

        self.actionExportJSON.triggered.connect(functools.partial(self.exportParquet, OutputFormat.JSON))
        self.actionExportCSV.triggered.connect(functools.partial(self.exportParquet, OutputFormat.CSV))

    def enableExport(self) -> None:
        self.menuExport.setEnabled(True)

    def exportParquet(self, output_format: Optional[OutputFormat] = None) -> None:
        if self.parquet_table is not None:
            try:
                export_dialog = ParquetExportDialog(self, output_format=output_format, parquet_table=self.parquet_table)
                export_dialog.show()
            except Exception as e:
                log_error(e)
                qt_show_error(self, "Unexpected error", e)

    # Drag and Drop
    def getFilesFromDropEvent(self, event: Any) -> List[str]:
        return [str(url.toLocalFile()) for url in event.mimeData().urls()]

    def dragEnterEvent(self, event: Any) -> Any:
        if event.mimeData().hasUrls():
            paths = self.getFilesFromDropEvent(event)
            if len(paths) == 1 and paths[0].endswith(self.PARQUET_EXTENSION):
                return event.accept()

        return event.ignore()

    def dropEvent(self, event: Any) -> None:
        paths = self.getFilesFromDropEvent(event)
        if paths:
            self.loadData(paths[0])

    # Other
    def showAbout(self) -> None:
        qt_show_about(self)

    def getPageSize(self) -> int:
        return self.PAGE_SIZES[self.pageSizeBox.currentIndex()]


def run_app(qt_args: List[str], parquet_file: Optional[str] = None) -> None:
    app = QApplication(qt_args)
    window = ParquetViewerGUI()
    window.show()

    if parquet_file:
        window.loadData(parquet_file)

    sys.exit(app.exec_())
