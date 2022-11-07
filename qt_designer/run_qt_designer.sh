#!/usr/bin/env sh

set -e

BASE_DIR="$(dirname "$(readlink -f "$0")")"
PROJECT_DIR="$(dirname ${BASE_DIR})"
PLUGINS_DIR="${BASE_DIR}/plugins"

UI_FILE_VIEWER="${PROJECT_DIR}/parquet_viewer/qt/ui/parquet_viewer.ui"
UI_FILE_EXPORT="${PROJECT_DIR}/parquet_viewer/qt/ui/parquet_export.ui"

export PYTHONPATH=${PROJECT_DIR}:${PYTHONPATH}
export PYQTDESIGNERPATH=${PLUGINS_DIR}:${PYQTDESIGNERPATH}


echo "Opening ${UI_FILE_VIEWER}, ${UI_FILE_EXPORT}"
designer "${UI_FILE_VIEWER}" "${UI_FILE_EXPORT}"