APP_NAME = "Parquet Viewer"
APP_VERSION = "0.1.0"
APP_LICENSE = "GPLv3"
APP_AUTHORS = "[Pavel &lt;<a href='https://github.com/i026e/'>GitHub</a>&gt;; ]"


def get_qt_version() -> str:
    from PyQt5.QtCore import QT_VERSION_STR
    return QT_VERSION_STR


def get_py_qt_version() -> str:
    from PyQt5.Qt import PYQT_VERSION_STR
    return PYQT_VERSION_STR


def get_platform() -> str:
    import platform
    return platform.platform()


def get_platform_version() -> str:
    import platform
    return platform.version()


def get_py_version() -> str:
    import sys
    return sys.version


def get_pyarrow_version() -> str:
    import pyarrow
    return pyarrow.__version__


def get_about() -> str:
    return f"""<b>{APP_NAME}</b>

<br/>
<table>

<tr>
<td>Version:</td><td>{APP_VERSION}</td>
</tr>

<tr>
<td>Licence:</td><td>{APP_LICENSE}</td>
</tr>

<tr>
<td>Authors:</td><td>{APP_AUTHORS}</td>
</tr>

</table>
"""


def get_details() -> str:
    return f"""Platform: {get_platform()}
Platform Version: {get_platform_version()}

Python Version: {get_py_version()}

QT Version: {get_qt_version()}
PyQt Version: {get_py_qt_version()}

PyArrow Version: {get_pyarrow_version()}
"""
