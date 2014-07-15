# -*- coding: utf-8 -*-
"""
graphicsWindows.py -  Convenience classes which create a new window with PlotWidget or ImageView.
Copyright 2010  Luke Campagnola
Distributed under MIT/X11 license. See license.txt for more infomation.
"""

from .Qt import QtCore, QtGui
from .widgets.PlotWidget import *
from .imageview import *
from .widgets.GraphicsLayoutWidget import GraphicsLayoutWidget
from .widgets.GraphicsView import GraphicsView
QAPP = None

def mkQApp():
    if QtGui.QApplication.instance() is None:
        global QAPP
        QAPP = QtGui.QApplication([])


class GraphicsWindow(GraphicsLayoutWidget):
    def __init__(self, title=None, size=(800,600), **kargs):
        mkQApp()
        #self.win = QtGui.QMainWindow()
        GraphicsLayoutWidget.__init__(self, **kargs)
        #self.win.setCentralWidget(self)
        self.resize(*size)
        if title is not None:
            self.setWindowTitle(title)
        self.show()
        

class TabWindow(QtGui.QMainWindow):
    def __init__(self, title=None, size=(800,600)):
        mkQApp()
        QtGui.QMainWindow.__init__(self)
        self.resize(*size)
        self.cw = QtGui.QTabWidget()
        self.setCentralWidget(self.cw)
        if title is not None:
            self.setWindowTitle(title)
        self.show()
        
    def __getattr__(self, attr):
        if hasattr(self.cw, attr):
            return getattr(self.cw, attr)
        else:
            raise NameError(attr)
    

class PlotWindow(PlotWidget):
    def __init__(self, title=None, **kargs):
        mkQApp()
        self.win = QtGui.QMainWindow()
        PlotWidget.__init__(self, **kargs)
        self.win.setCentralWidget(self)
        for m in ['resize']:
            setattr(self, m, getattr(self.win, m))
        if title is not None:
            self.win.setWindowTitle(title)
        self.win.show()


class ImageWindow(ImageView):
    def __init__(self, *args, **kargs):
        mkQApp()
        self.win = QtGui.QMainWindow()
        self.win.resize(800,600)
        if 'title' in kargs:
            self.win.setWindowTitle(kargs['title'])
            del kargs['title']
        ImageView.__init__(self, self.win)
        if len(args) > 0 or len(kargs) > 0:
            self.setImage(*args, **kargs)
        self.win.setCentralWidget(self)
        for m in ['resize']:
            setattr(self, m, getattr(self.win, m))
        #for m in ['setImage', 'autoRange', 'addItem', 'removeItem', 'blackLevel', 'whiteLevel', 'imageItem']:
            #setattr(self, m, getattr(self.cw, m))
        self.win.show()
