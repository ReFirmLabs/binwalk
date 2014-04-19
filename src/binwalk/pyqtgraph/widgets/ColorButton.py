# -*- coding: utf-8 -*-
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph.functions as functions

__all__ = ['ColorButton']

class ColorButton(QtGui.QPushButton):
    """
    **Bases:** QtGui.QPushButton
    
    Button displaying a color and allowing the user to select a new color.
    
    ====================== ============================================================
    **Signals**:
    sigColorChanging(self) emitted whenever a new color is picked in the color dialog
    sigColorChanged(self)  emitted when the selected color is accepted (user clicks OK)
    ====================== ============================================================
    """
    sigColorChanging = QtCore.Signal(object)  ## emitted whenever a new color is picked in the color dialog
    sigColorChanged = QtCore.Signal(object)   ## emitted when the selected color is accepted (user clicks OK)
    
    def __init__(self, parent=None, color=(128,128,128)):
        QtGui.QPushButton.__init__(self, parent)
        self.setColor(color)
        self.colorDialog = QtGui.QColorDialog()
        self.colorDialog.setOption(QtGui.QColorDialog.ShowAlphaChannel, True)
        self.colorDialog.setOption(QtGui.QColorDialog.DontUseNativeDialog, True)
        self.colorDialog.currentColorChanged.connect(self.dialogColorChanged)
        self.colorDialog.rejected.connect(self.colorRejected)
        self.colorDialog.colorSelected.connect(self.colorSelected)
        #QtCore.QObject.connect(self.colorDialog, QtCore.SIGNAL('currentColorChanged(const QColor&)'), self.currentColorChanged)
        #QtCore.QObject.connect(self.colorDialog, QtCore.SIGNAL('rejected()'), self.currentColorRejected)
        self.clicked.connect(self.selectColor)
        self.setMinimumHeight(15)
        self.setMinimumWidth(15)
        
    def paintEvent(self, ev):
        QtGui.QPushButton.paintEvent(self, ev)
        p = QtGui.QPainter(self)
        rect = self.rect().adjusted(6, 6, -6, -6)
        ## draw white base, then texture for indicating transparency, then actual color
        p.setBrush(functions.mkBrush('w'))
        p.drawRect(rect)
        p.setBrush(QtGui.QBrush(QtCore.Qt.DiagCrossPattern))
        p.drawRect(rect)
        p.setBrush(functions.mkBrush(self._color))
        p.drawRect(rect)
        p.end()
    
    def setColor(self, color, finished=True):
        """Sets the button's color and emits both sigColorChanged and sigColorChanging."""
        self._color = functions.mkColor(color)
        if finished:
            self.sigColorChanged.emit(self)
        else:
            self.sigColorChanging.emit(self)
        self.update()
        
    def selectColor(self):
        self.origColor = self.color()
        self.colorDialog.setCurrentColor(self.color())
        self.colorDialog.open()
        
    def dialogColorChanged(self, color):
        if color.isValid():
            self.setColor(color, finished=False)
            
    def colorRejected(self):
        self.setColor(self.origColor, finished=False)
    
    def colorSelected(self, color):
        self.setColor(self._color, finished=True)
    
    def saveState(self):
        return functions.colorTuple(self._color)
        
    def restoreState(self, state):
        self.setColor(state)
        
    def color(self, mode='qcolor'):
        color = functions.mkColor(self._color)
        if mode == 'qcolor':
            return color
        elif mode == 'byte':
            return (color.red(), color.green(), color.blue(), color.alpha())
        elif mode == 'float':
            return (color.red()/255., color.green()/255., color.blue()/255., color.alpha()/255.)

    def widgetGroupInterface(self):
        return (self.sigColorChanged, ColorButton.saveState, ColorButton.restoreState)
    
