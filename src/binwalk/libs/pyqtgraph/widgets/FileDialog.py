from pyqtgraph.Qt import QtGui, QtCore
import sys

__all__ = ['FileDialog']

class FileDialog(QtGui.QFileDialog):
    ## Compatibility fix for OSX:
    ## For some reason the native dialog doesn't show up when you set AcceptMode to AcceptSave on OS X, so we don't use the native dialog    
    
    def __init__(self, *args):
        QtGui.QFileDialog.__init__(self, *args)
        
        if sys.platform == 'darwin': 
            self.setOption(QtGui.QFileDialog.DontUseNativeDialog)