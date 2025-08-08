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
        self.tf_raw.textChanged.connect(self.exprUpdated)
        self.button_ok = self.OK_btn.button(QtWidgets.QDialogButtonBox.Ok)
        self.button_ok.setEnabled(False)
        #self.check_btn.clicked.connect(self.processTFValues)

    def getTFTitle(self):
        return self.tf_title.text()

    def enableTFFunction(self, txt):
        if txt != '':
            self.tf_raw.setEnabled(True)

    def exprUpdated(self, txt):
        self.drawExpression(txt.lower())
        err_txt = self.tf.setExpression(self.tf_raw.text().lower())
        self.error_label.setText(str(err_txt))
        self.button_ok.setEnabled(err_txt == '')

    def drawExpression(self, txt):
        txt = txt.lower()
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
        except Exception as e:
            pass

    def validateTF(self):
        err_txt = self.tf.setExpression(self.tf_raw.text().lower())
        if('EOF in multi-line statement' in err_txt):
            return 'Mismatched parentheses'
        else:
            return err_txt
