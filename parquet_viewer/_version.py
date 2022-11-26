APP_NAME = "Parquet Viewer"
APP_VERSION = "0.2.1"
APP_LICENSE = "GPLv3"
WEB_PAGE = "<a href='https://github.com/i026e/py-parquet-viewer/releases'>GitHub</a>"
APP_AUTHORS = "[Pavel K. &lt;<a href='mailto:klev.paul@gmail.com'>klev.paul@gmail.com</a>&gt;; ]"


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
