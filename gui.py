import pyqtgraph as pqg
from pyqtgraph.Qt import QtWidgets

class GUI:
    def __init__(self):
        self._app = QtWidgets.QApplication([])  # Initialize the application
        pqg.setConfigOption('background', 'w')
        self._window = pqg.GraphicsLayoutWidget(title="2D scatter plot")
        self._scatter_plot = self._window.addPlot()
        self._scatter_plot.setXRange(-0.5, 0.5)
        self._scatter_plot.setYRange(0, 1.5)
        self._scatter_plot.setLabel('left', text='Y position (m)')
        self._scatter_plot.setLabel('bottom', text='X position (m)')
        self._scatter_data = self._scatter_plot.plot([], [], pen=None, symbol='o')

    def show(self):
        self._window.show()

    def close(self):
        self._window.close()

    def setData(self, x, y):
        self._scatter_data.setData(x, y)
        QtWidgets.QApplication.processEvents()
