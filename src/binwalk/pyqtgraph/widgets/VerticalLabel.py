# -*- coding: utf-8 -*-
from pyqtgraph.Qt import QtGui, QtCore

__all__ = ['VerticalLabel']
#class VerticalLabel(QtGui.QLabel):
    #def paintEvent(self, ev):
        #p = QtGui.QPainter(self)
        #p.rotate(-90)
        #self.hint = p.drawText(QtCore.QRect(-self.height(), 0, self.height(), self.width()), QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter, self.text())
        #p.end()
        #self.setMinimumWidth(self.hint.height())
        #self.setMinimumHeight(self.hint.width())

    #def sizeHint(self):
        #if hasattr(self, 'hint'):
            #return QtCore.QSize(self.hint.height(), self.hint.width())
        #else:
            #return QtCore.QSize(16, 50)

class VerticalLabel(QtGui.QLabel):
    def __init__(self, text, orientation='vertical', forceWidth=True):
        QtGui.QLabel.__init__(self, text)
        self.forceWidth = forceWidth
        self.orientation = None
        self.setOrientation(orientation)
        
    def setOrientation(self, o):
        if self.orientation == o:
            return
        self.orientation = o
        self.update()
        self.updateGeometry()
        
    def paintEvent(self, ev):
        p = QtGui.QPainter(self)
        #p.setBrush(QtGui.QBrush(QtGui.QColor(100, 100, 200)))
        #p.setPen(QtGui.QPen(QtGui.QColor(50, 50, 100)))
        #p.drawRect(self.rect().adjusted(0, 0, -1, -1))
        
        #p.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255)))
        
        if self.orientation == 'vertical':
            p.rotate(-90)
            rgn = QtCore.QRect(-self.height(), 0, self.height(), self.width())
        else:
            rgn = self.contentsRect()
        align = self.alignment()
        #align  = QtCore.Qt.AlignTop|QtCore.Qt.AlignHCenter
            
        self.hint = p.drawText(rgn, align, self.text())
        p.end()
        
        if self.orientation == 'vertical':
            self.setMaximumWidth(self.hint.height())
            self.setMinimumWidth(0)
            self.setMaximumHeight(16777215)
            if self.forceWidth:
                self.setMinimumHeight(self.hint.width())
            else:
                self.setMinimumHeight(0)
        else:
            self.setMaximumHeight(self.hint.height())
            self.setMinimumHeight(0)
            self.setMaximumWidth(16777215)
            if self.forceWidth:
                self.setMinimumWidth(self.hint.width())
            else:
                self.setMinimumWidth(0)

    def sizeHint(self):
        if self.orientation == 'vertical':
            if hasattr(self, 'hint'):
                return QtCore.QSize(self.hint.height(), self.hint.width())
            else:
                return QtCore.QSize(19, 50)
        else:
            if hasattr(self, 'hint'):
                return QtCore.QSize(self.hint.width(), self.hint.height())
            else:
                return QtCore.QSize(50, 19)


if __name__ == '__main__':
    app = QtGui.QApplication([])
    win = QtGui.QMainWindow()
    w = QtGui.QWidget()
    l = QtGui.QGridLayout()
    w.setLayout(l)
    
    l1 = VerticalLabel("text 1", orientation='horizontal')
    l2 = VerticalLabel("text 2")
    l3 = VerticalLabel("text 3")
    l4 = VerticalLabel("text 4", orientation='horizontal')
    l.addWidget(l1, 0, 0)
    l.addWidget(l2, 1, 1)
    l.addWidget(l3, 2, 2)
    l.addWidget(l4, 3, 3)
    win.setCentralWidget(w)
    win.show()