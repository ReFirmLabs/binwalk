# -*- coding: utf-8 -*-
from .Qt import QtCore, QtGui
import pyqtgraph as pg
import numpy as np

class Transform3D(QtGui.QMatrix4x4):
    """
    Extension of QMatrix4x4 with some helpful methods added.
    """
    def __init__(self, *args):
        QtGui.QMatrix4x4.__init__(self, *args)
        
    def matrix(self, nd=3):
        if nd == 3:
            return np.array(self.copyDataTo()).reshape(4,4)
        elif nd == 2:
            m = np.array(self.copyDataTo()).reshape(4,4)
            m[2] = m[3]
            m[:,2] = m[:,3]
            return m[:3,:3]
        else:
            raise Exception("Argument 'nd' must be 2 or 3")
        
    def map(self, obj):
        """
        Extends QMatrix4x4.map() to allow mapping (3, ...) arrays of coordinates
        """
        if isinstance(obj, np.ndarray) and obj.ndim >= 2 and obj.shape[0] in (2,3):
            return pg.transformCoordinates(self, obj)
        else:
            return QtGui.QMatrix4x4.map(self, obj)
            
    def inverted(self):
        inv, b = QtGui.QMatrix4x4.inverted(self)
        return Transform3D(inv), b