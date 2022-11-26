from typing import Any, Dict

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
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Information)
    msg.setWindowTitle("About")
    msg.setText(get_about_table())
    msg.setDetailedText(get_details_text())

    msg.show()


def create_html_table(data: Dict, border: int = 0, cell_spacing: int = 1, width: int = 100) -> str:
    table = f"<table border='{border}' cellspacing='{cell_spacing}' width='{width}%'>\n"
    for key, val in data.items():
        table += f"<tr><td>{key}:</td><td>{val}</td></tr>\n"

    table += "</table>\n"
    return table


def get_about_table() -> str:
    from parquet_viewer._version import (
        APP_NAME,
        APP_VERSION,
        WEB_PAGE,
        APP_LICENSE,
        APP_AUTHORS
    )

    return f"<b>{APP_NAME}</b>\n<br/>\n" + create_html_table({
        "Version": APP_VERSION,
        "Web": WEB_PAGE,
        "Licence": APP_LICENSE,
        "Authors": APP_AUTHORS
    }, border=0, cell_spacing=8)


def get_details_text() -> str:
    from parquet_viewer._version import (
        get_platform,
        get_platform_version,
        get_py_version,
        get_qt_version,
        get_py_qt_version,
        get_pyarrow_version
    )

    details = {
        "Platform": get_platform(),
        "Platform Version": get_platform_version(),
        "Python Version": get_py_version(),
        "QT Version": get_qt_version(),
        "PyQt Version": get_py_qt_version(),
        "PyArrow Version": get_pyarrow_version()
    }

    return "\r\n".join(f"{k}: {v}" for k, v in details.items())
