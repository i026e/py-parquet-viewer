#!/usr/bin/env bash

set -e

BASE_DIR="$(dirname "$(readlink -f "$0")")"
PROJECT_DIR="$(dirname ${BASE_DIR})"
PLUGINS_DIR="${BASE_DIR}/plugins"

UI_FILE="${PROJECT_DIR}/parquet_viewer/qt/ui/parquet_viewer.ui"

export PYTHONPATH=${PROJECT_DIR}:${PYTHONPATH}
export PYQTDESIGNERPATH=${PLUGINS_DIR}:${PYQTDESIGNERPATH}


echo "Opening ${UI_FILE}"
designer "${UI_FILE}"