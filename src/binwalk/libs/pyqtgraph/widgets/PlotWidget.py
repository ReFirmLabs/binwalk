# -*- coding: utf-8 -*-
"""
PlotWidget.py -  Convenience class--GraphicsView widget displaying a single PlotItem
Copyright 2010  Luke Campagnola
Distributed under MIT/X11 license. See license.txt for more infomation.
"""

from pyqtgraph.Qt import QtCore, QtGui
from .GraphicsView import *
from pyqtgraph.graphicsItems.PlotItem import *

__all__ = ['PlotWidget']
class PlotWidget(GraphicsView):
    
    #sigRangeChanged = QtCore.Signal(object, object)  ## already defined in GraphicsView
    
    """
    :class:`GraphicsView <pyqtgraph.GraphicsView>` widget with a single 
    :class:`PlotItem <pyqtgraph.PlotItem>` inside.
    
    The following methods are wrapped directly from PlotItem: 
    :func:`addItem <pyqtgraph.PlotItem.addItem>`, 
    :func:`removeItem <pyqtgraph.PlotItem.removeItem>`, 
    :func:`clear <pyqtgraph.PlotItem.clear>`, 
    :func:`setXRange <pyqtgraph.ViewBox.setXRange>`,
    :func:`setYRange <pyqtgraph.ViewBox.setYRange>`,
    :func:`setRange <pyqtgraph.ViewBox.setRange>`,
    :func:`autoRange <pyqtgraph.ViewBox.autoRange>`,
    :func:`setXLink <pyqtgraph.ViewBox.setXLink>`,
    :func:`setYLink <pyqtgraph.ViewBox.setYLink>`,
    :func:`viewRect <pyqtgraph.ViewBox.viewRect>`,
    :func:`setMouseEnabled <pyqtgraph.ViewBox.setMouseEnabled>`,
    :func:`enableAutoRange <pyqtgraph.ViewBox.enableAutoRange>`,
    :func:`disableAutoRange <pyqtgraph.ViewBox.disableAutoRange>`,
    :func:`setAspectLocked <pyqtgraph.ViewBox.setAspectLocked>`,
    :func:`register <pyqtgraph.ViewBox.register>`,
    :func:`unregister <pyqtgraph.ViewBox.unregister>`
    
    
    For all 
    other methods, use :func:`getPlotItem <pyqtgraph.PlotWidget.getPlotItem>`.
    """
    def __init__(self, parent=None, background='default', **kargs):
        """When initializing PlotWidget, *parent* and *background* are passed to 
        :func:`GraphicsWidget.__init__() <pyqtgraph.GraphicsWidget.__init__>`
        and all others are passed
        to :func:`PlotItem.__init__() <pyqtgraph.PlotItem.__init__>`."""
        GraphicsView.__init__(self, parent, background=background)
        self.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        self.enableMouse(False)
        self.plotItem = PlotItem(**kargs)
        self.setCentralItem(self.plotItem)
        ## Explicitly wrap methods from plotItem
        ## NOTE: If you change this list, update the documentation above as well.
        for m in ['addItem', 'removeItem', 'autoRange', 'clear', 'setXRange', 'setYRange', 'setRange', 'setAspectLocked', 'setMouseEnabled', 'setXLink', 'setYLink', 'enableAutoRange', 'disableAutoRange', 'register', 'unregister', 'viewRect']:
            setattr(self, m, getattr(self.plotItem, m))
        #QtCore.QObject.connect(self.plotItem, QtCore.SIGNAL('viewChanged'), self.viewChanged)
        self.plotItem.sigRangeChanged.connect(self.viewRangeChanged)
    
    def close(self):
        self.plotItem.close()
        self.plotItem = None
        #self.scene().clear()
        #self.mPlotItem.close()
        self.setParent(None)
        GraphicsView.close(self)

    def __getattr__(self, attr):  ## implicitly wrap methods from plotItem
        if hasattr(self.plotItem, attr):
            m = getattr(self.plotItem, attr)
            if hasattr(m, '__call__'):
                return m
        raise NameError(attr)
    
    def viewRangeChanged(self, view, range):
        #self.emit(QtCore.SIGNAL('viewChanged'), *args)
        self.sigRangeChanged.emit(self, range)

    def widgetGroupInterface(self):
        return (None, PlotWidget.saveState, PlotWidget.restoreState)

    def saveState(self):
        return self.plotItem.saveState()
        
    def restoreState(self, state):
        return self.plotItem.restoreState(state)
        
    def getPlotItem(self):
        """Return the PlotItem contained within."""
        return self.plotItem
        
        
        