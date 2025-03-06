# Python modules
import sys
from PyQt5 import QtWidgets

# Project modules
from src.ui.tf_window import Ui_tf_window
from src.package.transfer_function import TFunction

class TFDialog(QtWidgets.QDialog, Ui_tf_window):
    def __init__(self, parent=None):
        super().__init__()
        self.setupUi(self)
        self.tf = TFunction()

        self.tf_title.textChanged.connect(self.enableTFFunction)
        self.tf_raw.textChanged.connect(self.drawExpression)
        self.check_btn.clicked.connect(self.processTFValues)

    def getTFTitle(self):
        return self.tf_title.text()

    def getTFExpression(self):
        return self.tf_raw.text()

    def enableTFFunction(self, txt):
        if txt != '':
            self.tf_raw.setEnabled(True)

    def drawExpression(self, txt):
        try:
            canvas = self.expr_plot.canvas
            canvas.ax.clear()
            canvas.ax.set_axis_off()
            canvas.ax.text(0.5,
                           0.5,
                           f"${self.tf.getLatex(txt)}$",
                           horizontalalignment='center',
                           verticalalignment='center',
                           fontsize=20,
                           transform=canvas.ax.transAxes)
            canvas.draw()
        except:
            pass

    def validateTF(self):
        return self.tf.setExpression(self.tf_raw.text())

    def processTFValues(self):
        if  self.validateTF():
            self.error_label.clear()
        else:
            self.error_label.setText("Revise function expression")