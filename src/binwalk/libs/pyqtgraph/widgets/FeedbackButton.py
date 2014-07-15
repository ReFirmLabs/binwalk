# -*- coding: utf-8 -*-
from pyqtgraph.Qt import QtCore, QtGui

__all__ = ['FeedbackButton']

class FeedbackButton(QtGui.QPushButton):
    """
    QPushButton which flashes success/failure indication for slow or asynchronous procedures.
    """
    
    
    ### For thread-safetyness
    sigCallSuccess = QtCore.Signal(object, object, object)
    sigCallFailure = QtCore.Signal(object, object, object)
    sigCallProcess = QtCore.Signal(object, object, object)
    sigReset = QtCore.Signal()
    
    def __init__(self, *args):
        QtGui.QPushButton.__init__(self, *args)
        self.origStyle = None
        self.origText = self.text()
        self.origStyle = self.styleSheet()
        self.origTip = self.toolTip()
        self.limitedTime = True
        
        
        #self.textTimer = QtCore.QTimer()
        #self.tipTimer = QtCore.QTimer()
        #self.textTimer.timeout.connect(self.setText)
        #self.tipTimer.timeout.connect(self.setToolTip)
        
        self.sigCallSuccess.connect(self.success)
        self.sigCallFailure.connect(self.failure)
        self.sigCallProcess.connect(self.processing)
        self.sigReset.connect(self.reset)
        

    def feedback(self, success, message=None, tip="", limitedTime=True):
        """Calls success() or failure(). If you want the message to be displayed until the user takes an action, set limitedTime to False. Then call self.reset() after the desired action.Threadsafe."""
        if success:
            self.success(message, tip, limitedTime=limitedTime)
        else:
            self.failure(message, tip, limitedTime=limitedTime)
    
    def success(self, message=None, tip="", limitedTime=True):
        """Displays specified message on button and flashes button green to let user know action was successful. If you want the success to be displayed until the user takes an action, set limitedTime to False. Then call self.reset() after the desired action. Threadsafe."""
        isGuiThread = QtCore.QThread.currentThread() == QtCore.QCoreApplication.instance().thread()
        if isGuiThread:
            self.setEnabled(True)
            #print "success"
            self.startBlink("#0F0", message, tip, limitedTime=limitedTime)
        else:
            self.sigCallSuccess.emit(message, tip, limitedTime)
            
    def failure(self, message=None, tip="", limitedTime=True):
        """Displays specified message on button and flashes button red to let user know there was an error. If you want the error to be displayed until the user takes an action, set limitedTime to False. Then call self.reset() after the desired action. Threadsafe. """
        isGuiThread = QtCore.QThread.currentThread() == QtCore.QCoreApplication.instance().thread()
        if isGuiThread:
            self.setEnabled(True)
            #print "fail"
            self.startBlink("#F00", message, tip, limitedTime=limitedTime)
        else:
            self.sigCallFailure.emit(message, tip, limitedTime)

    def processing(self, message="Processing..", tip="", processEvents=True):
        """Displays specified message on button to let user know the action is in progress. Threadsafe. """
        isGuiThread = QtCore.QThread.currentThread() == QtCore.QCoreApplication.instance().thread()
        if isGuiThread:
            self.setEnabled(False)
            self.setText(message, temporary=True)
            self.setToolTip(tip, temporary=True)
            if processEvents:
                QtGui.QApplication.processEvents()
        else:
            self.sigCallProcess.emit(message, tip, processEvents)
           
                
    def reset(self):
        """Resets the button to its original text and style. Threadsafe."""
        isGuiThread = QtCore.QThread.currentThread() == QtCore.QCoreApplication.instance().thread()
        if isGuiThread:
            self.limitedTime = True
            self.setText()
            self.setToolTip()
            self.setStyleSheet()
        else:
            self.sigReset.emit()
        
    def startBlink(self, color, message=None, tip="", limitedTime=True):
        #if self.origStyle is None:
            #self.origStyle = self.styleSheet()
            #self.origText = self.text()
        self.setFixedHeight(self.height())
        
        if message is not None:
            self.setText(message, temporary=True)
        self.setToolTip(tip, temporary=True)
        self.count = 0
        #self.indStyle = "QPushButton {border: 2px solid %s; border-radius: 5px}" % color
        self.indStyle = "QPushButton {background-color: %s}" % color
        self.limitedTime = limitedTime
        self.borderOn()
        if limitedTime:
            QtCore.QTimer.singleShot(2000, self.setText)
            QtCore.QTimer.singleShot(10000, self.setToolTip)

    def borderOn(self):
        self.setStyleSheet(self.indStyle, temporary=True)
        if self.limitedTime or self.count <=2:
            QtCore.QTimer.singleShot(100, self.borderOff)
        
            
    def borderOff(self):
        self.setStyleSheet()
        self.count += 1
        if self.count >= 2:
            if self.limitedTime:
                return
        QtCore.QTimer.singleShot(30, self.borderOn)
        
            
    def setText(self, text=None, temporary=False):
        if text is None:
            text = self.origText
        #print text
        QtGui.QPushButton.setText(self, text)
        if not temporary:
            self.origText = text

    def setToolTip(self, text=None, temporary=False):
        if text is None:
            text = self.origTip
        QtGui.QPushButton.setToolTip(self, text)
        if not temporary:
            self.origTip = text

    def setStyleSheet(self, style=None, temporary=False):
        if style is None:
            style = self.origStyle
        QtGui.QPushButton.setStyleSheet(self, style)
        if not temporary:
            self.origStyle = style


if __name__ == '__main__':
    import time
    app = QtGui.QApplication([])
    win = QtGui.QMainWindow()
    btn = FeedbackButton("Button")
    fail = True
    def click():
        btn.processing("Hold on..")
        time.sleep(2.0)
        
        global fail
        fail = not fail
        if fail:
            btn.failure(message="FAIL.", tip="There was a failure. Get over it.")
        else:
            btn.success(message="Bueno!")
    btn.clicked.connect(click)
    win.setCentralWidget(btn)
    win.show()