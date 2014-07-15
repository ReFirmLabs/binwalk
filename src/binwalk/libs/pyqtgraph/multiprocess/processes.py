from .remoteproxy import RemoteEventHandler, ClosedError, NoResultError, LocalObjectProxy, ObjectProxy
import subprocess, atexit, os, sys, time, random, socket, signal
import multiprocessing.connection
import pyqtgraph as pg
try:
    import cPickle as pickle
except ImportError:
    import pickle

__all__ = ['Process', 'QtProcess', 'ForkedProcess', 'ClosedError', 'NoResultError']

class Process(RemoteEventHandler):
    """
    Bases: RemoteEventHandler
    
    This class is used to spawn and control a new python interpreter.
    It uses subprocess.Popen to start the new process and communicates with it
    using multiprocessing.Connection objects over a network socket.
    
    By default, the remote process will immediately enter an event-processing
    loop that carries out requests send from the parent process.
    
    Remote control works mainly through proxy objects::
    
        proc = Process()              ## starts process, returns handle
        rsys = proc._import('sys')    ## asks remote process to import 'sys', returns
                                      ## a proxy which references the imported module
        rsys.stdout.write('hello\n')  ## This message will be printed from the remote 
                                      ## process. Proxy objects can usually be used
                                      ## exactly as regular objects are.
        proc.close()                  ## Request the remote process shut down
    
    Requests made via proxy objects may be synchronous or asynchronous and may
    return objects either by proxy or by value (if they are picklable). See
    ProxyObject for more information.
    """
    
    def __init__(self, name=None, target=None, executable=None, copySysPath=True, debug=False, timeout=20, wrapStdout=None):
        """
        ============  =============================================================
        Arguments:
        name          Optional name for this process used when printing messages
                      from the remote process.
        target        Optional function to call after starting remote process. 
                      By default, this is startEventLoop(), which causes the remote
                      process to process requests from the parent process until it
                      is asked to quit. If you wish to specify a different target,
                      it must be picklable (bound methods are not).
        copySysPath   If True, copy the contents of sys.path to the remote process
        debug         If True, print detailed information about communication
                      with the child process.
        wrapStdout    If True (default on windows) then stdout and stderr from the
                      child process will be caught by the parent process and
                      forwarded to its stdout/stderr. This provides a workaround
                      for a python bug: http://bugs.python.org/issue3905
                      but has the side effect that child output is significantly
                      delayed relative to the parent output.
        ============  =============================================================
        """
        if target is None:
            target = startEventLoop
        if name is None:
            name = str(self)
        if executable is None:
            executable = sys.executable
        self.debug = debug
        
        ## random authentication key
        authkey = os.urandom(20)

        ## Windows seems to have a hard time with hmac 
        if sys.platform.startswith('win'):
            authkey = None

        #print "key:", ' '.join([str(ord(x)) for x in authkey])
        ## Listen for connection from remote process (and find free port number)
        port = 10000
        while True:
            try:
                l = multiprocessing.connection.Listener(('localhost', int(port)), authkey=authkey)
                break
            except socket.error as ex:
                if ex.errno != 98 and ex.errno != 10048: # unix=98, win=10048
                    raise
                port += 1


        ## start remote process, instruct it to run target function
        sysPath = sys.path if copySysPath else None
        bootstrap = os.path.abspath(os.path.join(os.path.dirname(__file__), 'bootstrap.py'))
        self.debugMsg('Starting child process (%s %s)' % (executable, bootstrap))
        
        if wrapStdout is None:
            wrapStdout = sys.platform.startswith('win')

        if wrapStdout:
            ## note: we need all three streams to have their own PIPE due to this bug:
            ## http://bugs.python.org/issue3905
            stdout = subprocess.PIPE
            stderr = subprocess.PIPE
            self.proc = subprocess.Popen((executable, bootstrap), stdin=subprocess.PIPE, stdout=stdout, stderr=stderr)
            ## to circumvent the bug and still make the output visible, we use 
            ## background threads to pass data from pipes to stdout/stderr
            self._stdoutForwarder = FileForwarder(self.proc.stdout, "stdout")
            self._stderrForwarder = FileForwarder(self.proc.stderr, "stderr")
        else:
            self.proc = subprocess.Popen((executable, bootstrap), stdin=subprocess.PIPE)

        targetStr = pickle.dumps(target)  ## double-pickle target so that child has a chance to 
                                          ## set its sys.path properly before unpickling the target
        pid = os.getpid() # we must send pid to child because windows does not have getppid
        
        ## Send everything the remote process needs to start correctly
        data = dict(
            name=name+'_child', 
            port=port, 
            authkey=authkey, 
            ppid=pid, 
            targetStr=targetStr, 
            path=sysPath, 
            pyside=pg.Qt.USE_PYSIDE,
            debug=debug
            )
        pickle.dump(data, self.proc.stdin)
        self.proc.stdin.close()
        
        ## open connection for remote process
        self.debugMsg('Listening for child process on port %d, authkey=%s..' % (port, repr(authkey)))
        while True:
            try:
                conn = l.accept()
                break
            except IOError as err:
                if err.errno == 4:  # interrupted; try again
                    continue
                else:
                    raise
                
        RemoteEventHandler.__init__(self, conn, name+'_parent', pid=self.proc.pid, debug=debug)
        self.debugMsg('Connected to child process.')
        
        atexit.register(self.join)

        
    def join(self, timeout=10):
        self.debugMsg('Joining child process..')
        if self.proc.poll() is None:
            self.close()
            start = time.time()
            while self.proc.poll() is None:
                if timeout is not None and time.time() - start > timeout:
                    raise Exception('Timed out waiting for remote process to end.')
                time.sleep(0.05)
        self.debugMsg('Child process exited. (%d)' % self.proc.returncode)

    def debugMsg(self, msg):
        if hasattr(self, '_stdoutForwarder'):
            ## Lock output from subprocess to make sure we do not get line collisions
            with self._stdoutForwarder.lock:
                with self._stderrForwarder.lock:
                    RemoteEventHandler.debugMsg(self, msg)
        else:
            RemoteEventHandler.debugMsg(self, msg)

        
