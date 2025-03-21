# PyQt5 modules
from PyQt5 import QtWidgets, QtGui

# Python modules
import sys
import os

# Main window ui import
from src.mainwindow import MainWindow


def main():
    app = QtWidgets.QApplication(sys.argv)
    if(os.name == 'nt'):
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('tc2.plottool.1')
    window = MainWindow()
    window.show()
    window.setWindowIcon(QtGui.QIcon('icon.png'))
    sys.exit(app.exec())
