from pyqtgraph.Qt import QtGui, QtCore


__all__ = ['JoystickButton']

class JoystickButton(QtGui.QPushButton):
    sigStateChanged = QtCore.Signal(object, object)  ## self, state
    
    def __init__(self, parent=None):
        QtGui.QPushButton.__init__(self, parent)
        self.radius = 200
        self.setCheckable(True)
        self.state = None
        self.setState(0,0)
        self.setFixedWidth(50)
        self.setFixedHeight(50)
        
        
    def mousePressEvent(self, ev):
        self.setChecked(True)
        self.pressPos = ev.pos()
        ev.accept()
        
    def mouseMoveEvent(self, ev):
        dif = ev.pos()-self.pressPos
        self.setState(dif.x(), -dif.y())
        
    def mouseReleaseEvent(self, ev):
        self.setChecked(False)
        self.setState(0,0)
        
    def wheelEvent(self, ev):
        ev.accept()
        
        
    def doubleClickEvent(self, ev):
        ev.accept()
        
    def getState(self):
        return self.state
        
    def setState(self, *xy):
        xy = list(xy)
        d = (xy[0]**2 + xy[1]**2)**0.5
        nxy = [0,0]
        for i in [0,1]:
            if xy[i] == 0:
                nxy[i] = 0
            else:
                nxy[i] = xy[i]/d
        
        if d > self.radius:
            d = self.radius
        d = (d/self.radius)**2
        xy = [nxy[0]*d, nxy[1]*d]
        
        w2 = self.width()/2.
        h2 = self.height()/2
        self.spotPos = QtCore.QPoint(w2*(1+xy[0]), h2*(1-xy[1]))
        self.update()
        if self.state == xy:
            return
        self.state = xy
        self.sigStateChanged.emit(self, self.state)
        
    def paintEvent(self, ev):
        QtGui.QPushButton.paintEvent(self, ev)
        p = QtGui.QPainter(self)
        p.setBrush(QtGui.QBrush(QtGui.QColor(0,0,0)))
        p.drawEllipse(self.spotPos.x()-3,self.spotPos.y()-3,6,6)
        
    def resizeEvent(self, ev):
        self.setState(*self.state)
        QtGui.QPushButton.resizeEvent(self, ev)
        
        
        
if __name__ == '__main__':
    app = QtGui.QApplication([])
    w = QtGui.QMainWindow()
    b = JoystickButton()
    w.setCentralWidget(b)
    w.show()
    w.resize(100, 100)
    
    def fn(b, s):
        print("state changed:", s)
        
    b.sigStateChanged.connect(fn)
        
    ## Start Qt event loop unless running in interactive mode.
    import sys
    if sys.flags.interactive != 1:
        app.exec_()
        