def startEventLoop(name, port, authkey, ppid, debug=False):
    if debug:
        import os
        print('[%d] connecting to server at port localhost:%d, authkey=%s..' % (os.getpid(), port, repr(authkey)))
    conn = multiprocessing.connection.Client(('localhost', int(port)), authkey=authkey)
    if debug:
        print('[%d] connected; starting remote proxy.' % os.getpid())
    global HANDLER
    #ppid = 0 if not hasattr(os, 'getppid') else os.getppid()
    HANDLER = RemoteEventHandler(conn, name, ppid, debug=debug)
    while True:
        try:
            HANDLER.processRequests()  # exception raised when the loop should exit
            time.sleep(0.01)
        except ClosedError:
            break


class ForkedProcess(RemoteEventHandler):
    """
    ForkedProcess is a substitute for Process that uses os.fork() to generate a new process.
    This is much faster than starting a completely new interpreter and child processes
    automatically have a copy of the entire program state from before the fork. This
    makes it an appealing approach when parallelizing expensive computations. (see
    also Parallelizer)
    
    However, fork() comes with some caveats and limitations:

    - fork() is not available on Windows.
    - It is not possible to have a QApplication in both parent and child process
      (unless both QApplications are created _after_ the call to fork())
      Attempts by the forked process to access Qt GUI elements created by the parent
      will most likely cause the child to crash.
    - Likewise, database connections are unlikely to function correctly in a forked child.
    - Threads are not copied by fork(); the new process 
      will have only one thread that starts wherever fork() was called in the parent process.
    - Forked processes are unceremoniously terminated when join() is called; they are not 
      given any opportunity to clean up. (This prevents them calling any cleanup code that
      was only intended to be used by the parent process)
    - Normally when fork()ing, open file handles are shared with the parent process, 
      which is potentially dangerous. ForkedProcess is careful to close all file handles 
      that are not explicitly needed--stdout, stderr, and a single pipe to the parent 
      process.
      
    """
    
    def __init__(self, name=None, target=0, preProxy=None, randomReseed=True):
        """
        When initializing, an optional target may be given. 
        If no target is specified, self.eventLoop will be used.
        If None is given, no target will be called (and it will be up 
        to the caller to properly shut down the forked process)
        
        preProxy may be a dict of values that will appear as ObjectProxy
        in the remote process (but do not need to be sent explicitly since 
        they are available immediately before the call to fork().
        Proxies will be availabe as self.proxies[name].
        
        If randomReseed is True, the built-in random and numpy.random generators
        will be reseeded in the child process.
        """
        self.hasJoined = False
        if target == 0:
            target = self.eventLoop
        if name is None:
            name = str(self)
        
        conn, remoteConn = multiprocessing.Pipe()
        
        proxyIDs = {}
        if preProxy is not None:
            for k, v in preProxy.iteritems():
                proxyId = LocalObjectProxy.registerObject(v)
                proxyIDs[k] = proxyId
        
        ppid = os.getpid()  # write this down now; windows doesn't have getppid
        pid = os.fork()
        if pid == 0:
            self.isParent = False
            ## We are now in the forked process; need to be extra careful what we touch while here.
            ##   - no reading/writing file handles/sockets owned by parent process (stdout is ok)
            ##   - don't touch QtGui or QApplication at all; these are landmines.
            ##   - don't let the process call exit handlers
            
            os.setpgrp()  ## prevents signals (notably keyboard interrupt) being forwarded from parent to this process
            
            ## close all file handles we do not want shared with parent
            conn.close()
            sys.stdin.close()  ## otherwise we screw with interactive prompts.
            fid = remoteConn.fileno()
            os.closerange(3, fid)
            os.closerange(fid+1, 4096) ## just guessing on the maximum descriptor count..
            
            ## Override any custom exception hooks
            def excepthook(*args):
                import traceback
                traceback.print_exception(*args)
            sys.excepthook = excepthook 
            
            ## Make it harder to access QApplication instance
            if 'PyQt4.QtGui' in sys.modules:
                sys.modules['PyQt4.QtGui'].QApplication = None
            sys.modules.pop('PyQt4.QtGui', None)
            sys.modules.pop('PyQt4.QtCore', None)
            
            ## sabotage atexit callbacks
            atexit._exithandlers = []
            atexit.register(lambda: os._exit(0))
            
            if randomReseed:
                if 'numpy.random' in sys.modules:
                    sys.modules['numpy.random'].seed(os.getpid() ^ int(time.time()*10000%10000))
                if 'random' in sys.modules:
                    sys.modules['random'].seed(os.getpid() ^ int(time.time()*10000%10000))
            
            #ppid = 0 if not hasattr(os, 'getppid') else os.getppid()
            RemoteEventHandler.__init__(self, remoteConn, name+'_child', pid=ppid)
            
            self.forkedProxies = {}
            for name, proxyId in proxyIDs.iteritems():
                self.forkedProxies[name] = ObjectProxy(ppid, proxyId=proxyId, typeStr=repr(preProxy[name]))
            
            if target is not None:
                target()
                
        else:
            self.isParent = True
            self.childPid = pid
            remoteConn.close()
            RemoteEventHandler.handlers = {}  ## don't want to inherit any of this from the parent.
            
            RemoteEventHandler.__init__(self, conn, name+'_parent', pid=pid)
            atexit.register(self.join)
        
        
    def eventLoop(self):
        while True:
            try:
                self.processRequests()  # exception raised when the loop should exit
                time.sleep(0.01)
            except ClosedError:
                break
            except:
                print("Error occurred in forked event loop:")
                sys.excepthook(*sys.exc_info())
        sys.exit(0)
        
    def join(self, timeout=10):
        if self.hasJoined:
            return
        #os.kill(pid, 9)  
        try:
            self.close(callSync='sync', timeout=timeout, noCleanup=True)  ## ask the child process to exit and require that it return a confirmation.
            os.waitpid(self.childPid, 0)
        except IOError:  ## probably remote process has already quit
            pass  
        self.hasJoined = True

    def kill(self):
        """Immediately kill the forked remote process. 
        This is generally safe because forked processes are already
        expected to _avoid_ any cleanup at exit."""
        os.kill(self.childPid, signal.SIGKILL)
        self.hasJoined = True
        
        

