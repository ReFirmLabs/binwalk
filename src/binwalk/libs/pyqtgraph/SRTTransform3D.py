# -*- coding: utf-8 -*-
from .Qt import QtCore, QtGui
from .Vector import Vector
from .SRTTransform import SRTTransform
import pyqtgraph as pg
import numpy as np
import scipy.linalg

class SRTTransform3D(pg.Transform3D):
    """4x4 Transform matrix that can always be represented as a combination of 3 matrices: scale * rotate * translate
    This transform has no shear; angles are always preserved.
    """
    def __init__(self, init=None):
        pg.Transform3D.__init__(self)
        self.reset()
        if init is None:
            return
        if init.__class__ is QtGui.QTransform:
            init = SRTTransform(init)
        
        if isinstance(init, dict):
            self.restoreState(init)
        elif isinstance(init, SRTTransform3D):
            self._state = {
                'pos': Vector(init._state['pos']),
                'scale': Vector(init._state['scale']),
                'angle': init._state['angle'],
                'axis': Vector(init._state['axis']),
            }
            self.update()
        elif isinstance(init, SRTTransform):
            self._state = {
                'pos': Vector(init._state['pos']),
                'scale': Vector(init._state['scale']),
                'angle': init._state['angle'],
                'axis': Vector(0, 0, 1),
            }
            self._state['scale'][2] = 1.0
            self.update()
        elif isinstance(init, QtGui.QMatrix4x4):
            self.setFromMatrix(init)
        else:
            raise Exception("Cannot build SRTTransform3D from argument type:", type(init))

        
    def getScale(self):
        return pg.Vector(self._state['scale'])
        
    def getRotation(self):
        """Return (angle, axis) of rotation"""
        return self._state['angle'], pg.Vector(self._state['axis'])
        
    def getTranslation(self):
        return pg.Vector(self._state['pos'])
    
    def reset(self):
        self._state = {
            'pos': Vector(0,0,0),
            'scale': Vector(1,1,1),
            'angle': 0.0,  ## in degrees
            'axis': (0, 0, 1)
        }
        self.update()
        
    def translate(self, *args):
        """Adjust the translation of this transform"""
        t = Vector(*args)
        self.setTranslate(self._state['pos']+t)
        
    def setTranslate(self, *args):
        """Set the translation of this transform"""
        self._state['pos'] = Vector(*args)
        self.update()
        
    def scale(self, *args):
        """adjust the scale of this transform"""
        ## try to prevent accidentally setting 0 scale on z axis
        if len(args) == 1 and hasattr(args[0], '__len__'):
            args = args[0]
        if len(args) == 2:
            args = args + (1,)
            
        s = Vector(*args)
        self.setScale(self._state['scale'] * s)
        
    def setScale(self, *args):
        """Set the scale of this transform"""
        if len(args) == 1 and hasattr(args[0], '__len__'):
            args = args[0]
        if len(args) == 2:
            args = args + (1,)
        self._state['scale'] = Vector(*args)
        self.update()
        
    def rotate(self, angle, axis=(0,0,1)):
        """Adjust the rotation of this transform"""
        origAxis = self._state['axis']
        if axis[0] == origAxis[0] and axis[1] == origAxis[1] and axis[2] == origAxis[2]:
            self.setRotate(self._state['angle'] + angle)
        else:
            m = QtGui.QMatrix4x4()
            m.translate(*self._state['pos'])
            m.rotate(self._state['angle'], *self._state['axis'])
            m.rotate(angle, *axis)
            m.scale(*self._state['scale'])
            self.setFromMatrix(m)
        
    def setRotate(self, angle, axis=(0,0,1)):
        """Set the transformation rotation to angle (in degrees)"""
        
        self._state['angle'] = angle
        self._state['axis'] = Vector(axis)
        self.update()
    
    def setFromMatrix(self, m):
        """
        Set this transform mased on the elements of *m*
        The input matrix must be affine AND have no shear,
        otherwise the conversion will most likely fail.
        """
        for i in range(4):
            self.setRow(i, m.row(i))
        m = self.matrix().reshape(4,4)
        ## translation is 4th column
        self._state['pos'] = m[:3,3] 
        ## scale is vector-length of first three columns
        scale = (m[:3,:3]**2).sum(axis=0)**0.5
        ## see whether there is an inversion
        z = np.cross(m[0, :3], m[1, :3])
        if np.dot(z, m[2, :3]) < 0:
            scale[1] *= -1  ## doesn't really matter which axis we invert
        self._state['scale'] = scale
        
        ## rotation axis is the eigenvector with eigenvalue=1
        r = m[:3, :3] / scale[:, np.newaxis]
        try:
            evals, evecs = scipy.linalg.eig(r)
        except:
            print("Rotation matrix: %s" % str(r))
            print("Scale: %s" % str(scale))
            print("Original matrix: %s" % str(m))
            raise
        eigIndex = np.argwhere(np.abs(evals-1) < 1e-6)
        if len(eigIndex) < 1:
            print("eigenvalues: %s" % str(evals))
            print("eigenvectors: %s" % str(evecs))
            print("index: %s, %s" % (str(eigIndex), str(evals-1)))
            raise Exception("Could not determine rotation axis.")
        axis = evecs[:,eigIndex[0,0]].real
        axis /= ((axis**2).sum())**0.5
        self._state['axis'] = axis
        
        ## trace(r) == 2 cos(angle) + 1, so:
        cos = (r.trace()-1)*0.5  ## this only gets us abs(angle)
        
        ## The off-diagonal values can be used to correct the angle ambiguity, 
        ## but we need to figure out which element to use:
        axisInd = np.argmax(np.abs(axis))
        rInd,sign = [((1,2), -1), ((0,2), 1), ((0,1), -1)][axisInd]
        
        ## Then we have r-r.T = sin(angle) * 2 * sign * axis[axisInd];
        ## solve for sin(angle)
        sin = (r-r.T)[rInd] / (2. * sign * axis[axisInd])
        
        ## finally, we get the complete angle from arctan(sin/cos)
        self._state['angle'] = np.arctan2(sin, cos) * 180 / np.pi
        if self._state['angle'] == 0:
            self._state['axis'] = (0,0,1)
        
    def as2D(self):
        """Return a QTransform representing the x,y portion of this transform (if possible)"""
        return pg.SRTTransform(self)

    #def __div__(self, t):
        #"""A / B  ==  B^-1 * A"""
        #dt = t.inverted()[0] * self
        #return SRTTransform(dt)
        
    #def __mul__(self, t):
        #return SRTTransform(QtGui.QTransform.__mul__(self, t))

    def saveState(self):
        p = self._state['pos']
        s = self._state['scale']
        ax = self._state['axis']
        #if s[0] == 0:
            #raise Exception('Invalid scale: %s' % str(s))
        return {
            'pos': (p[0], p[1], p[2]), 
            'scale': (s[0], s[1], s[2]), 
            'angle': self._state['angle'], 
            'axis': (ax[0], ax[1], ax[2])
        }

    def restoreState(self, state):
        self._state['pos'] = Vector(state.get('pos', (0.,0.,0.)))
        scale = state.get('scale', (1.,1.,1.))
        scale = tuple(scale) + (1.,) * (3-len(scale))
        self._state['scale'] = Vector(scale)
        self._state['angle'] = state.get('angle', 0.)
        self._state['axis'] = state.get('axis', (0, 0, 1))
        self.update()

    def update(self):
        pg.Transform3D.setToIdentity(self)
        ## modifications to the transform are multiplied on the right, so we need to reverse order here.
        pg.Transform3D.translate(self, *self._state['pos'])
        pg.Transform3D.rotate(self, self._state['angle'], *self._state['axis'])
        pg.Transform3D.scale(self, *self._state['scale'])

    def __repr__(self):
        return str(self.saveState())
        
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
        
