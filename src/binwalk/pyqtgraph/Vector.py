# -*- coding: utf-8 -*-
"""
Vector.py -  Extension of QVector3D which adds a few missing methods.
Copyright 2010  Luke Campagnola
Distributed under MIT/X11 license. See license.txt for more infomation.
"""

from .Qt import QtGui, QtCore, USE_PYSIDE
import numpy as np

class Vector(QtGui.QVector3D):
    """Extension of QVector3D which adds a few helpful methods."""
    
    def __init__(self, *args):
        if len(args) == 1:
            if isinstance(args[0], QtCore.QSizeF):
                QtGui.QVector3D.__init__(self, float(args[0].width()), float(args[0].height()), 0)
                return
            elif isinstance(args[0], QtCore.QPoint) or isinstance(args[0], QtCore.QPointF):
                QtGui.QVector3D.__init__(self, float(args[0].x()), float(args[0].y()), 0)
            elif hasattr(args[0], '__getitem__'):
                vals = list(args[0])
                if len(vals) == 2:
                    vals.append(0)
                if len(vals) != 3:
                    raise Exception('Cannot init Vector with sequence of length %d' % len(args[0]))
                QtGui.QVector3D.__init__(self, *vals)
                return
        elif len(args) == 2:
            QtGui.QVector3D.__init__(self, args[0], args[1], 0)
            return
        QtGui.QVector3D.__init__(self, *args)

    def __len__(self):
        return 3

    def __add__(self, b):
        # workaround for pyside bug. see https://bugs.launchpad.net/pyqtgraph/+bug/1223173
        if USE_PYSIDE and isinstance(b, QtGui.QVector3D):
            b = Vector(b)
        return QtGui.QVector3D.__add__(self, b)
    
    #def __reduce__(self):
        #return (Point, (self.x(), self.y()))
        
    def __getitem__(self, i):
        if i == 0:
            return self.x()
        elif i == 1:
            return self.y()
        elif i == 2:
            return self.z()
        else:
            raise IndexError("Point has no index %s" % str(i))
        
    def __setitem__(self, i, x):
        if i == 0:
            return self.setX(x)
        elif i == 1:
            return self.setY(x)
        elif i == 2:
            return self.setZ(x)
        else:
            raise IndexError("Point has no index %s" % str(i))
        
    def __iter__(self):
        yield(self.x())
        yield(self.y())
        yield(self.z())
        