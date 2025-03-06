# Python modules
import sys
from PyQt5 import QtWidgets

# Project modules
from src.ui.response_window import Ui_ResponseDialog

import ast
import numpy as np
import scipy.signal as signal

class ResponseDialog(QtWidgets.QDialog, Ui_ResponseDialog):
    def __init__(self, parent=None):
        super().__init__()
        self.setupUi(self)
        self.input_txt.setEnabled(True)
        self.input_txt.textChanged.connect(self.enableResponseFunction)
        self.check_btn.clicked.connect(self.processResponseValues)
    
    def setResponseHelp(self):
        try:
            canvas = self.expr_plot.canvas
            canvas.ax.clear()
            canvas.ax.set_axis_off()
            canvas.ax.text("AYUDA \n")
            canvas.draw()
        except:
            pass

    def getResponseTitle(self):
        return self.resp_name_txt.text()

    def getResponseExpression(self):
        return self.input_txt.text()
    
    def getTimeDomain(self):
        return np.arange(self.minbox.value(), self.maxbox.value(), self.stepbox.value())

    def enableResponseFunction(self, txt):
        if txt != '':
            self.input_txt.setEnabled(True)
    
    def validateResponse(self):
        try:
            ast.parse(self.input_txt.text())
            if (self.minbox.value() >= self.maxbox.value()):
                return False
        except SyntaxError:
            return False
        return True

    def processResponseValues(self):
        if self.validateResponse():
            self.error_label.clear()
        else:
            self.error_label.setText("La expresión y/o los límites no son válidos")