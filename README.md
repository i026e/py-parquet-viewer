# Parquet Viewer
GUI application based on PyArrow + QT framework to view *.parquet files
Requires python version 3.8+

## Screenshots

## Installation

## Development

Clone repo from GitHub
```shell
git clone git@github.com:i026e/py-parquet-viewer.git
```

Create virtual environment and install dependencies with [poetry](https://python-poetry.org/docs/managing-environments):

```shell
python3 -m venv .venv
source .venv/bin/activate
pip3 install poetry
poetry install
```

To run the application
```shell
poetry run parquet-viewer [path/to/parquet/file]
```

To change the UI layout you need [QTDesigner](https://doc.qt.io/qt-5/qtdesigner-manual.html)
Run `qt_designer/run_qt_designer.sh` script to launch it with required plugins loaded

## Attribution
* [PyQT Framework](https://doc.qt.io/qtforpython/)

* [PyArrow Library](https://arrow.apache.org/docs/python/index.html)

* [Floor icons created by Freepik - Flaticon](https://www.flaticon.com/free-icons/floor)