##Special set of subclasses that implement a Qt event loop instead.
        
class RemoteQtEventHandler(RemoteEventHandler):
    def __init__(self, *args, **kwds):
        RemoteEventHandler.__init__(self, *args, **kwds)
        
    def startEventTimer(self):
        from pyqtgraph.Qt import QtGui, QtCore
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.processRequests)
        self.timer.start(10)
    
    def processRequests(self):
        try:
            RemoteEventHandler.processRequests(self)
        except ClosedError:
            from pyqtgraph.Qt import QtGui, QtCore
            QtGui.QApplication.instance().quit()
            self.timer.stop()
            #raise SystemExit

class QtProcess(Process):
    """
    QtProcess is essentially the same as Process, with two major differences:
    
    - The remote process starts by running startQtEventLoop() which creates a 
      QApplication in the remote process and uses a QTimer to trigger
      remote event processing. This allows the remote process to have its own 
      GUI.
    - A QTimer is also started on the parent process which polls for requests
      from the child process. This allows Qt signals emitted within the child 
      process to invoke slots on the parent process and vice-versa. This can 
      be disabled using processRequests=False in the constructor.
      
    Example::
    
        proc = QtProcess()            
        rQtGui = proc._import('PyQt4.QtGui')
        btn = rQtGui.QPushButton('button on child process')
        btn.show()
        
        def slot():
            print('slot invoked on parent process')
        btn.clicked.connect(proxy(slot))   # be sure to send a proxy of the slot
    """
    
    def __init__(self, **kwds):
        if 'target' not in kwds:
            kwds['target'] = startQtEventLoop
        self._processRequests = kwds.pop('processRequests', True)
        Process.__init__(self, **kwds)
        self.startEventTimer()
        
    def startEventTimer(self):
        from pyqtgraph.Qt import QtGui, QtCore  ## avoid module-level import to keep bootstrap snappy.
        self.timer = QtCore.QTimer()
        if self._processRequests:
            app = QtGui.QApplication.instance()
            if app is None:
                raise Exception("Must create QApplication before starting QtProcess, or use QtProcess(processRequests=False)")
            self.startRequestProcessing()
    
    def startRequestProcessing(self, interval=0.01):
        """Start listening for requests coming from the child process.
        This allows signals to be connected from the child process to the parent.
        """
        self.timer.timeout.connect(self.processRequests)
        self.timer.start(interval*1000)
        
    def stopRequestProcessing(self):
        self.timer.stop()
    
    def processRequests(self):
        try:
            Process.processRequests(self)
        except ClosedError:
            self.timer.stop()
    
