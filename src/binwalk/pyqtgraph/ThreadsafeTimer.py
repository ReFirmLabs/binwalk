from pyqtgraph.Qt import QtCore, QtGui

class ThreadsafeTimer(QtCore.QObject):
    """
    Thread-safe replacement for QTimer.
    """
    
    timeout = QtCore.Signal()
    sigTimerStopRequested = QtCore.Signal()
    sigTimerStartRequested = QtCore.Signal(object)
    
    def __init__(self):
        QtCore.QObject.__init__(self)
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.timerFinished)
        self.timer.moveToThread(QtCore.QCoreApplication.instance().thread())
        self.moveToThread(QtCore.QCoreApplication.instance().thread())
        self.sigTimerStopRequested.connect(self.stop, QtCore.Qt.QueuedConnection)
        self.sigTimerStartRequested.connect(self.start, QtCore.Qt.QueuedConnection)
        
        
    def start(self, timeout):
        isGuiThread = QtCore.QThread.currentThread() == QtCore.QCoreApplication.instance().thread()
        if isGuiThread:
            #print "start timer", self, "from gui thread"
            self.timer.start(timeout)
        else:
            #print "start timer", self, "from remote thread"
            self.sigTimerStartRequested.emit(timeout)
        
    def stop(self):
        isGuiThread = QtCore.QThread.currentThread() == QtCore.QCoreApplication.instance().thread()
        if isGuiThread:
            #print "stop timer", self, "from gui thread"
            self.timer.stop()
        else:
            #print "stop timer", self, "from remote thread"
            self.sigTimerStopRequested.emit()
        
    def timerFinished(self):
        self.timeout.emit()