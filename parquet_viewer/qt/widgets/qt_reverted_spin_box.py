from PyQt5 import QtWidgets


class RevertedSpinBox(QtWidgets.QSpinBox):
    def stepEnabled(self):
        if self.wrapping() or self.isReadOnly():
            return super().stepEnabled()
        ret = QtWidgets.QAbstractSpinBox.StepNone
        if self.value() > self.minimum():
            ret |= QtWidgets.QAbstractSpinBox.StepUpEnabled
        if self.value() < self.maximum():
            ret |= QtWidgets.QAbstractSpinBox.StepDownEnabled
        return ret

    def stepBy(self, steps):
        return super().stepBy(-steps)
