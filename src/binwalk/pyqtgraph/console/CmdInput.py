from pyqtgraph.Qt import QtCore, QtGui
from pyqtgraph.python2_3 import asUnicode

class CmdInput(QtGui.QLineEdit):
    
    sigExecuteCmd = QtCore.Signal(object)
    
    def __init__(self, parent):
        QtGui.QLineEdit.__init__(self, parent)
        self.history = [""]
        self.ptr = 0
        #self.lastCmd = None
        #self.setMultiline(False)
    
    def keyPressEvent(self, ev):
        #print "press:", ev.key(), QtCore.Qt.Key_Up, QtCore.Qt.Key_Down, QtCore.Qt.Key_Enter
        if ev.key() == QtCore.Qt.Key_Up and self.ptr < len(self.history) - 1:
            self.setHistory(self.ptr+1)
            ev.accept()
            return
        elif ev.key() ==  QtCore.Qt.Key_Down and self.ptr > 0:
            self.setHistory(self.ptr-1)
            ev.accept()
            return
        elif ev.key() == QtCore.Qt.Key_Return:
            self.execCmd()
        else:
            QtGui.QLineEdit.keyPressEvent(self, ev)
            self.history[0] = asUnicode(self.text())
        
    def execCmd(self):
        cmd = asUnicode(self.text())
        if len(self.history) == 1 or cmd != self.history[1]:
            self.history.insert(1, cmd)
        #self.lastCmd = cmd
        self.history[0] = ""
        self.setHistory(0)
        self.sigExecuteCmd.emit(cmd)
        
    def setHistory(self, num):
        self.ptr = num
        self.setText(self.history[self.ptr])
        
    #def setMultiline(self, m):
        #height = QtGui.QFontMetrics(self.font()).lineSpacing()
        #if m:
            #self.setFixedHeight(height*5)
        #else:
            #self.setFixedHeight(height+15)
            #self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            #self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            
       
    #def sizeHint(self):
        #hint = QtGui.QPlainTextEdit.sizeHint(self)
        #height = QtGui.QFontMetrics(self.font()).lineSpacing()
        #hint.setHeight(height)
        #return hint

        
        
        