def startQtEventLoop(name, port, authkey, ppid, debug=False):
    if debug:
        import os
        print('[%d] connecting to server at port localhost:%d, authkey=%s..' % (os.getpid(), port, repr(authkey)))
    conn = multiprocessing.connection.Client(('localhost', int(port)), authkey=authkey)
    if debug:
        print('[%d] connected; starting remote proxy.' % os.getpid())
    from pyqtgraph.Qt import QtGui, QtCore
    #from PyQt4 import QtGui, QtCore
    app = QtGui.QApplication.instance()
    #print app
    if app is None:
        app = QtGui.QApplication([])
        app.setQuitOnLastWindowClosed(False)  ## generally we want the event loop to stay open 
                                              ## until it is explicitly closed by the parent process.
    
    global HANDLER
    #ppid = 0 if not hasattr(os, 'getppid') else os.getppid()
    HANDLER = RemoteQtEventHandler(conn, name, ppid, debug=debug)
    HANDLER.startEventTimer()
    app.exec_()

import threading
class FileForwarder(threading.Thread):
    """
    Background thread that forwards data from one pipe to another. 
    This is used to catch data from stdout/stderr of the child process
    and print it back out to stdout/stderr. We need this because this
    bug: http://bugs.python.org/issue3905  _requires_ us to catch
    stdout/stderr.

    *output* may be a file or 'stdout' or 'stderr'. In the latter cases,
    sys.stdout/stderr are retrieved once for every line that is output,
    which ensures that the correct behavior is achieved even if 
    sys.stdout/stderr are replaced at runtime.
    """
    def __init__(self, input, output):
        threading.Thread.__init__(self)
        self.input = input
        self.output = output
        self.lock = threading.Lock()
        self.start()

    def run(self):
        if self.output == 'stdout':
            while True:
                line = self.input.readline()
                with self.lock:
                    sys.stdout.write(line)
        elif self.output == 'stderr':
            while True:
                line = self.input.readline()
                with self.lock:
                    sys.stderr.write(line)
        else:
            while True:
                line = self.input.readline()
                with self.lock:
                    self.output.write(line)



