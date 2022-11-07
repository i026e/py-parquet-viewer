from typing import Any

from PyQt5.QtWidgets import QMessageBox

from parquet_viewer._logger import log_error


def qt_show_error(parent: Any, message: Any, detail: Any = None, error_from_show_error=False) -> None:
    try:
        error_msg = QMessageBox(parent)
        error_msg.setIcon(QMessageBox.Critical)
        error_msg.setWindowTitle("Error")
        error_msg.setText(str(message))

        if detail:
            error_msg.setDetailedText(str(detail))

        error_msg.show()
    except Exception as e:
        log_error(e)
        if not error_from_show_error:
            qt_show_error(parent=parent, message="Unexpected error", detail=e, error_from_show_error=True)


def qt_ask_confirmation(parent: Any, message: str, title: str = "Confirmation Required") -> bool:
    reply = QMessageBox.question(parent, title, message)
    return reply == QMessageBox.Yes


def qt_show_about(parent: Any) -> None:
    from parquet_viewer._version import get_about, get_details

    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Information)
    msg.setWindowTitle("About")
    msg.setText(get_about())
    msg.setDetailedText(get_details())

    msg.show()
