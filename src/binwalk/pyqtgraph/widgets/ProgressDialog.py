# -*- coding: utf-8 -*-
from pyqtgraph.Qt import QtGui, QtCore

__all__ = ['ProgressDialog']
class ProgressDialog(QtGui.QProgressDialog):
    """
    Extends QProgressDialog for use in 'with' statements.

    Example::

        with ProgressDialog("Processing..", minVal, maxVal) as dlg:
            # do stuff
            dlg.setValue(i)   ## could also use dlg += 1
            if dlg.wasCanceled():
                raise Exception("Processing canceled by user")
    """
    def __init__(self, labelText, minimum=0, maximum=100, cancelText='Cancel', parent=None, wait=250, busyCursor=False, disable=False):
        """
        ============== ================================================================
        **Arguments:**
        labelText      (required)
        cancelText     Text to display on cancel button, or None to disable it.
        minimum
        maximum
        parent       
        wait           Length of time (im ms) to wait before displaying dialog
        busyCursor     If True, show busy cursor until dialog finishes
        disable        If True, the progress dialog will not be displayed
                       and calls to wasCanceled() will always return False.
                       If ProgressDialog is entered from a non-gui thread, it will
                       always be disabled.
        ============== ================================================================
        """    
        isGuiThread = QtCore.QThread.currentThread() == QtCore.QCoreApplication.instance().thread()
        self.disabled = disable or (not isGuiThread)
        if self.disabled:
            return

        noCancel = False
        if cancelText is None:
            cancelText = ''
            noCancel = True
            
        self.busyCursor = busyCursor
            
        QtGui.QProgressDialog.__init__(self, labelText, cancelText, minimum, maximum, parent)
        self.setMinimumDuration(wait)
        self.setWindowModality(QtCore.Qt.WindowModal)
        self.setValue(self.minimum())
        if noCancel:
            self.setCancelButton(None)
        

    def __enter__(self):
        if self.disabled:
            return self
        if self.busyCursor:
            QtGui.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
        return self

    def __exit__(self, exType, exValue, exTrace):
        if self.disabled:
            return
        if self.busyCursor:
            QtGui.QApplication.restoreOverrideCursor()
        self.setValue(self.maximum())
        
    def __iadd__(self, val):
        """Use inplace-addition operator for easy incrementing."""
        if self.disabled:
            return self
        self.setValue(self.value()+val)
        return self


    ## wrap all other functions to make sure they aren't being called from non-gui threads
    
    def setValue(self, val):
        if self.disabled:
            return
        QtGui.QProgressDialog.setValue(self, val)
        
    def setLabelText(self, val):
        if self.disabled:
            return
        QtGui.QProgressDialog.setLabelText(self, val)
    
    def setMaximum(self, val):
        if self.disabled:
            return
        QtGui.QProgressDialog.setMaximum(self, val)

    def setMinimum(self, val):
        if self.disabled:
            return
        QtGui.QProgressDialog.setMinimum(self, val)
        
    def wasCanceled(self):
        if self.disabled:
            return False
        return QtGui.QProgressDialog.wasCanceled(self)

    def maximum(self):
        if self.disabled:
            return 0
        return QtGui.QProgressDialog.maximum(self)

    def minimum(self):
        if self.disabled:
            return 0
        return QtGui.QProgressDialog.minimum(self)
        
