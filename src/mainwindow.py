# PyQt5 modules
from math import inf
from PyQt5.QtWidgets import QMainWindow, QListWidgetItem, QColorDialog, QFileDialog, QDialog, QStyle
from PyQt5.QtCore import Qt, QCoreApplication

# Project modules
from src.ui.mainwindow import Ui_MainWindow
from src.package.Dataset import Dataset
import src.package.Filter as Filter
import src.package.CellCalculator as CellCalculator
import src.package.transfer_function as TF
from src.package.Filter import AnalogFilter, NORM_CB_DC, NORM_CB_HF, NORM_CB_BP, NORM_CB_PB
from src.widgets.fleischer_tow_window import FleischerTowDialog
from src.widgets.tf_dialog import TFDialog
from src.widgets.case_window import CaseDialog
from src.widgets.zp_window import ZPWindow
from src.widgets.response_dialog import ResponseDialog
from src.widgets.prompt_dialog import PromptDialog

from scipy.signal import savgol_filter
import scipy.signal as signal
import matplotlib.ticker as ticker
from matplotlib.pyplot import Circle
from mplcursors import  cursor, Selection

import numpy as np
import random
from pyparsing.exceptions import ParseSyntaxException

import pickle

MARKER_STYLES = { 'None': '', 'Point': '.',  'Pixel': ',',  'Circle': 'o',  'Triangle down': 'v',  'Triangle up': '^',  'Triangle left': '<',  'Triangle right': '>',  'Tri down': '1',  'Tri up': '2',  'Tri left': '3',  'Tri right': '4',  'Octagon': '8',  'Square': 's',  'Pentagon': 'p',  'Plus (filled)': 'P',  'Star': '*',  'Hexagon': 'h',  'Hexagon alt.': 'H',  'Plus': '+',  'x': 'x',  'x (filled)': 'X',  'Diamond': 'D',  'Diamond (thin)': 'd',  'Vline': '|',  'Hline': '_' }
LINE_STYLES = { 'None': '', 'Solid': '-', 'Dashed': '--', 'Dash-dot': '-.', 'Dotted': ':' }
DEFAULT_COLORS = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2']
CANON_COLORS = [
    '#1f77b4',      # azul, butter
    '#d62728',      # rojo, cheby I
    '#2ca02c',      # verde, cheby II
    '#ff7f0e',      # naranja, cauer
    '#9467bd',      # violeta, optimo l
    '#e377c2',      # rosa, bessel
    '#8c564b',      # marrón, gauss
]

POLE_COLOR = '#FF0000'
POLE_SEL_COLOR = '#00FF00'
ZERO_COLOR = '#0000FF'
ZERO_SEL_COLOR = '#00FF00'

TEMPLATE_FACE_COLOR = '#ffcccb'
TEMPLATE_EDGE_COLOR = '#ef9a9a'
ADD_TEMPLATE_FACE_COLOR = '#c8e6c9'
ADD_TEMPLATE_EDGE_COLOR = '#a5d6a7'


F_TO_W = 2*np.pi
W_TO_F = 1/F_TO_W

PZ_LIM_SCALING = 1.35

def stage_to_str(stage, k):
    stage_str = 'Z={'
    for z in stage.z:
        stage_str += "{0:.3}j".format(np.imag(z))
        stage_str += ', '
    if(len(stage.z) > 0):
        stage_str = stage_str[0:-2]
    stage_str += '} , P={'
    for p in stage.p:
        stage_str += "{0:.3g}".format(p)
        stage_str += ', '
    if(len(stage.p) > 0):
        stage_str = stage_str[0:-2]
    stage_str += '}} , K={0:.2g} dB'.format(20*np.log10(stage.gain))
    return stage_str

