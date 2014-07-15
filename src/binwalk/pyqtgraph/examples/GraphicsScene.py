# -*- coding: utf-8 -*-
## Add path to library (just for examples; you do not need this)
import initExample

from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg
from pyqtgraph.GraphicsScene import GraphicsScene

app = QtGui.QApplication([])
win = pg.GraphicsView()
win.show()


class Obj(QtGui.QGraphicsObject):
    def __init__(self):
        QtGui.QGraphicsObject.__init__(self)
        GraphicsScene.registerObject(self)
        
    def paint(self, p, *args):
        p.setPen(pg.mkPen(200,200,200))
        p.drawRect(self.boundingRect())
        
    def boundingRect(self):
        return QtCore.QRectF(0, 0, 20, 20)
        
    def mouseClickEvent(self, ev):
        if ev.double():
            print("double click")
        else:
            print("click")
        ev.accept()
        
    #def mouseDragEvent(self, ev):
        #print "drag"
        #ev.accept()
        #self.setPos(self.pos() + ev.pos()-ev.lastPos())
        
        

vb = pg.ViewBox()
win.setCentralItem(vb)

obj = Obj()
vb.addItem(obj)

obj2 = Obj()
win.addItem(obj2)

def clicked():
    print("button click")
btn = QtGui.QPushButton("BTN")
btn.clicked.connect(clicked)
prox = QtGui.QGraphicsProxyWidget()
prox.setWidget(btn)
prox.setPos(100,0)
vb.addItem(prox)

g = pg.GridItem()
vb.addItem(g)


## Start Qt event loop unless running in interactive mode.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
