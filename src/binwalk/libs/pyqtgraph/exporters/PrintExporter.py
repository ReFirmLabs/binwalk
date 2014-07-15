from .Exporter import Exporter
from pyqtgraph.parametertree import Parameter
from pyqtgraph.Qt import QtGui, QtCore, QtSvg
import re

__all__ = ['PrintExporter']  
#__all__ = []   ## Printer is disabled for now--does not work very well.

class PrintExporter(Exporter):
    Name = "Printer"
    def __init__(self, item):
        Exporter.__init__(self, item)
        tr = self.getTargetRect()
        self.params = Parameter(name='params', type='group', children=[
            {'name': 'width', 'type': 'float', 'value': 0.1, 'limits': (0, None), 'suffix': 'm', 'siPrefix': True},
            {'name': 'height', 'type': 'float', 'value': (0.1 * tr.height()) / tr.width(), 'limits': (0, None), 'suffix': 'm', 'siPrefix': True},
        ])
        self.params.param('width').sigValueChanged.connect(self.widthChanged)
        self.params.param('height').sigValueChanged.connect(self.heightChanged)

    def widthChanged(self):
        sr = self.getSourceRect()
        ar = sr.height() / sr.width()
        self.params.param('height').setValue(self.params['width'] * ar, blockSignal=self.heightChanged)
        
    def heightChanged(self):
        sr = self.getSourceRect()
        ar = sr.width() / sr.height()
        self.params.param('width').setValue(self.params['height'] * ar, blockSignal=self.widthChanged)
        
    def parameters(self):
        return self.params
    
    def export(self, fileName=None):
        printer = QtGui.QPrinter(QtGui.QPrinter.HighResolution)
        dialog = QtGui.QPrintDialog(printer)
        dialog.setWindowTitle("Print Document")
        if dialog.exec_() != QtGui.QDialog.Accepted:
            return;
            
        #dpi = QtGui.QDesktopWidget().physicalDpiX()
        
        #self.svg.setSize(QtCore.QSize(100,100))
        #self.svg.setResolution(600)
        #res = printer.resolution()
        sr = self.getSourceRect()
        #res = sr.width() * .4 / (self.params['width'] * 100 / 2.54)
        res = QtGui.QDesktopWidget().physicalDpiX()
        printer.setResolution(res)
        rect = printer.pageRect()
        center = rect.center()
        h = self.params['height'] * res * 100. / 2.54
        w = self.params['width'] * res * 100. / 2.54
        x = center.x() - w/2.
        y = center.y() - h/2.
        
        targetRect = QtCore.QRect(x, y, w, h)
        sourceRect = self.getSourceRect()
        painter = QtGui.QPainter(printer)
        try:
            self.setExportMode(True, {'painter': painter})
            self.getScene().render(painter, QtCore.QRectF(targetRect), QtCore.QRectF(sourceRect))
        finally:
            self.setExportMode(False)
        painter.end()
