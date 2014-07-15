# -*- coding: utf-8 -*-
from .Qt import QtCore, QtGui
from .Point import Point
import numpy as np
import pyqtgraph as pg

class SRTTransform(QtGui.QTransform):
    """Transform that can always be represented as a combination of 3 matrices: scale * rotate * translate
    This transform has no shear; angles are always preserved.
    """
    def __init__(self, init=None):
        QtGui.QTransform.__init__(self)
        self.reset()
        
        if init is None:
            return
        elif isinstance(init, dict):
            self.restoreState(init)
        elif isinstance(init, SRTTransform):
            self._state = {
                'pos': Point(init._state['pos']),
                'scale': Point(init._state['scale']),
                'angle': init._state['angle']
            }
            self.update()
        elif isinstance(init, QtGui.QTransform):
            self.setFromQTransform(init)
        elif isinstance(init, QtGui.QMatrix4x4):
            self.setFromMatrix4x4(init)
        else:
            raise Exception("Cannot create SRTTransform from input type: %s" % str(type(init)))

        
    def getScale(self):
        return self._state['scale']
        
    def getAngle(self):  
        ## deprecated; for backward compatibility
        return self.getRotation()
        
    def getRotation(self):
        return self._state['angle']
        
    def getTranslation(self):
        return self._state['pos']
    
    def reset(self):
        self._state = {
            'pos': Point(0,0),
            'scale': Point(1,1),
            'angle': 0.0  ## in degrees
        }
        self.update()
        
    def setFromQTransform(self, tr):
        p1 = Point(tr.map(0., 0.))
        p2 = Point(tr.map(1., 0.))
        p3 = Point(tr.map(0., 1.))
        
        dp2 = Point(p2-p1)
        dp3 = Point(p3-p1)
        
        ## detect flipped axes
        if dp2.angle(dp3) > 0:
            #da = 180
            da = 0
            sy = -1.0
        else:
            da = 0
            sy = 1.0
            
        self._state = {
            'pos': Point(p1),
            'scale': Point(dp2.length(), dp3.length() * sy),
            'angle': (np.arctan2(dp2[1], dp2[0]) * 180. / np.pi) + da
        }
        self.update()
        
    def setFromMatrix4x4(self, m):
        m = pg.SRTTransform3D(m)
        angle, axis = m.getRotation()
        if angle != 0 and (axis[0] != 0 or axis[1] != 0 or axis[2] != 1):
            print("angle: %s  axis: %s" % (str(angle), str(axis)))
            raise Exception("Can only convert 4x4 matrix to 3x3 if rotation is around Z-axis.")
        self._state = {
            'pos': Point(m.getTranslation()),
            'scale': Point(m.getScale()),
            'angle': angle
        }
        self.update()
        
    def translate(self, *args):
        """Acceptable arguments are: 
           x, y
           [x, y]
           Point(x,y)"""
        t = Point(*args)
        self.setTranslate(self._state['pos']+t)
        
    def setTranslate(self, *args):
        """Acceptable arguments are: 
           x, y
           [x, y]
           Point(x,y)"""
        self._state['pos'] = Point(*args)
        self.update()
        
    def scale(self, *args):
        """Acceptable arguments are: 
           x, y
           [x, y]
           Point(x,y)"""
        s = Point(*args)
        self.setScale(self._state['scale'] * s)
        
    def setScale(self, *args):
        """Acceptable arguments are: 
           x, y
           [x, y]
           Point(x,y)"""
        self._state['scale'] = Point(*args)
        self.update()
        
    def rotate(self, angle):
        """Rotate the transformation by angle (in degrees)"""
        self.setRotate(self._state['angle'] + angle)
        
    def setRotate(self, angle):
        """Set the transformation rotation to angle (in degrees)"""
        self._state['angle'] = angle
        self.update()

    def __truediv__(self, t):
        """A / B  ==  B^-1 * A"""
        dt = t.inverted()[0] * self
        return SRTTransform(dt)
        
    def __div__(self, t):
        return self.__truediv__(t)
        
    def __mul__(self, t):
        return SRTTransform(QtGui.QTransform.__mul__(self, t))

    def saveState(self):
        p = self._state['pos']
        s = self._state['scale']
        #if s[0] == 0:
            #raise Exception('Invalid scale: %s' % str(s))
        return {'pos': (p[0], p[1]), 'scale': (s[0], s[1]), 'angle': self._state['angle']}

    def restoreState(self, state):
        self._state['pos'] = Point(state.get('pos', (0,0)))
        self._state['scale'] = Point(state.get('scale', (1.,1.)))
        self._state['angle'] = state.get('angle', 0)
        self.update()

    def update(self):
        QtGui.QTransform.reset(self)
        ## modifications to the transform are multiplied on the right, so we need to reverse order here.
        QtGui.QTransform.translate(self, *self._state['pos'])
        QtGui.QTransform.rotate(self, self._state['angle'])
        QtGui.QTransform.scale(self, *self._state['scale'])

    def __repr__(self):
        return str(self.saveState())
        
    def matrix(self):
        return np.array([[self.m11(), self.m12(), self.m13()],[self.m21(), self.m22(), self.m23()],[self.m31(), self.m32(), self.m33()]])
        
if __name__ == '__main__':
    from . import widgets
    import GraphicsView
    from .functions import *
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
    print("QTransform -> Transform:", SRTTransform(tr3))
    
    print("tr1:", tr1)
    
    tr2.translate(20, 0)
    tr2.rotate(45)
    print("tr2:", tr2)
    
    dt = tr2/tr1
    print("tr2 / tr1 = ", dt)
    
    print("tr2 * tr1 = ", tr2*tr1)
    
    tr4 = SRTTransform()
    tr4.scale(-1, 1)
    tr4.rotate(30)
    print("tr1 * tr4 = ", tr1*tr4)
    
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
    
    