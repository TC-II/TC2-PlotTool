import sys
from PyQt5 import QtWidgets, QtCore, QtGui

from src.ui.fleischertow_window import Ui_fleischertow_dialog
from src.package.CellCalculator import FleischerTow
from src.package.transfer_function import TFunction
import numpy as np

class FleischerTowDialog(QtWidgets.QDialog, Ui_fleischertow_dialog):
    def __init__(self, parent=None):
        super().__init__()
        self.setupUi(self)
        self.calc_btn.clicked.connect(self.calculateResistors)
        self.cpyclipboard_btn.clicked.connect(self.copyParamToClipboard)
        self.cell = {}
        self.Rlabels = [0, self.R1_val, self.R2_val, self.R3_val, self.R4_val, self.R5_val, self.R6_val, self.R7_val,self.R8_val]
        self.tf = {}


    def populate(self, stage_tf):
        if(not isinstance(stage_tf, TFunction)):
            return
        self.tf = stage_tf
        N = [0] * (3 - len(stage_tf.N))
        N.extend(stage_tf.N)
        D = [0] * (3 - len(stage_tf.D))
        D.extend(stage_tf.D)
        self.N = np.array(N)
        self.D = np.array(D)

        a = D[1] / D[0]
        b = D[2] / D[0]
        wz = np.sqrt(N[2] / N[0]) # la div por D[0] se cancela
        wp = np.sqrt(b)
        Q = np.sqrt(b) / a
        fp = wp / (2*np.pi)
        bw = fp / Q
        self.f0_val.setText(str(fp))
        print(fp)
        self.w0_val.setText(str(wp))
        print(wp)
        self.Q_val.setText(str(Q))
        print(Q)
        self.bw_val.setText(str(bw))
        print(bw)

    def calculateResistors(self):
        self.cell = FleischerTow(self.C1_sb.value(), self.C2_sb.value(), self.R8_sb.value(), self.k1_sb.value(), self.k2_sb.value())
        self.cell.calculateComponentsND(self.N, self.D)
        for i, res in enumerate(self.cell.resistors):
            if(i == 0): continue
            self.Rlabels[i].setText(str(res))

    def copyParamToClipboard(self):
        clipboard = QtCore.QCoreApplication.instance().clipboard()
        s = '.param '
        for i, res in enumerate(self.cell.resistors[1:]):
            s += "R{:}={:} ".format(i + 1, res)
        for i, res in enumerate(self.cell.capacitors[1:]):
            s += "C{:}={:} ".format(i + 1, res)
        clipboard.setText(s)
        