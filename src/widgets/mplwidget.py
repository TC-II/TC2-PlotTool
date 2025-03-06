# Imports
from PyQt5 import QtWidgets
import matplotlib
matplotlib.use('Agg')

from matplotlib.figure import Figure
# from matplotlib.widgets import Cursor
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as Canvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

# Ensure using PyQt5 backend
# matplotlib.use('pgf')
matplotlib.rcParams.update({
    "pgf.texsystem": "pdflatex",
    'font.family': 'serif',
    # 'text.usetex': True,
    'pgf.rcfonts': False,
    'legend.fancybox': False,
    'legend.edgecolor': 'black',
    'savefig.format': 'pdf',
    'path.simplify_threshold': 0.2
})

class CustomNavigationToolbar(NavigationToolbar):
    toolitems = [t for t in NavigationToolbar.toolitems if
                 t[0] in ('Home', 'Pan', 'Zoom', 'Save')]

# Matplotlib canvas class to create figure
class MplCanvas(Canvas):
    def __init__(self):
        self.fig = Figure()
        self.fig.set_tight_layout(True)
        self.ax = self.fig.add_subplot(111)
        Canvas.__init__(self, self.fig)
        Canvas.setSizePolicy(self, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        Canvas.updateGeometry(self)
        # self.cursor = Cursor(self.ax, useblit=True, color='red', linewidth=0.3, linestyle='--')
    
    def get_properties(self):
        return {
            "xlabel": self.ax.get_xlabel(),
            "ylabel": self.ax.get_ylabel(),
            "title": self.ax.get_title(),
            "xlim": self.ax.get_xlim(),
            "ylim": self.ax.get_ylim(),
            "xscale": self.ax.get_xscale(),
            "yscale": self.ax.get_yscale()
        }

    def restore_properties(self, props):
        self.ax.set_xlabel(props['xlabel'])
        self.ax.set_ylabel(props['ylabel'])
        self.ax.set_title(props['title'])
        self.ax.set_xlim(props['xlim'])
        self.ax.set_ylim(props['ylim'])
        self.ax.set_xscale(props['xscale'])
        self.ax.set_yscale(props['yscale'])
        
# Matplotlib widget
class MplWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)   # Inherit from QWidget
        self.canvas = MplCanvas()                  # Create canvas object
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.vbl = QtWidgets.QVBoxLayout()         # Set box for plotting
        self.vbl.addWidget(self.toolbar)
        self.vbl.addWidget(self.canvas)
        self.setLayout(self.vbl)