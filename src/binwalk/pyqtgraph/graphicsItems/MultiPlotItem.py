# -*- coding: utf-8 -*-
"""
MultiPlotItem.py -  Graphics item used for displaying an array of PlotItems
Copyright 2010  Luke Campagnola
Distributed under MIT/X11 license. See license.txt for more infomation.
"""

from numpy import ndarray
from . import GraphicsLayout

try:
    from metaarray import *
    HAVE_METAARRAY = True
except:
    #raise
    HAVE_METAARRAY = False
    

__all__ = ['MultiPlotItem']
class MultiPlotItem(GraphicsLayout.GraphicsLayout):
    """
    Automaticaly generates a grid of plots from a multi-dimensional array
    """
    
    def plot(self, data):
        #self.layout.clear()
        self.plots = []
            
        if HAVE_METAARRAY and (hasattr(data, 'implements') and data.implements('MetaArray')):
            if data.ndim != 2:
                raise Exception("MultiPlot currently only accepts 2D MetaArray.")
            ic = data.infoCopy()
            ax = 0
            for i in [0, 1]:
                if 'cols' in ic[i]:
                    ax = i
                    break
            #print "Plotting using axis %d as columns (%d plots)" % (ax, data.shape[ax])
            for i in range(data.shape[ax]):
                pi = self.addPlot()
                self.nextRow()
                sl = [slice(None)] * 2
                sl[ax] = i
                pi.plot(data[tuple(sl)])
                #self.layout.addItem(pi, i, 0)
                self.plots.append((pi, i, 0))
                title = None
                units = None
                info = ic[ax]['cols'][i]
                if 'title' in info:
                    title = info['title']
                elif 'name' in info:
                    title = info['name']
                if 'units' in info:
                    units = info['units']
                    
                pi.setLabel('left', text=title, units=units)
                
        else:
            raise Exception("Data type %s not (yet?) supported for MultiPlot." % type(data))
            
    def close(self):
        for p in self.plots:
            p[0].close()
        self.plots = None
        self.clear()



