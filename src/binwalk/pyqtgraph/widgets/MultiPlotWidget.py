# -*- coding: utf-8 -*-
"""
MultiPlotWidget.py -  Convenience class--GraphicsView widget displaying a MultiPlotItem
Copyright 2010  Luke Campagnola
Distributed under MIT/X11 license. See license.txt for more infomation.
"""

from .GraphicsView import GraphicsView
import pyqtgraph.graphicsItems.MultiPlotItem as MultiPlotItem

__all__ = ['MultiPlotWidget']
class MultiPlotWidget(GraphicsView):
    """Widget implementing a graphicsView with a single PlotItem inside."""
    def __init__(self, parent=None):
        GraphicsView.__init__(self, parent)
        self.enableMouse(False)
        self.mPlotItem = MultiPlotItem.MultiPlotItem()
        self.setCentralItem(self.mPlotItem)
        ## Explicitly wrap methods from mPlotItem
        #for m in ['setData']:
            #setattr(self, m, getattr(self.mPlotItem, m))
                
    def __getattr__(self, attr):  ## implicitly wrap methods from plotItem
        if hasattr(self.mPlotItem, attr):
            m = getattr(self.mPlotItem, attr)
            if hasattr(m, '__call__'):
                return m
        raise NameError(attr)

    def widgetGroupInterface(self):
        return (None, MultiPlotWidget.saveState, MultiPlotWidget.restoreState)

    def saveState(self):
        return {}
        #return self.plotItem.saveState()
        
    def restoreState(self, state):
        pass
        #return self.plotItem.restoreState(state)

    def close(self):
        self.mPlotItem.close()
        self.mPlotItem = None
        self.setParent(None)
        GraphicsView.close(self)