# Parquet Viewer
GUI application based on QT framework to view *.parquet files
Requires python version 3.8+


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

## Attribution
[PyQT Framework](https://doc.qt.io/qtforpython/)
[PyArrow Library](https://arrow.apache.org/docs/python/index.html)
[Floor icons created by Freepik - Flaticon](https://www.flaticon.com/free-icons/floor)