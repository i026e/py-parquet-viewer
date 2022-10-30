import json
import os
import fnmatch
import subprocess
import tempfile
from sys import platform
from typing import List

import PyInstaller.__main__

from test.create_parquet_file import create_parquet_file

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
DIST_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "dist"))
WORK_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "build"))
APP_NAME = "parquet-viewer"
MAIN_FILE = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "parquet-viewer.py"))

SEP = ";" if platform == "win32" else ":"


PYINSTALLER_PARAMS = [
    f"--add-data={os.path.join(SCRIPT_DIR, '../parquet_viewer/qt/ui/parquet_viewer.ui')}{SEP}parquet_viewer/qt/ui",
    f"--add-binary={os.path.join(SCRIPT_DIR, '../parquet_viewer/qt/ui/floor.png')}{SEP}parquet_viewer/qt/ui",

    "--hidden-import=parquet_viewer.qt.widgets",
    "--hidden-import=parquet_viewer.qt.widgets.qt_reverted_spin_box",

    f"--distpath={DIST_DIR}",
    f"--workpath={WORK_DIR}",
    
    "--clean",
    "--noconfirm",
    "--onedir",
    "--windowed",

    f"--icon={os.path.join(SCRIPT_DIR, '../parquet_viewer/qt/ui/floor.png')}",
    f"--name={APP_NAME}",
    f"{MAIN_FILE}",

]

LIBS_WHITE_LIST = {
    "parquet-viewer/parquet_viewer/qt/ui/floor.png",
    "parquet-viewer/hashlib.pyc",
    "parquet-viewer/libQt5Gui.so.5",
    "parquet-viewer/libQt5XcbQpa.so.5",
    "parquet-viewer/libQt5DBus.so.5"
}



# def clean_up(dist_dir: str, to_remove: list) -> None:
#     to_remove = ["*" + v for v in to_remove]
#
#     def check_delete(folder: str, file_name: str) -> bool:
#         file_path = os.path.join(folder, file_name)
#
#         for mask in to_remove:
#             if fnmatch.fnmatch(file_path, mask):
#                 print("Deleting file", file_path)
#                 os.unlink(file_path)
#                 return True
#         return False
#
#     for root, sub_dirs, files in os.walk(dist_dir):
#         for f in files:
#             check_delete(root, f)

def remove_libs(dist_dir: str, unused_libs_list_filepath: str) -> None:
    with open(unused_libs_list_filepath, "r", encoding="utf-8") as f:
        libs_list = json.load(f)

        for line in libs_list:
            file_path = os.path.join(dist_dir, line)
            if os.path.isfile(file_path):
                print("Removing", file_path)
                os.unlink(file_path)


def check_app_works(command: List[str], timeout: int = 2) -> bool:
    def safe_kill(p):
        try:
            proc.kill()
        except:
            pass

    try:
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, shell=False)
        status = proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        safe_kill(proc)
        return True
    except Exception as e:
        pass

    return False


def find_unused_libs() -> str:
    checked_libs_filepath = os.path.join(WORK_DIR, "checked_libs.txt")
    unused_libs_filepath = os.path.join(WORK_DIR, "unused_libs.json")

    white_list = {os.path.join(DIST_DIR, r) for r in LIBS_WHITE_LIST}

    with tempfile.NamedTemporaryFile(suffix=".parquet") as tmp:
        parquet_file_path = create_parquet_file(tmp.name)
        command = [os.path.join(DIST_DIR, APP_NAME, APP_NAME), parquet_file_path]

        with open(checked_libs_filepath, "a+", encoding="utf-8") as checked_libs_file:
            checked_libs_file.seek(0)
            checked_libs = {}
            for line in checked_libs_file.readlines():
                line = line.strip()
                if line:
                    checked_libs.update(json.loads(line))

            for root, sub_dirs, files in os.walk(os.path.join(DIST_DIR, APP_NAME)):
                for f in files:

                    file_path = os.path.join(root, f)
                    tmp_path = file_path + ".tmp"

                    if file_path not in checked_libs and file_path not in white_list:
                        print("Checking", f)
                        os.rename(file_path, tmp_path)

                        app_work = check_app_works(command)

                        checked_libs[file_path] = app_work
                        checked_libs_file.write(json.dumps({file_path: app_work}, indent=None) + os.linesep)
                        checked_libs_file.flush()

                        if app_work:
                            print("Deleting", f)
                            os.unlink(tmp_path)
                        else:
                            os.rename(tmp_path, file_path)

    with open(checked_libs_filepath, "r", encoding="utf-8") as checked_libs_file:
        unused_libs = []

        for line in checked_libs_file.readlines():
            line = line.strip()
            if line:
                data = json.loads(line)
                for key, val in data.items():
                    if val:
                        path = key.removeprefix(DIST_DIR).lstrip("/").lstrip("\\")
                        if path not in LIBS_WHITE_LIST:
                            unused_libs.append(path)
        with open(unused_libs_filepath, "w", encoding="utf-8") as f:
            json.dump(unused_libs, f, indent=2)

    return unused_libs_filepath


def main() -> None:
    print("Executable file will be created in", DIST_DIR, "folder")
    PyInstaller.__main__.run(PYINSTALLER_PARAMS)
    #unused_libs_path = find_unused_libs()
    #remove_libs(DIST_DIR, unused_libs_path)
    print("Done")


if __name__ == "__main__":
    main()