class MainWindow(QMainWindow, Ui_MainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.droppedFiles = []
        self.datasets = []
        self.datalines = []
        # self.stage_datasets = [] capaz mas adelante lo ponga para serializar también las etapas, pero creo que para ahora es mucho
        self.selected_dataset_widget = {}
        self.selected_dataline_widget = {}
        self.selected_dataset_data = {}
        self.selected_dataline_data = {}
        self.zpWindow = type('ZPWindow', (), {})()
        
        self.import_file_btn.clicked.connect(self.importFiles)
        
        self.dataset_list.currentItemChanged.connect(self.populateSelectedDatasetDetails)
        self.ds_title_edit.textEdited.connect(self.updateSelectedDatasetName)
        self.ds_addline_btn.clicked.connect(self.addDataline)
        self.ds_remove_btn.clicked.connect(self.removeSelectedDataset)
        self.ds_poleszeros_btn.clicked.connect(self.showZPWindow)

        self.dataline_list.currentItemChanged.connect(self.populateSelectedDatalineDetails)
        self.dl_name_edit.textEdited.connect(self.updateSelectedDataline)
        self.dl_render_cb.activated.connect(self.updateSelectedDataline)
        self.dl_transform_cb.activated.connect(self.updateSelectedDataline)
        self.dl_xdata_cb.activated.connect(self.updateSelectedDataline)
        self.dl_xscale_sb.valueChanged.connect(self.updateSelectedDataline)
        self.dl_xoffset_sb.valueChanged.connect(self.updateSelectedDataline)
        self.dl_ydata_cb.activated.connect(self.updateSelectedDataline)
        self.dl_yscale_sb.valueChanged.connect(self.updateSelectedDataline)
        self.dl_yoffset_sb.valueChanged.connect(self.updateSelectedDataline)
        self.dl_color_edit.textEdited.connect(self.updateSelectedDataline)
        self.dl_style_cb.activated.connect(self.updateSelectedDataline)
        self.dl_linewidth_sb.valueChanged.connect(self.updateSelectedDataline)
        self.dl_marker_cb.activated.connect(self.updateSelectedDataline)
        self.dl_markersize_sb.valueChanged.connect(self.updateSelectedDataline)
        self.dl_remove_btn.clicked.connect(self.removeSelectedDataline)
        self.dl_savgol_wlen.valueChanged.connect(self.updateSelectedDataline)
        self.dl_savgol_ord.valueChanged.connect(self.updateSelectedDataline)

        self.dl_color_pickerbtn.clicked.connect(self.openColorPicker)

        self.respd = ResponseDialog()
        self.resp_btn.clicked.connect(self.openResponseDialog)
        self.respd.accepted.connect(self.resolveResponseDialog)

        self.tfd = TFDialog()
        self.function_btn.clicked.connect(self.openTFDialog)
        self.tfd.accepted.connect(self.resolveTFDialog)

        self.csd = CaseDialog()
        self.ds_caseadd_btn.clicked.connect(self.openCaseDialog)
        self.csd.accepted.connect(self.resolveCSDialog)

        self.pmptd = PromptDialog()
        
        self.plt_labelsize_sb.valueChanged.connect(self.updatePlots)
        self.plt_legendsize_sb.valueChanged.connect(self.updatePlots)
        self.plt_ticksize_sb.valueChanged.connect(self.updatePlots)
        self.plt_titlesize_sb.valueChanged.connect(self.updatePlots)
        self.plt_autoscale.clicked.connect(self.autoscalePlots)
        self.plt_legendpos.activated.connect(self.updatePlots)
        self.plt_grid.stateChanged.connect(self.updatePlots)
        self.tabbing_plots.currentChanged.connect(self.updatePlots)
        
        self.plots_canvases = [
            [ self.plot_1 ],
            [ self.plot_2_1, self.plot_2_2 ],
            [ self.plot_3 ],
            [ self.plot_4_1, self.plot_4_2 ],
            [ self.plot_5 ],
        ]
        self.dataline_gb.setEnabled(False)

    def updateFilterLegends(self):
        pass

    def updateComparisonAproxOptions(self, index):
        pass

    def selectUseCanonical(self):
        pass

    def selectUseRandom(self):
        pass

    def selectUseHz(self):
        if(self.actionUse_Hz.isChecked()):
            self.actionUse_rad_s.setChecked(False)
            self.updateFequencySettings(True)
        else:
            self.actionUse_rad_s.setChecked(True)
            self.selectUseRadians()

    def selectUseRadians(self):
        if(self.actionUse_rad_s.isChecked()):
            self.actionUse_Hz.setChecked(False)
            self.updateFequencySettings(False)
        else:
            self.actionUse_Hz.setChecked(True)
            self.selectUseHz()

    def updateFequencySettings(self, useHz):
        pass

    def addDataset(self, ds):
        qlwt = QListWidgetItem()
        qlwt.setData(Qt.UserRole, ds)
        qlwt.setText(ds.title)
        self.dataset_list.addItem(qlwt)
        self.datasets.append(ds)
        self.datalines.append([])
        self.dataset_list.setCurrentRow(self.dataset_list.count() - 1)

    def removeDataset(self, i):
        #Saco los datalines
        first_dataline_index = 0
        last_dataline_index = len(self.datalines[0])
        for x in range(self.dataset_list.count()):
            if(x == 0):
                first_dataline_index = 0
            else:    
                first_dataline_index += len(self.datalines[x - 1])
            if(x == i):
                break
        last_dataline_index = first_dataline_index + len(self.datalines[i])

        for x in range(first_dataline_index, last_dataline_index):
            self.dataline_list.takeItem(first_dataline_index)
        self.datalines.pop(i)

        ds = self.dataset_list.item(i).data(Qt.UserRole)
        if(ds.type == 'filter'):
            fi = self.filters.index(ds)
            self.filters.pop(fi)
            self.selfil_cb.removeItem(fi)
            self.stages_selfil_cb.removeItem(fi)
            if(self.selfil_cb.count() == 0):
                self.chg_filter_btn.setEnabled(False)
                self.fgetHhuman_btn.setEnabled(False)
                self.fgetHlatex_btn.setEnabled(False)
                self.sgetHhuman_btn.setEnabled(False)
                self.sgetHlatex_btn.setEnabled(False)
        self.dataset_list.takeItem(i)
        self.updatePlots()

    def addDataline(self):
        if(not self.selected_dataset_data):
            return
        dl = self.selected_dataset_data.create_dataline()
        qlwt = QListWidgetItem()
        qlwt.setData(Qt.UserRole, dl)
        qlwt.setText(dl.name)
        dli = 0
        for x in range(self.dataset_list.count()):
            ds = self.dataset_list.item(x).data(Qt.UserRole)
            dli += len(self.datalines[x])
            if(ds.origin == self.selected_dataset_data.origin):
                break
        self.dataline_list.insertItem(dli, qlwt)
        self.dataline_list.setCurrentRow(dli)
        self.datalines[self.dataset_list.currentRow()].append(dl)
        self.updateSelectedDataline()
        self.updatePlots()

    def removeDataline(self, i):        
        try:
            dsi, dli = self.getInternalDataIndexes(i)
            del self.datalines[dsi][dli]
            self.dataline_list.takeItem(i).data(Qt.UserRole)
            del self.dataset_list.item(dsi).data(Qt.UserRole).datalines[dli]
            if(self.dataline_list.currentRow() == -1):
                self.dataline_list.setCurrentRow(self.dataline_list.count() - 1)
        except AttributeError:
            pass
        except UnboundLocalError:
            pass
        self.updatePlots()
    
    def removeSelectedDataline(self, event):
        selected_row = self.dataline_list.currentRow()
        self.removeDataline(selected_row)

    def removeSelectedDataset(self, event):
        selected_row = self.dataset_list.currentRow()
        self.removeDataset(selected_row)

    def getInternalDataIndexes(self, datalineRow):
        i = self.dataline_list.currentRow()
        for x in range(self.dataset_list.count()):
            ds = self.dataset_list.item(x).data(Qt.UserRole)
            if(i >= len(self.datalines[x])):
                i = i - len(self.datalines[x])
            else:
                return (x, i)
        return (x, i)

    def dragEnterEvent(self, event):
        if(event.mimeData().hasUrls()):
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        self.statusbar.showMessage('Loading files')
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        self.processFiles(files)

    def importFiles(self):
        options = QFileDialog.Options()
        # options |= QFileDialog.DontUseNativeDialog
        files, _ = QFileDialog.getOpenFileNames(self,"Select files", "","All Files (*);;CSV files (*.csv);;SPICE output files (*.raw)", options=options)
        self.processFiles(files)

    def processFiles(self, filenamearray):
        for f in filenamearray:
            # try:
            ds = Dataset(filepath=f)
            dataset_items_origin = [
                self.dataset_list.item(x).data(Qt.UserRole).origin
                for x in range(self.dataset_list.count())
            ]
            if(ds.origin not in dataset_items_origin):
                self.droppedFiles.append(ds.origin)
                self.addDataset(ds)
            # except(ValueError):
            #     print('Wrong file config')
        self.statusbar.clearMessage()

    def openTFDialog(self):
        self.tfd.open()
        self.tfd.tf_title.setFocus()

    def resolveTFDialog(self):
        if not self.tfd.validateTF():
            return
        ds = Dataset(filepath='', origin=self.tfd.tf, title=self.tfd.getTFTitle())
        self.addDataset(ds)

    def openResponseDialog(self):
        self.respd.open()
        self.respd.input_txt.setFocus()

    def resolveResponseDialog(self):
        if not(self.respd.validateResponse()):
            return

        t = self.respd.getTimeDomain()
        expression = self.respd.getResponseExpression()
        title = self.respd.getResponseTitle()
        time_title = title + "_timebase"
        ans_title = title + "_ans"
        
        if expression == 'step':
            x = np.heaviside(t, 0.5)
            _, response = signal.step(self.selected_dataset_data.tf.tf_object, T=t)
        elif expression == 'delta':
            delta = lambda t, eps: (1 / (np.sqrt(np.pi) *eps)) * np.exp(-(t/eps)**2) #para plotear la delta
            x = delta(t, (t[1] - t[0]))
            _, response = signal.impulse(self.selected_dataset_data.tf.tf_object, T=t)
        else:
            x = eval(expression)
            response = signal.lsim(self.selected_dataset_data.tf.tf_object , U = x , T = t)[1]
        
        self.selected_dataset_data.data[0][time_title] = t
        self.selected_dataset_data.data[0][title] = x
        self.selected_dataset_data.data[0][ans_title] = response

        self.selected_dataset_data.fields.append(time_title)
        self.selected_dataset_data.fields.append(title)
        self.selected_dataset_data.fields.append(ans_title)
        
        self.populateSelectedDatasetDetails(self.selected_dataset_widget, None)
        self.updateSelectedDataline()

    def buildFilterFromParams(self):
        pass
    
    def addFilter(self):
        pass
    
    def makeFilterTemplateSymmetric(self):
        pass

    def changeSelectedFilter(self):
        pass

    def updateFilterParametersAvailable(self):
        pass

    def condition_canvas(self, canvas, xlabel, ylabel, xscale='linear', yscale='linear', grid=True):
        canvas.ax.clear()
        canvas.ax.grid(grid, which="both", linestyle=':')
        canvas.ax.set_xlabel(xlabel)
        canvas.ax.set_ylabel(ylabel)
        canvas.ax.set_xscale(xscale)
        canvas.ax.set_yscale(yscale)
        canvas.ax.xaxis.label.set_size(self.plt_labelsize_sb.value())
        canvas.ax.yaxis.label.set_size(self.plt_labelsize_sb.value())
        for label in (canvas.ax.get_xticklabels() + canvas.ax.get_yticklabels()):
            label.set_fontsize(self.plt_ticksize_sb.value())

    def updateFilterPlots(self):
        pass
    
    def redrawFilterPlots(self, index):
        if(self.redrawFilterPlotsArr[index]):
            self.redrawFilterPlotsArr[index] = False
            self.filterPlots[index].canvas.draw_idle()
    def redrawStagePlots(self, index):
        if(self.redrawStagePlotsArr[index]):
            self.redrawStagePlotsArr[index] = False
            self.stagePlots[index].canvas.draw_idle()
        

    def updateFilterStages(self):
        pass

    def stage_sel_changed(self):
        pass

    def updateNormalizationCb(self, z, p):
        pass


    def updateSelectedPolesFromPlot(self, s):
        pass

    def updateSelectedZerosFromPlot(self, s):
        pass


    def addFilterStage(self):
        pass

    def swapStagesUpwards(self):
        pass

    def swapStagesDownwards(self):
        pass

    def orderStagesBySos(self):
        pass

    def removeFilterStage(self):
        pass

    def formatPoleAnnotation(self, sel):
        pass

    def formatPoleAnnotationW(self, sel):
        pass

    def formatZeroAnnotation(self, sel):
        pass

    def calcQ(self, singRe, singIm):
        return self.calcQ(singRe + singIm*1j)

    def calcQ(self, sing):
        if(isinstance(sing, (list, tuple, np.ndarray))):
            sing = sing[0] + sing[1]*1j
        if(sing.real == 0):
            return inf
        elif(sing.real > 0):
            return -1
        else:
            return np.abs(sing)/(- 2 * sing.real)

    def updateStagePlots(self):
        pass

    def clearCanvas(self, canvas):
        canvas.ax.clear()
        canvas.ax.grid(True, which="both", linestyle=':')

    def openCaseDialog(self):
        self.csd.open()
        self.csd.populate(ds = self.selected_dataset_data)
        # self.tfd.tf_title.setFocus()

    def resolveCSDialog(self):
        first_case = int(self.csd.case_first_cb.currentIndex())
        last_case = int(self.csd.case_last_cb.currentIndex())
        casenum = len(self.selected_dataset_data.data)
        dli = 0
        for x in range(self.dataset_list.count()):
            ds = self.dataset_list.item(x).data(Qt.UserRole)
            dli = dli + len(self.datalines[x])
            if(ds.origin == self.selected_dataset_data.origin):
                break
        color_iter = 0
        for case in range(first_case, min(last_case + 1, casenum)):
            dl = self.selected_dataset_data.create_dataline(case)
            qlwt = QListWidgetItem()
            dl.plots = self.csd.case_render_cb.currentIndex()
            dl.transform = self.csd.case_transform_cb.currentIndex()
            dl.xsource = self.csd.case_xdata_cb.currentText()
            dl.xscale = self.csd.case_xscale_sb.value()
            dl.xoffset = self.csd.case_xoffset_sb.value()
            dl.ysource = self.csd.case_ydata_cb.currentText()
            dl.yscale = self.csd.case_yscale_sb.value()
            dl.yoffset = self.csd.case_yoffset_sb.value()
            if(self.csd.case_randomcol_rb.isChecked()):
                dl.color = ["#"+''.join([random.choice('0123456789ABCDEF') for i in range(6)])][0]
            elif(self.csd.case_presetcol_rb.isChecked()):
                colorpalette_i = self.csd.case_palettecol_cb.currentIndex()
                colorpalette = self.csd.COLOR_LIST[colorpalette_i]
                dl.color = colorpalette[color_iter]
                color_iter += 1
                if(color_iter == len(colorpalette)):
                    color_iter = 0
            else:
                dl.color = self.csd.color
            dl.linestyle = self.csd.case_style_cb.currentText()
            dl.linewidth = self.csd.case_linewidth_sb.value()
            dl.markerstyle = self.csd.case_marker_cb.currentText()
            dl.markersize = self.csd.case_markersize_sb.value()
            if(self.csd.case_inforname_rb.isChecked()):
                dstitle = self.selected_dataset_data.title 
                dscases = self.selected_dataset_data.casenames
                if(case < len(dscases)):
                    dl.name = dstitle + ' ' + dscases[case]
            qlwt.setText(dl.name)
            dl.name = dl.name if self.csd.case_addlegend_cb.isChecked() else '_' + dl.name
            qlwt.setData(Qt.UserRole, dl)
            self.dataline_list.insertItem(dli, qlwt)
            self.datalines[self.dataset_list.currentRow()].append(dl)
        self.updatePlots()

    def populateSelectedDatasetDetails(self, listitemwidget, qlistwidget):
        if(not listitemwidget):
            self.setDatasetControlsStatus(False)
            self.ds_title_edit.setText('')
            self.ds_casenum_lb.setText('0')
            self.ds_info_lb.setText('')
            return
        self.setDatasetControlsStatus(True)
        self.ds_title_edit.setText(listitemwidget.text())
        self.selected_dataset_widget = listitemwidget
        self.selected_dataset_data = listitemwidget.data(Qt.UserRole)
        isTF = self.selected_dataset_data.type in ['TF', 'filter']
        self.ds_poleszeros_btn.setEnabled(isTF)
        self.resp_btn.setEnabled(isTF)
        self.ds_casenum_lb.setText(str(len(self.selected_dataset_data.data)))
        self.ds_caseadd_btn.setVisible(len(self.selected_dataset_data.data) > 1)
        self.ds_info_lb.setText(self.selected_dataset_data.miscinfo)

        #relleno las cajas del filtro
        if(self.selected_dataset_data.type == 'filter'):
            self.populateSelectedFilterDetails()

    
    def populateSelectedFilterDetails(self, index=-2):
        if(index == -2):
            for i, fds in enumerate(self.filters):
                if(fds.origin == self.selected_dataset_data.origin):
                    self.selfil_cb.blockSignals(True)
                    self.stages_selfil_cb.blockSignals(True)
                    self.selfil_cb.setCurrentIndex(i)
                    self.stages_selfil_cb.setCurrentIndex(i)
                    self.selfil_cb.blockSignals(False)
                    self.stages_selfil_cb.blockSignals(False)
                    break
        elif(index != -1):
            if(index == self.selfil_cb.currentIndex()):
                filtds = self.selfil_cb.currentData()
                self.stages_selfil_cb.blockSignals(True)
                self.stages_selfil_cb.setCurrentIndex(index)
                self.stages_selfil_cb.blockSignals(False)
            else:
                filtds = self.stages_selfil_cb.currentData()
                self.selfil_cb.blockSignals(True)
                self.selfil_cb.setCurrentIndex(index)
                self.selfil_cb.blockSignals(False)
            if(self.selected_dataset_data.origin != filtds.origin):
                for x in range(self.dataset_list.count()):
                    item = self.dataset_list.item(x)
                    ds = item.data(Qt.UserRole)
                    if(ds.origin == filtds.origin):
                        self.dataset_list.setCurrentRow(x)
                        self.populateSelectedDatasetDetails(item, None)
                        return
        else:
            return
        self.filtername_box.setText(self.selected_dataset_data.title)
        self.tipo_box.setCurrentIndex(self.selected_dataset_data.origin.filter_type)
        self.aprox_box.setCurrentIndex(self.selected_dataset_data.origin.approx_type)
        self.compareapprox_cb.setCurrentIndexes(self.selected_dataset_data.origin.helper_approx)
        self.comp_N_box.setValue(self.selected_dataset_data.origin.helper_N)
        self.gain_box.setValue(20*np.log10(self.selected_dataset_data.origin.gain))
        self.aa_box.setValue(self.selected_dataset_data.origin.aa_dB)
        self.ap_box.setValue(self.selected_dataset_data.origin.ap_dB)
        self.N_label.setText(str(self.selected_dataset_data.origin.N))
        self.N_min_box.setValue(self.selected_dataset_data.origin.N_min)
        self.N_max_box.setValue(self.selected_dataset_data.origin.N_max)
        Qs = [self.calcQ(p) for p in self.selected_dataset_data.origin.tf.getZP()[1]]
        if(len(Qs) > 0):
            self.max_Q_label.setText("{:.2f}".format(max(Qs)))
        self.drloss_label.setText("{:.2f} dB".format(self.selected_dataset_data.origin.getDynamicRangeLoss()))
        self.define_with_box.setCurrentIndex(self.selected_dataset_data.origin.define_with)
        if self.selected_dataset_data.origin.filter_type in [Filter.BAND_PASS, Filter.BAND_REJECT]:
            self.fp_box.setValue(0)
            self.fa_box.setValue(0)
            fa = []
            fp = []
            if(self.selected_dataset_data.origin.filter_type == Filter.BAND_PASS):
                fp = [w * self.SING_B_TO_F for w in self.selected_dataset_data.origin.wp]
                fa = [w * self.SING_B_TO_F for w in self.selected_dataset_data.origin.reqwa]
            else:
                fp = [w * self.SING_B_TO_F for w in self.selected_dataset_data.origin.reqwp]
                fa = [w * self.SING_B_TO_F for w in self.selected_dataset_data.origin.wa]
            self.fa_min_box.setValue(fa[0])
            self.fa_max_box.setValue(fa[1])
            self.fp_min_box.setValue(fp[0])
            self.fp_max_box.setValue(fp[1])
            self.bw_max_box.setValue(self.selected_dataset_data.origin.bw[1] * self.SING_B_TO_F)
            self.bw_min_box.setValue(self.selected_dataset_data.origin.bw[0] * self.SING_B_TO_F)
            self.f0_box.setValue(self.selected_dataset_data.origin.w0 * self.SING_B_TO_F)
        elif self.selected_dataset_data.origin.filter_type in [Filter.LOW_PASS, Filter.HIGH_PASS]:
            self.fp_box.setValue(self.selected_dataset_data.origin.wp * self.SING_B_TO_F)
            self.fa_box.setValue(self.selected_dataset_data.origin.wa * self.SING_B_TO_F)
            self.fa_min_box.setValue(0)
            self.fa_max_box.setValue(0)
            self.fp_min_box.setValue(0)
            self.fp_max_box.setValue(0)
        else:
            self.fp_box.setValue(0)
            self.fa_box.setValue(0)
            self.fa_min_box.setValue(0)
            self.fa_max_box.setValue(0)
            self.fp_min_box.setValue(0)
            self.fp_max_box.setValue(0)
        self.updateFilterStages()
        self.updateFilterPlots()
        self.updateFilterParametersAvailable()

    def updateSelectedDatasetName(self):
        new_title = self.ds_title_edit.text()
        self.selected_dataset_widget.setText(new_title)
        self.selected_dataset_data.title = new_title
        if(self.selected_dataset_data.type == 'filter'):
            self.selfil_cb.setItemText(self.selfil_cb.currentIndex(), new_title)
            self.stages_selfil_cb.setItemText(self.stages_selfil_cb.currentIndex(), new_title)
            self.filtername_box.setText(new_title)

    def populateSelectedDatalineDetails(self, listitemwidget, qlistwidget):
        if(not listitemwidget):
            self.setDatalineControlsStatus(False)
            self.dl_name_edit.setText('')
            return
        self.setDatalineControlsStatus(True)
        self.dl_xscale_sb.blockSignals(True)
        self.dl_yscale_sb.blockSignals(True)
        self.dl_xoffset_sb.blockSignals(True)
        self.dl_yoffset_sb.blockSignals(True)
        self.dl_linewidth_sb.blockSignals(True)
        self.dl_markersize_sb.blockSignals(True)
        self.dl_savgol_wlen.blockSignals(True)
        self.dl_savgol_ord.blockSignals(True)

        self.selected_dataline_widget = listitemwidget
        self.selected_dataline_data = listitemwidget.data(Qt.UserRole)
        self.dl_name_edit.setText(self.selected_dataline_widget.text())
        self.dl_render_cb.setCurrentIndex(self.selected_dataline_data.plots)
        
        self.dl_xdata_cb.clear()
        self.dl_ydata_cb.clear()
        self.dl_xdata_cb.addItems(self.selected_dataline_data.dataset.fields)
        self.dl_ydata_cb.addItems(self.selected_dataline_data.dataset.fields)
        
        self.dl_transform_cb.setCurrentIndex(self.selected_dataline_data.transform)
        self.dl_xdata_cb.setCurrentText(self.selected_dataline_data.xsource)
        self.dl_xscale_sb.setValue(self.selected_dataline_data.xscale)
        self.dl_xoffset_sb.setValue(self.selected_dataline_data.xoffset)
        self.dl_ydata_cb.setCurrentText(self.selected_dataline_data.ysource)
        self.dl_yscale_sb.setValue(self.selected_dataline_data.yscale)
        self.dl_yoffset_sb.setValue(self.selected_dataline_data.yoffset)
        self.dl_color_edit.setText(self.selected_dataline_data.color)
        self.dl_style_cb.setCurrentText(self.selected_dataline_data.linestyle)
        self.dl_linewidth_sb.setValue(self.selected_dataline_data.linewidth)
        self.dl_marker_cb.setCurrentText(self.selected_dataline_data.markerstyle)
        self.dl_markersize_sb.setValue(self.selected_dataline_data.markersize)
        self.dl_color_label.setStyleSheet(f'background-color: {self.selected_dataline_data.color}')
        self.dl_savgol_wlen.setValue(self.selected_dataline_data.savgolwindow)
        self.dl_savgol_ord.setValue(self.selected_dataline_data.savgolord)
        
        self.dl_xscale_sb.blockSignals(False)
        self.dl_yscale_sb.blockSignals(False)
        self.dl_xoffset_sb.blockSignals(False)
        self.dl_yoffset_sb.blockSignals(False)
        self.dl_linewidth_sb.blockSignals(False)
        self.dl_markersize_sb.blockSignals(False)
        self.dl_savgol_wlen.blockSignals(False)
        self.dl_savgol_ord.blockSignals(False)

    def updateSelectedDataline(self):
        self.saveFile(True)
        if(not self.selected_dataline_widget):
            return
        new_name = self.dl_name_edit.text()
        self.selected_dataline_widget.setText(new_name)
        self.selected_dataline_data.name = new_name
        self.selected_dataline_data.plots = self.dl_render_cb.currentIndex()
        self.selected_dataline_data.transform = self.dl_transform_cb.currentIndex()
        self.selected_dataline_data.xsource = self.dl_xdata_cb.currentText()
        self.selected_dataline_data.xscale = self.dl_xscale_sb.value()
        self.selected_dataline_data.xoffset = self.dl_xoffset_sb.value()
        self.selected_dataline_data.ysource = self.dl_ydata_cb.currentText()
        self.selected_dataline_data.yscale = self.dl_yscale_sb.value()
        self.selected_dataline_data.yoffset = self.dl_yoffset_sb.value()
        self.selected_dataline_data.color = self.dl_color_edit.text()
        self.selected_dataline_data.linestyle = self.dl_style_cb.currentText()
        self.selected_dataline_data.linewidth = self.dl_linewidth_sb.value()
        self.selected_dataline_data.markerstyle = self.dl_marker_cb.currentText()
        self.selected_dataline_data.markersize = self.dl_markersize_sb.value()
        self.selected_dataline_data.savgolwindow = self.dl_savgol_wlen.value()
        self.selected_dataline_data.savgolord = self.dl_savgol_ord.value()
        self.populateSelectedDatalineDetails(self.selected_dataline_widget, None)
        self.updatePlots()

    
    def openColorPicker(self):
        dialog = QColorDialog(self)
        dialog.setCurrentColor(Qt.red)
        dialog.setOption(QColorDialog.ShowAlphaChannel)
        dialog.open()
        dialog.currentColorChanged.connect(self.updateDatalineColor)

    def updateDatalineColor(self, color):
        self.dl_color_edit.setText(color.name())
        self.dl_color_label.setStyleSheet(f'background-color: {color.name()}')
        self.selected_dataline_data.color = color.name()
        self.updatePlots()

    def setDatasetControlsStatus(self, enabled=True):
        self.ds_title_edit.setEnabled(enabled)
        self.ds_addline_btn.setEnabled(enabled)
        self.ds_caseadd_btn.setEnabled(enabled)
        self.ds_remove_btn.setEnabled(enabled)

    def setDatalineControlsStatus(self, enabled=True):
        self.dataline_gb.setEnabled(enabled)

    def getPlotFromIndex(self, plotnum):
        x = plotnum
        tab = 0
        for tab_plots in self.plots_canvases:
            if(x - len(tab_plots) >= 0):
                tab += 1
                x -= len(tab_plots)
            else:
                break
        return self.plots_canvases[tab][x]

    def autoscalePlots(self):
        processedCanvas = [x.canvas for x in self.plots_canvases[self.tabbing_plots.currentIndex()]]
        for canvas in processedCanvas:
            canvas.ax.margins(self.plt_marginx.value(), self.plt_marginy.value())
            canvas.ax.relim()
            canvas.ax.autoscale()
        self.updatePlots()

    def changeLabelSize(self):
        # plt.rcParams.update({'font.size': self.plt_labelsize_sb.value()})
        self.updatePlots()

    def updatePlots(self):
        self.saveFile(True)
        processedCanvas = [x.canvas for x in self.plots_canvases[self.tabbing_plots.currentIndex()]]
        for canvas in processedCanvas:
            plotlist = []
            for artist in canvas.ax.lines + canvas.ax.collections:
                artist.remove()
            for x in range(self.dataset_list.count()):
                ds = self.dataset_list.item(x).data(Qt.UserRole)
                for dl in ds.datalines:
                    dl_canvas = self.getPlotFromIndex(dl.plots).canvas
                    if(dl_canvas == canvas):
                        
                        for label in (canvas.ax.get_xticklabels() + canvas.ax.get_yticklabels()):
                            label.set_fontsize(self.plt_ticksize_sb.value())
                        canvas.ax.xaxis.label.set_size(self.plt_labelsize_sb.value())
                        canvas.ax.yaxis.label.set_size(self.plt_labelsize_sb.value())
                        canvas.ax.title.set_size(self.plt_titlesize_sb.value())

                        x, y = ds.get_datapoints(dl.xsource, dl.ysource, dl.casenum)

                        if(dl.transform == 1):
                            y = np.abs(y)
                        elif(dl.transform == 2):
                            y = np.angle(y, deg=True)
                        elif(dl.transform == 3):
                            y = np.unwrap(np.angle(y, deg=True), period=360)
                        elif(dl.transform == 4):
                            y = 20 * np.log10(y)
                        elif(dl.transform == 5):
                            y = 20 * np.log10(np.abs(y))
                        elif(dl.transform == 6):
                            y = np.unwrap(y, period=360)
                        else:
                            y = np.real(y)

                        if(dl.transform in [2,3,6]):
                            canvas.ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins='auto', steps=[1.8,2.25,4.5,9]))
                        else:
                            canvas.ax.yaxis.set_major_locator(ticker.AutoLocator())

                        try:
                            savgolw = int(dl.savgolwindow)
                            if(savgolw <= len(x)):
                                savgolo = int(dl.savgolord)
                                y = y if savgolw <= savgolo else savgol_filter(y, savgolw, savgolo)
                        except ValueError:
                            pass

                        try:
                            line, = canvas.ax.plot(
                                x * dl.xscale + dl.xoffset,
                                y * dl.yscale + dl.yoffset,
                                linestyle = LINE_STYLES[dl.linestyle],
                                linewidth = dl.linewidth,
                                marker = MARKER_STYLES[dl.markerstyle],
                                markersize = dl.markersize,
                                color = dl.color,
                                label = dl.name,
                            )
                            if(dl.name != '' and dl.name[0] != '_'):
                                plotlist.append(line)
                        except ValueError:
                            self.statusbar.showMessage('Wrong data source matching', 2000)
            if(self.plt_legendpos.currentText() == 'None'):
                if(canvas.ax.get_legend()):
                    canvas.ax.get_legend().remove()
            else:
                canvas.ax.legend(handles=plotlist, fontsize=self.plt_legendsize_sb.value(), loc=self.plt_legendpos.currentIndex())
            if(self.plt_grid.isChecked()):
                canvas.ax.grid(True, which="both", linestyle=':')
            else:
                canvas.ax.grid(False, which="both")
                

            try:
                canvas.draw_idle()
            except ValueError:
                pass

    def showZPWindow(self):
        zeros = self.selected_dataset_data.zeros[0]
        poles = self.selected_dataset_data.poles[0]
        self.zpWindow = ZPWindow(zeros, poles, self.selected_dataset_data.title)
        self.zpWindow.show()

    def newFile(self):
        self.droppedFiles = []
        self.datasets = []
        self.datalines = []
        self.selected_dataset_widget = {}
        self.selected_dataline_widget = {}
        self.selected_dataset_data = {}
        self.selected_dataline_data = {}
        self.zpWindow = type(ZPWindow, (), {})()
        self.updateAll()
    
    def saveFile(self, noprompt=False):
        if(noprompt):
            filename = 'temp.fto'
        else:
            filename, _ = QFileDialog.getSaveFileName(self,"Save File", "","Filter tool file (*.fto)")
        if(not filename): return
        with open(filename, 'wb') as f:
            flat_plots_canvas = [item.canvas for sublist in self.plots_canvases for item in sublist]
            plots_data = []
            for canv in flat_plots_canvas:
                plots_data.append(canv.get_properties())
            general_config = {
                'labelsize_sb': self.plt_labelsize_sb.value(),
                'legendsize_sb': self.plt_legendsize_sb.value(),
                'ticksize_sb': self.plt_ticksize_sb.value(),
                'titlesize_sb': self.plt_titlesize_sb.value(),
                'legendpos': self.plt_legendpos.currentIndex(),
                'grid': self.plt_grid.isChecked(),
                'marginx': self.plt_marginx.value(),
                'marginy': self.plt_marginy.value()      
            }
            d = [self.datasets, self.datalines, plots_data, general_config]
            pickle.dump(d, f, pickle.HIGHEST_PROTOCOL)

    def loadFile(self):
        filename, _ = QFileDialog.getOpenFileName(self,"Select files", "","Filter tool file (*.fto)")
        if(not filename): return
        with open(filename, 'rb') as f:
            f.seek(0)
            self.datasets, self.datalines, plotdata, general_config = pickle.load(f)            
            self.plt_labelsize_sb.setValue(general_config['labelsize_sb'])
            self.plt_legendsize_sb.setValue(general_config['legendsize_sb'])
            self.plt_ticksize_sb.setValue(general_config['ticksize_sb'])
            self.plt_titlesize_sb.setValue(general_config['titlesize_sb'])
            self.plt_legendpos.setCurrentIndex(general_config['legendpos'])
            self.plt_grid.setChecked(general_config['grid'])
            self.plt_marginx.setValue(general_config['marginx'])
            self.plt_marginy.setValue(general_config['marginy'])  
            acc = 0   
            for s in self.plots_canvases:
                for p in s:
                    p.canvas.restore_properties(plotdata[acc])
                    acc += 1
            for ds in self.datasets:
                qlwt = QListWidgetItem()
                qlwt.setData(Qt.UserRole, ds)
                qlwt.setText(ds.title)
                self.dataset_list.addItem(qlwt)
                for dl in ds.datalines:
                    qlwt = QListWidgetItem()
                    qlwt.setData(Qt.UserRole, dl)
                    qlwt.setText(dl.name)
                    self.dataline_list.addItem(qlwt)
                if(ds.type == 'filter'):
                    self.filters.append(ds)
                    self.selfil_cb.blockSignals(True)
                    self.stages_selfil_cb.blockSignals(True)
                    self.selfil_cb.addItem(ds.title, ds)
                    self.stages_selfil_cb.addItem(ds.title, ds)
                    self.selfil_cb.blockSignals(False)
                    self.stages_selfil_cb.blockSignals(False)

            self.dataset_list.setCurrentRow(self.dataset_list.count() - 1)
            self.updateAll()
    
    def updateAll(self):
        self.updatePlots()
        self.updateSelectedDataline()
        self.updateFilterParametersAvailable()
    
    def getRelevantFrequencies(self, zeros, poles):
        singularitiesNorm = np.append(np.abs(zeros), np.abs(poles))
        singularitiesNormWithoutZeros = [s for s in singularitiesNorm if s != 0]
        if(len(singularitiesNormWithoutZeros) == 0):
            return (1, 1)
        return (np.min(singularitiesNormWithoutZeros), np.max(singularitiesNormWithoutZeros))
    
    def getMultiplierAndPrefix(self, val):
        multiplier = 1
        prefix = ''
        if(val < 1e-7):
            multiplier = 1e9
            prefix = 'n'
        elif(val < 1e-4):
            multiplier = 1e-6
            prefix = 'μ'
        elif(val < 1e-1):
            multiplier = 1e-3
            prefix = 'm'
        elif(val < 1e2):
            multiplier = 1
            prefix = ''
        elif(val < 1e5):
            multiplier = 1e3
            prefix = 'k'
        elif(val < 1e8):
            multiplier = 1e6
            prefix = 'M'
        elif(val > 1e11):
            multiplier = 1e9
            prefix = 'G'
        return (multiplier, prefix)

    def updatePossibleImplementations(self):
        if(not self.stages_list.currentItem()):
            return
        stage_tf = self.stages_list.currentItem().data(Qt.UserRole)
        stagetype, text = stage_tf.origin.getSOFilterType()
        arr = [False] * CellCalculator.IMPL_COUNT

        if(stagetype in [TF.LP1, TF.HP1]):
            arr[CellCalculator.PASSIVERC] = True
            arr[CellCalculator.PASSIVERLC] = False
            arr[CellCalculator.INTEGDERIV] = True
            arr[CellCalculator.SALLENKEY] = False
            arr[CellCalculator.RAUCH] = False
            arr[CellCalculator.DOUBLET] = False
            arr[CellCalculator.KHN] = False
            arr[CellCalculator.SEDRA] = False
            arr[CellCalculator.ACKERBERG] = False
            arr[CellCalculator.TOWTHOMAS] = False
            arr[CellCalculator.FLEISCHERTOW] = False
        else:
            arr[CellCalculator.INTEGDERIV] = False
            arr[CellCalculator.FLEISCHERTOW] = True
            if(stagetype in [TF.LP2, TF.HP2]):
                arr[CellCalculator.PASSIVERC] = True
                arr[CellCalculator.PASSIVERLC] = True
                arr[CellCalculator.SALLENKEY] = True
                arr[CellCalculator.RAUCH] = True
                arr[CellCalculator.DOUBLET] = True
                arr[CellCalculator.SEDRA] = True
                arr[CellCalculator.ACKERBERG] = stagetype == TF.LP2
                arr[CellCalculator.KHN] = True
                arr[CellCalculator.TOWTHOMAS] = stagetype == TF.LP2
            elif(stagetype == TF.BP):
                arr[CellCalculator.PASSIVERC] = stage_tf.gain <= 1 and stage_tf.getPoleQ() <= 1/3 # hay que ver bien el Q!!!
                arr[CellCalculator.PASSIVERLC] = True
                arr[CellCalculator.SALLENKEY] = False
                arr[CellCalculator.RAUCH] = True
                arr[CellCalculator.DOUBLET] = False
                arr[CellCalculator.SEDRA] = False
                arr[CellCalculator.ACKERBERG] = True
                arr[CellCalculator.KHN] = True
                arr[CellCalculator.TOWTHOMAS] = True
            elif(stagetype in [TF.BR, TF.HPN, TF.LPN]):
                arr[CellCalculator.PASSIVERC] = stage_tf.gain <= 1 and stage_tf.getPoleQ() < 1/3 # hay que ver bien el Q!!!
                arr[CellCalculator.PASSIVERLC] = True
                arr[CellCalculator.SALLENKEY] = False
                arr[CellCalculator.RAUCH] = False
                arr[CellCalculator.DOUBLET] = False
                arr[CellCalculator.SEDRA] = False
                arr[CellCalculator.ACKERBERG] = False
                arr[CellCalculator.KHN] = False # Por ahora!
                arr[CellCalculator.TOWTHOMAS] = False
        for i in range(CellCalculator.IMPL_COUNT):
            self.si_type_cb.model().item(i).setEnabled(arr[i])
        # f = accumulated_ds.data[0]['f']
        # g = accumulated_ds.data[0]['g']
        # ph = accumulated_ds.data[0]['ph']
        # z, p = accumulated_ds.origin.getZP(self.use_hz)

        # gline, = smagcanvas.ax.plot(f, g)
        # phline, = sphasecanvas.ax.plot(f, ph)

        # (min, max) = self.getRelevantFrequencies(z, p)
        # self.splot_pz.canvas.ax.axis('equal')
        # self.splot_pz.canvas.ax.axhline(0, color="black", alpha=0.1)
        # self.splot_pz.canvas.ax.axvline(0, color="black", alpha=0.1)
        # self.splot_pz.canvas.ax.set_xlim(left=-max*PZ_LIM_SCALING, right=max*PZ_LIM_SCALING)
        # self.splot_pz.canvas.ax.set_ylim(bottom=-max*PZ_LIM_SCALING, top=max*PZ_LIM_SCALING)

        # zeroes_f = self.splot_pz.canvas.ax.scatter(z.real, z.imag, marker='o')
        # poles_f = self.splot_pz.canvas.ax.scatter(p.real, p.imag, marker='x')

        # cursor(zeroes_f).connect("add", self.formatZeroAnnotation)
        # cursor(poles_f).connect("add", self.formatPoleAnnotation)

    def openImplementationDialog(self):
        sel_impl = self.si_type_cb.currentIndex()
        stage = self.stages_list.currentItem().data(Qt.UserRole).origin
        if(not stage): return
        if(sel_impl == CellCalculator.PASSIVERC):
            pass
        elif(sel_impl == CellCalculator.PASSIVERLC):
            pass
        elif(sel_impl == CellCalculator.SALLENKEY):
            pass
        elif(sel_impl == CellCalculator.RAUCH):
            pass
        elif(sel_impl == CellCalculator.DOUBLET):
            pass
        elif(sel_impl == CellCalculator.SEDRA):
            pass
        elif(sel_impl == CellCalculator.KHN):
            pass
        elif(sel_impl == CellCalculator.TOWTHOMAS):
            pass
        elif(sel_impl == CellCalculator.ACKERBERG):
            pass
        elif(sel_impl == CellCalculator.FLEISCHERTOW):
            self.ftd.open()
            self.ftd.populate(stage)
    
    def copyFilterHhuman(self):
        if(self.selected_dataset_data.type == 'filter'):
            clipboard = QCoreApplication.instance().clipboard()
            clipboard.setText(self.selected_dataset_data.origin.tf.buildSymbolicText())
    
    def copyFilterHlatex(self):
        if(self.selected_dataset_data.type == 'filter'):
            clipboard = QCoreApplication.instance().clipboard()
            s = self.selected_dataset_data.origin.tf.buildSymbolicText()
            clipboard.setText(self.selected_dataset_data.origin.tf.getLatex(s))

    def copyStageHhuman(self):
        if(self.stages_list.currentItem()):
            clipboard = QCoreApplication.instance().clipboard()
            tf = self.stages_list.currentItem().data(Qt.UserRole).origin
            clipboard.setText(tf.buildSymbolicText())

    def copyStageHlatex(self):
        if(self.stages_list.currentItem()):
            clipboard = QCoreApplication.instance().clipboard()
            tf = self.stages_list.currentItem().data(Qt.UserRole).origin
            s = tf.buildSymbolicText()
            clipboard.setText(tf.getLatex(s))
