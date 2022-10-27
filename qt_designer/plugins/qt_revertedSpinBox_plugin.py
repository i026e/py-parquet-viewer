#!/usr/bin/env python3

from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtDesigner import QPyDesignerCustomWidgetPlugin

from parquet_viewer.qt.widgets.qt_reverted_spin_box import RevertedSpinBox


class RevertedSpinBoxPlugin(QPyDesignerCustomWidgetPlugin):
    """Plugin for exampleWidget functionality.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

    def createWidget(self, parent, *args, **kwargs):
        return RevertedSpinBox(parent=parent)

    def name(self):
        return "RevertedSpinBox"

    def group(self):
        return "Input Widgets"

    def icon(self):
        return QIcon()

    def toolTip(self):
        return "Spinbox with reverted input"

    def whatsThis(self):
        return ""

    def isContainer(self):
        return False

    def domXml(self):
        return '<widget class="RevertedSpinBox" name="RevertedSpinBox">\n</widget>'

    def includeFile(self):
        return "parquet_viewer.qt.widgets.qt_reverted_spin_box"
