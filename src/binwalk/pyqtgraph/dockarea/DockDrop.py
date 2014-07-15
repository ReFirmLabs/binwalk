# -*- coding: utf-8 -*-
from pyqtgraph.Qt import QtCore, QtGui

class DockDrop(object):
    """Provides dock-dropping methods"""
    def __init__(self, allowedAreas=None):
        object.__init__(self)
        if allowedAreas is None:
            allowedAreas = ['center', 'right', 'left', 'top', 'bottom']
        self.allowedAreas = set(allowedAreas)
        self.setAcceptDrops(True)
        self.dropArea = None
        self.overlay = DropAreaOverlay(self)
        self.overlay.raise_()
    
    def resizeOverlay(self, size):
        self.overlay.resize(size)
        
    def raiseOverlay(self):
        self.overlay.raise_()
    
    def dragEnterEvent(self, ev):
        src = ev.source()
        if hasattr(src, 'implements') and src.implements('dock'):
            #print "drag enter accept"
            ev.accept()
        else:
            #print "drag enter ignore"
            ev.ignore()
        
    def dragMoveEvent(self, ev):
        #print "drag move"
        ld = ev.pos().x()
        rd = self.width() - ld
        td = ev.pos().y()
        bd = self.height() - td
        
        mn = min(ld, rd, td, bd)
        if mn > 30:
            self.dropArea = "center"
        elif (ld == mn or td == mn) and mn > self.height()/3.:
            self.dropArea = "center"
        elif (rd == mn or ld == mn) and mn > self.width()/3.:
            self.dropArea = "center"
            
        elif rd == mn:
            self.dropArea = "right"
        elif ld == mn:
            self.dropArea = "left"
        elif td == mn:
            self.dropArea = "top"
        elif bd == mn:
            self.dropArea = "bottom"
            
        if ev.source() is self and self.dropArea == 'center':
            #print "  no self-center"
            self.dropArea = None
            ev.ignore()
        elif self.dropArea not in self.allowedAreas:
            #print "  not allowed"
            self.dropArea = None
            ev.ignore()
        else:
            #print "  ok"
            ev.accept()
        self.overlay.setDropArea(self.dropArea)
            
    def dragLeaveEvent(self, ev):
        self.dropArea = None
        self.overlay.setDropArea(self.dropArea)
    
    def dropEvent(self, ev):
        area = self.dropArea
        if area is None:
            return
        if area == 'center':
            area = 'above'
        self.area.moveDock(ev.source(), area, self)
        self.dropArea = None
        self.overlay.setDropArea(self.dropArea)

        

class DropAreaOverlay(QtGui.QWidget):
    """Overlay widget that draws drop areas during a drag-drop operation"""
    
    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)
        self.dropArea = None
        self.hide()
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        
    def setDropArea(self, area):
        self.dropArea = area
        if area is None:
            self.hide()
        else:
            ## Resize overlay to just the region where drop area should be displayed.
            ## This works around a Qt bug--can't display transparent widgets over QGLWidget
            prgn = self.parent().rect()
            rgn = QtCore.QRect(prgn)
            w = min(30, prgn.width()/3.)
            h = min(30, prgn.height()/3.)
            
            if self.dropArea == 'left':
                rgn.setWidth(w)
            elif self.dropArea == 'right':
                rgn.setLeft(rgn.left() + prgn.width() - w)
            elif self.dropArea == 'top':
                rgn.setHeight(h)
            elif self.dropArea == 'bottom':
                rgn.setTop(rgn.top() + prgn.height() - h)
            elif self.dropArea == 'center':
                rgn.adjust(w, h, -w, -h)
            self.setGeometry(rgn)
            self.show()

        self.update()
    
    def paintEvent(self, ev):
        if self.dropArea is None:
            return
        p = QtGui.QPainter(self)
        rgn = self.rect()

        p.setBrush(QtGui.QBrush(QtGui.QColor(100, 100, 255, 50)))
        p.setPen(QtGui.QPen(QtGui.QColor(50, 50, 150), 3))
        p.drawRect(rgn)
