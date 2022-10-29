import os
import fnmatch
from sys import platform

import PyInstaller.__main__

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
DIST_DIR = os.path.join(SCRIPT_DIR, "dist")
WORK_DIR = os.path.join(SCRIPT_DIR, "build")

SEP = ";" if platform == "win32" else ":"


params = [
    f"--add-data={os.path.join(SCRIPT_DIR, 'parquet_viewer/qt/ui/parquet_viewer.ui')}{SEP}parquet_viewer/qt/ui",
    f"--add-binary={os.path.join(SCRIPT_DIR, 'parquet_viewer/qt/ui/floor.png')}{SEP}parquet_viewer/qt/ui",

    "--hidden-import=parquet_viewer.qt.widgets",
    "--hidden-import=parquet_viewer.qt.widgets.qt_reverted_spin_box",

    f"--distpath={DIST_DIR}",
    f"--workpath={WORK_DIR}",
    
    "--clean",
    "--noconfirm",
    "--onedir",

    f"--icon={os.path.join(SCRIPT_DIR, 'parquet_viewer/qt/ui/floor.png')}",
    "--name=parquet-viewer",
    "parquet-viewer.py",

]

#  KEEP!!!
"""
libopenblas64*
libicudata*
libgfortran*
"""

TO_REMOVE = [
    "libQt5Quick*",
    "libQt5Multimedia*",
    "libQt5Sql*",
    "libQt5Nfc*",
    "libQt5Network*",
    "libQt5Location*",
    "libQt5OpenGL*",
    "libQt5TextToSpeach*",
    "libQt5Bluetooth*",
    "libQt5Designer*",
    "libQt5Qml*",
    "libQt5XmlPatterns*",
    "libQt5SerialPort*",
    "libQt5EglFSDeviceIntegration.*",
    "libQt5PrintSupport.*",
    "libQt5EglFsKmsSupport.*",
    "libQt5WebSockets.*",
    "libQt5PositioningQuick.*",
    "libQt5Positioning.*",
    "libQt5RemoteObjects.*",

    "QtQuick.abi3.*",
    "QtMultimedia.abi3.*",
    "QtQml.abi3.*",
    "QtLocation.abi3.*",
    "QtBluetooth.abi3.*",
    "QtSql.abi3.*",
    "QtDesigner.abi3.*",
    "QtXml.abi3.*",
    "QtSensors.abi3.*",
    "QtPrintSupport.abi3.*",
    "QtNfc.abi3.*",
    "QtOpenGL.abi3.*",
    "QtMultimediaWidgets.abi3.*",
    "QtTest.abi3.*",
    "QtWebSockets.abi3.*",
    "QtSerialPort.abi3.*",
    "QtTextToSpeech.abi3.*",
    "QtQuick3D.abi3.*",


    "libasound*",
    "libgstreamer*",
    "libFLAC*",
    "libgstvideo*",
    "libpulse*",

    "libgtk-3*",

    "parquet-viewer/libarrow.*",
    "parquet-viewer/libarrow_dataset.*",
    "parquet-viewer/libarrow_python.*",
    "parquet-viewer/libparquet.*",
    "pyarrow/libarrow_flight.*",

    "parquet-viewer/libstdc++.*",
]


def clean_up(dist_dir: str, to_remove: list) -> None:
    to_remove = ["*" + v for v in to_remove]

    def check_delete(folder: str, file_name: str) -> bool:
        file_path = os.path.join(folder, file_name)

        for mask in to_remove:
            if fnmatch.fnmatch(file_path, mask):
                print("Deleting file", file_path)
                os.unlink(file_path)
                return True
        return False

    for root, sub_dirs, files in os.walk(dist_dir):
        for f in files:
            check_delete(root, f)


def main() -> None:
    print("Executable file will be created in", DIST_DIR, "folder")
    PyInstaller.__main__.run(params)
    clean_up(DIST_DIR, TO_REMOVE)
    print("Done")


if __name__ == "__main__":
    main()




