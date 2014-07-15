import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
from .Exporter import Exporter


__all__ = ['MatplotlibExporter']
    
    
class MatplotlibExporter(Exporter):
    Name = "Matplotlib Window"
    windows = []
    def __init__(self, item):
        Exporter.__init__(self, item)
        
    def parameters(self):
        return None
    
    def export(self, fileName=None):
        
        if isinstance(self.item, pg.PlotItem):
            mpw = MatplotlibWindow()
            MatplotlibExporter.windows.append(mpw)
            fig = mpw.getFigure()
            
            ax = fig.add_subplot(111)
            ax.clear()
            #ax.grid(True)
            
            for item in self.item.curves:
                x, y = item.getData()
                opts = item.opts
                pen = pg.mkPen(opts['pen'])
                if pen.style() == QtCore.Qt.NoPen:
                    linestyle = ''
                else:
                    linestyle = '-'
                color = tuple([c/255. for c in pg.colorTuple(pen.color())])
                symbol = opts['symbol']
                if symbol == 't':
                    symbol = '^'
                symbolPen = pg.mkPen(opts['symbolPen'])
                symbolBrush = pg.mkBrush(opts['symbolBrush'])
                markeredgecolor = tuple([c/255. for c in pg.colorTuple(symbolPen.color())])
                markerfacecolor = tuple([c/255. for c in pg.colorTuple(symbolBrush.color())])
                
                if opts['fillLevel'] is not None and opts['fillBrush'] is not None:
                    fillBrush = pg.mkBrush(opts['fillBrush'])
                    fillcolor = tuple([c/255. for c in pg.colorTuple(fillBrush.color())])
                    ax.fill_between(x=x, y1=y, y2=opts['fillLevel'], facecolor=fillcolor)
                
                ax.plot(x, y, marker=symbol, color=color, linewidth=pen.width(), linestyle=linestyle, markeredgecolor=markeredgecolor, markerfacecolor=markerfacecolor)
                
                xr, yr = self.item.viewRange()
                ax.set_xbound(*xr)
                ax.set_ybound(*yr)
            mpw.draw()
        else:
            raise Exception("Matplotlib export currently only works with plot items")
                
        

class MatplotlibWindow(QtGui.QMainWindow):
    def __init__(self):
        import pyqtgraph.widgets.MatplotlibWidget
        QtGui.QMainWindow.__init__(self)
        self.mpl = pyqtgraph.widgets.MatplotlibWidget.MatplotlibWidget()
        self.setCentralWidget(self.mpl)
        self.show()
        
    def __getattr__(self, attr):
        return getattr(self.mpl, attr)
        
    def closeEvent(self, ev):
        MatplotlibExporter.windows.remove(self)
