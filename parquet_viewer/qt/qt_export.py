import os
from typing import Any, Optional

from PyQt5 import uic
from PyQt5.QtCore import QObject, pyqtSignal, QThread, QMutex, QMutexLocker
from PyQt5.QtWidgets import QDialog, QFileDialog, QDialogButtonBox

from parquet_viewer._logger import LOGGER
from parquet_viewer.parquet.parquet_conversion import (
    OutputFormat,
    CsvDialect,
    ConversionProcess,
    ProgressData,
    ConversionStatus
)
from parquet_viewer.parquet.parquet_table import ParquetTable

from parquet_viewer.qt.qt_utils import qt_ask_confirmation, qt_show_error
from parquet_viewer.qt.ui import PARQUET_EXPORT_UI

EXTENSIONS = {
    OutputFormat.JSON: ".json",
    OutputFormat.CSV: ".csv"
}


class BackgroundExportController(QObject):
    POLLING_TIMEOUT = 0.1

    finished = pyqtSignal()
    updated = pyqtSignal(ProgressData)

    def __init__(
            self,
            parent: Any,
            parquet_table: ParquetTable,
            output_format: OutputFormat,
            output_file: str,
            csv_dialect: CsvDialect,
            apply_filters: bool
    ):
        super().__init__(parent=parent)

        self.output_format = output_format
        self.kwargs = dict(
            table=parquet_table.lazy_filtered_table if apply_filters else parquet_table.lazy_table,
            output_file=output_file,
            batch_size=parquet_table.batch_size,
            csv_dialect=csv_dialect
        )
        self.process = ConversionProcess(self.output_format, **self.kwargs)

    def updateProgress(self):
        for progress_data in self.process.get_progress(self.POLLING_TIMEOUT):
            self.updated.emit(progress_data)

    def start(self) -> None:
        with self.process:
            while self.process.is_running():
                self.updateProgress()

        self.updateProgress()
        self.finished.emit()

    def abort(self) -> None:
        self.process.abort()


class ParquetExportDialog(QDialog):
    UI_FILE = PARQUET_EXPORT_UI

    OUTPUT_FORMATS = list(OutputFormat)
    CSV_DIALECTS = list(CsvDialect)

    def __init__(self, parent: Any, parquet_table: ParquetTable, output_format: Optional[OutputFormat] = None) -> None:
        super().__init__(parent=parent)
        uic.loadUi(self.UI_FILE, self)

        self.mutex = QMutex()

        self.parquet_table = parquet_table
        self.export_controller: Optional[BackgroundExportController] = None
        self.export_thread: Optional[QThread] = None

        self.setupWidgets(output_format)

        self.setupSignals()
        self.formatChanged()
        self.exportCompleted()

    def setupWidgets(self, output_format: Optional[OutputFormat] = None) -> None:
        self.formatComboBox.addItems(f.name for f in self.OUTPUT_FORMATS)
        self.csvDialectBox.addItems(d.value for d in self.CSV_DIALECTS)

        if output_format is not None:
            self.formatComboBox.setCurrentIndex(self.OUTPUT_FORMATS.index(output_format))

        self.inputLocationEdit.setText(self.parquet_table.parquet_file)
        self.outputLocationEdit.setText(self.parquet_table.parquet_file)

    def setupSignals(self) -> None:
        self.formatComboBox.currentIndexChanged.connect(self.formatChanged)
        self.buttonBox.accepted.connect(self.runExport)
        self.buttonBox.rejected.connect(self.cancelExport)
        self.browseButton.clicked.connect(self.browseOutputFile)

    def getCurrentFormat(self) -> OutputFormat:
        return self.OUTPUT_FORMATS[self.formatComboBox.currentIndex()]

    def getCurrentCsvDialect(self) -> CsvDialect:
        return self.CSV_DIALECTS[self.csvDialectBox.currentIndex()]

    def getCurrentOutputLocation(self) -> str:
        return self.outputLocationEdit.text().strip()

    def getCurrentApplyFilters(self) -> bool:
        return self.applyFilterBox.isChecked()

    def formatChanged(self) -> None:
        format_ = self.getCurrentFormat()
        file_path = os.path.splitext(self.getCurrentOutputLocation())[0] + EXTENSIONS[format_]
        self.outputLocationEdit.setText(file_path)

        self.csvDialectBox.setEnabled(format_ == OutputFormat.CSV)

    def browseOutputFile(self) -> None:
        format_ = self.getCurrentFormat()
        extension = EXTENSIONS[format_]

        file_path = QFileDialog.getSaveFileName(self, "Save file", "", f"{format_.name} files (*{extension})")[0]
        if file_path:
            if not file_path.lower().endswith(extension):
                file_path += extension

            self.outputLocationEdit.setText(file_path)

    def runExport(self) -> None:
        with QMutexLocker(self.mutex):

            output_location = self.getCurrentOutputLocation()
            if os.path.exists(
                    output_location
            ) and not qt_ask_confirmation(
                self, f"Overwrite existing file\n'{output_location}' ?"
            ):
                return

            if self.export_controller is None:
                self.userInputFrame.setEnabled(False)
                self.progressBar.setEnabled(True)
                self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel)

                self.export_controller = BackgroundExportController(
                    parent=None,
                    parquet_table=self.parquet_table,
                    output_format=self.getCurrentFormat(),
                    output_file=output_location,
                    csv_dialect=self.getCurrentCsvDialect(),
                    apply_filters=self.getCurrentApplyFilters()
                )

                self.export_thread = QThread()
                self.export_controller.moveToThread(self.export_thread)

                self.export_thread.started.connect(self.export_controller.start)
                self.export_thread.finished.connect(self.export_thread.deleteLater)

                self.export_controller.finished.connect(self.export_thread.quit)
                self.export_controller.finished.connect(self.exportCompleted)
                self.export_controller.updated.connect(self.exportUpdated)

                self.export_thread.start()

    def exportUpdated(self, progress_data: ProgressData) -> None:
        LOGGER.debug(progress_data)

        format = f"{progress_data.status.value}: %p%"
        self.progressBar.setFormat(format)

        if progress_data.status == ConversionStatus.RUNNING:
            self.progressBar.setMaximum(progress_data.num_batches)
            self.progressBar.setValue(progress_data.batch)

        elif progress_data.status == ConversionStatus.FAILED:
            qt_show_error(self, "Export failed", detail=progress_data.context)

    def exportCompleted(self) -> None:
        with QMutexLocker(self.mutex):
            if self.export_controller is not None:
                self.export_controller.deleteLater()
                self.export_controller = None

            self.userInputFrame.setEnabled(True)
            self.buttonBox.setStandardButtons(QDialogButtonBox.Save | QDialogButtonBox.Close)

    def cancelExport(self) -> None:
        with QMutexLocker(self.mutex):
            if self.export_controller is None:
                self.close()

            else:
                if qt_ask_confirmation(self, "Abort export?"):
                    self.export_controller.abort()
