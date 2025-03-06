from PyQt5 import QtWidgets, QtGui, QtCore

import typing

class CheckableComboBox(QtWidgets.QComboBox):
    def __init__(self, arg):
        super(CheckableComboBox, self).__init__()
        self.view().pressed.connect(self.handleItemPressed)
        self.setModel(QtGui.QStandardItemModel(self))
        self._changed = False

    def handleItemPressed(self, index):
        item = self.model().itemFromIndex(index)
        if item.checkState() == QtCore.Qt.Checked:
            item.setCheckState(QtCore.Qt.Unchecked)
        else:
            item.setCheckState(QtCore.Qt.Checked)
        self._changed = True
        
    def hidePopup(self):
        if not self._changed:
            super(CheckableComboBox, self).hidePopup()
        self._changed = False

    def item_checked(self, index):
        item = self.model().item(index, 0)
        return item.checkState() == QtCore.Qt.Checked

    def get_checked_items(self):
        checkedItems = []
        for i in range(self.count()):
            if self.item_checked(i):
                checkedItems.append(i)
        return checkedItems

    def currentIndexes(self):
        return self.get_checked_items()
    
    def setCurrentIndexes(self, indexes):
        for i in range(self.count()):
            item = self.model().item(i, 0)
            item.setCheckState(QtCore.Qt.Checked if i in indexes else QtCore.Qt.Unchecked)