if __name__ == '__main__':
    import widgets
    import GraphicsView
    from functions import *
    app = QtGui.QApplication([])
    win = QtGui.QMainWindow()
    win.show()
    cw = GraphicsView.GraphicsView()
    #cw.enableMouse()  
    win.setCentralWidget(cw)
    s = QtGui.QGraphicsScene()
    cw.setScene(s)
    win.resize(600,600)
    cw.enableMouse()
    cw.setRange(QtCore.QRectF(-100., -100., 200., 200.))
    
    class Item(QtGui.QGraphicsItem):
        def __init__(self):
            QtGui.QGraphicsItem.__init__(self)
            self.b = QtGui.QGraphicsRectItem(20, 20, 20, 20, self)
            self.b.setPen(QtGui.QPen(mkPen('y')))
            self.t1 = QtGui.QGraphicsTextItem(self)
            self.t1.setHtml('<span style="color: #F00">R</span>')
            self.t1.translate(20, 20)
            self.l1 = QtGui.QGraphicsLineItem(10, 0, -10, 0, self)
            self.l2 = QtGui.QGraphicsLineItem(0, 10, 0, -10, self)
            self.l1.setPen(QtGui.QPen(mkPen('y')))
            self.l2.setPen(QtGui.QPen(mkPen('y')))
        def boundingRect(self):
            return QtCore.QRectF()
        def paint(self, *args):
            pass
            
    #s.addItem(b)
    #s.addItem(t1)
    item = Item()
    s.addItem(item)
    l1 = QtGui.QGraphicsLineItem(10, 0, -10, 0)
    l2 = QtGui.QGraphicsLineItem(0, 10, 0, -10)
    l1.setPen(QtGui.QPen(mkPen('r')))
    l2.setPen(QtGui.QPen(mkPen('r')))
    s.addItem(l1)
    s.addItem(l2)
    
    tr1 = SRTTransform()
    tr2 = SRTTransform()
    tr3 = QtGui.QTransform()
    tr3.translate(20, 0)
    tr3.rotate(45)
    print("QTransform -> Transform: %s" % str(SRTTransform(tr3)))
    
    print("tr1: %s" % str(tr1))
    
    tr2.translate(20, 0)
    tr2.rotate(45)
    print("tr2: %s" % str(tr2))
    
    dt = tr2/tr1
    print("tr2 / tr1 = %s" % str(dt))
    
    print("tr2 * tr1 = %s" % str(tr2*tr1))
    
    tr4 = SRTTransform()
    tr4.scale(-1, 1)
    tr4.rotate(30)
    print("tr1 * tr4 = %s" % str(tr1*tr4))
    
    w1 = widgets.TestROI((19,19), (22, 22), invertible=True)
    #w2 = widgets.TestROI((0,0), (150, 150))
    w1.setZValue(10)
    s.addItem(w1)
    #s.addItem(w2)
    w1Base = w1.getState()
    #w2Base = w2.getState()
    def update():
        tr1 = w1.getGlobalTransform(w1Base)
        #tr2 = w2.getGlobalTransform(w2Base)
        item.setTransform(tr1)
        
    #def update2():
        #tr1 = w1.getGlobalTransform(w1Base)
        #tr2 = w2.getGlobalTransform(w2Base)
        #t1.setTransform(tr1)
        #w1.setState(w1Base)
        #w1.applyGlobalTransform(tr2)
        
    w1.sigRegionChanged.connect(update)
    #w2.sigRegionChanged.connect(update2)
    
    	