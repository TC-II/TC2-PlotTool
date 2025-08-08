from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel, 
                             QVBoxLayout, QWidget, QToolBar, QAction, QActionGroup)
from PyQt5.QtCore import Qt

import numpy
from src.widgets.mplwidget import MplWidget

class ZPWindow(QWidget):
    def __init__(self, zeros = [], poles = [], title = '', *args, **kwargs):
        super(ZPWindow, self).__init__()
        # Store original data (assuming it's in radians)
        self.zeros_rad = numpy.array(zeros) if len(zeros) > 0 else numpy.array([])
        self.poles_rad = numpy.array(poles) if len(poles) > 0 else numpy.array([])
        self.title = title
        self.current_unit = 'radians'  # Default unit
        
        self.setup_ui()
        self.draw_pzmap()

    def setup_ui(self):
        self.layout = QVBoxLayout()
        
        # Create toolbar
        self.toolbar = QToolBar()
        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextOnly)
        
        # Create frequency units menu
        freq_units_action = QAction('Frequency Units', self)
        freq_units_menu = self.toolbar.addAction(freq_units_action)
        
        # Create action group for mutual exclusion
        self.freq_unit_group = QActionGroup(self)
        
        # Radians option
        self.radians_action = QAction('Radians (rad/s)', self, checkable=True)
        self.radians_action.setChecked(True)  # Default selection
        self.radians_action.triggered.connect(lambda: self.change_frequency_unit('radians'))
        self.freq_unit_group.addAction(self.radians_action)
        
        # Hertz option
        self.hertz_action = QAction('Hertz (Hz)', self, checkable=True)
        self.hertz_action.triggered.connect(lambda: self.change_frequency_unit('hertz'))
        self.freq_unit_group.addAction(self.hertz_action)
        
        # Add actions to toolbar with separators for better organization
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.radians_action)
        self.toolbar.addAction(self.hertz_action)
        self.toolbar.addSeparator()
        
        # Create plot widget
        self.zp_plot = MplWidget()
        self.zp_plot.focusWidget()
        
        # Add widgets to layout
        self.layout.addWidget(self.toolbar)
        self.layout.addWidget(self.zp_plot)
        self.setLayout(self.layout)

        self.setWindowTitle(f'Poles and zeros of function {self.title}')

    def change_frequency_unit(self, unit):
        """Change the frequency unit and redraw the plot"""
        if self.current_unit != unit:
            self.current_unit = unit
            self.draw_pzmap()

    def get_current_data(self):
        """Get zeros and poles in the current unit"""
        if self.current_unit == 'hertz':
            # Convert from radians to hertz: Hz = rad/s / (2π)
            zeros_current = self.zeros_rad / (2 * numpy.pi) if len(self.zeros_rad) > 0 else self.zeros_rad
            poles_current = self.poles_rad / (2 * numpy.pi) if len(self.poles_rad) > 0 else self.poles_rad
        else:
            # Use radians (original data)
            zeros_current = self.zeros_rad
            poles_current = self.poles_rad
        
        return zeros_current, poles_current

    def get_unit_labels(self):
        """Get appropriate labels for current unit"""
        if self.current_unit == 'hertz':
            return '1/s', 'Hz'
        else:
            return 'rad/s', 'rad/s'

    def draw_pzmap(self):
        zeros, poles = self.get_current_data()
        unit_label_real, unit_label_imag = self.get_unit_labels()
        
        canvas = self.zp_plot.canvas
        canvas.ax.clear()
        canvas.ax.axhline(0, color="black", alpha=0.1)
        canvas.ax.axvline(0, color="black", alpha=0.1)
        
        (min_freq, max_freq) = self.getRelevantFrequencies(zeros, poles)
        (multiplier, prefix) = self.getMultiplierAndPrefix(max_freq)
        
        if len(zeros) > 0:
            canvas.ax.scatter(zeros.real/multiplier, zeros.imag/multiplier, 
                            marker='o', s=50, c='blue', label='Zeros')
        if len(poles) > 0:
            canvas.ax.scatter(poles.real/multiplier, poles.imag/multiplier, 
                            marker='x', s=50, c='red', linewidth=2, label='Poles')
        
        # Set labels based on current unit
        if self.current_unit == 'hertz':
            canvas.ax.set_xlabel(f'$\sigma$ (${prefix}{unit_label_real}$)')
            canvas.ax.set_ylabel(f'$jf$ (${prefix}{unit_label_imag}$)')
        else:
            canvas.ax.set_xlabel(f'$\sigma$ (${prefix}{unit_label_real}$)')
            canvas.ax.set_ylabel(f'$j\omega$ (${prefix}{unit_label_imag}$)')
        
        canvas.ax.set_xlim(left=-max_freq*1.2/multiplier, right=max_freq*1.2/multiplier)
        canvas.ax.set_ylim(bottom=-max_freq*1.2/multiplier, top=max_freq*1.2/multiplier)
        canvas.ax.set_aspect('equal', adjustable='box')

        canvas.ax.grid(True, which="both", linestyle=':')
        
        # Add legend if there are poles or zeros
        if len(zeros) > 0 or len(poles) > 0:
            canvas.ax.legend()
        
        canvas.draw()

    def getRelevantFrequencies(self, zeros, poles):
        all_singularities = numpy.array([])
        if len(zeros) > 0:
            all_singularities = numpy.append(all_singularities, numpy.abs(zeros))
        if len(poles) > 0:
            all_singularities = numpy.append(all_singularities, numpy.abs(poles))
        
        singularitiesNormWithoutZeros = all_singularities[all_singularities != 0]
        
        if len(singularitiesNormWithoutZeros) == 0:
            return (1, 1)
        return (numpy.min(singularitiesNormWithoutZeros), numpy.max(singularitiesNormWithoutZeros))
    
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