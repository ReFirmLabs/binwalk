import os, sys, time, multiprocessing, re
from .processes import ForkedProcess
from .remoteproxy import ClosedError

class CanceledError(Exception):
    """Raised when the progress dialog is canceled during a processing operation."""
    pass

class Parallelize(object):
    """
    Class for ultra-simple inline parallelization on multi-core CPUs
    
    Example::
    
        ## Here is the serial (single-process) task:
        
        tasks = [1, 2, 4, 8]
        results = []
        for task in tasks:
            result = processTask(task)
            results.append(result)
        print(results)
        
        
        ## Here is the parallelized version:
        
        tasks = [1, 2, 4, 8]
        results = []
        with Parallelize(tasks, workers=4, results=results) as tasker:
            for task in tasker:
                result = processTask(task)
                tasker.results.append(result)
        print(results)
        
        
    The only major caveat is that *result* in the example above must be picklable,
    since it is automatically sent via pipe back to the parent process.
    """

    def __init__(self, tasks=None, workers=None, block=True, progressDialog=None, randomReseed=True, **kwds):
        """
        ===============  ===================================================================
        Arguments:
        tasks            list of objects to be processed (Parallelize will determine how to 
                         distribute the tasks). If unspecified, then each worker will receive
                         a single task with a unique id number.
        workers          number of worker processes or None to use number of CPUs in the 
                         system
        progressDialog   optional dict of arguments for ProgressDialog
                         to update while tasks are processed
        randomReseed     If True, each forked process will reseed its random number generator
                         to ensure independent results. Works with the built-in random
                         and numpy.random.
        kwds             objects to be shared by proxy with child processes (they will 
                         appear as attributes of the tasker)
        ===============  ===================================================================
        """
        
        ## Generate progress dialog. 
        ## Note that we want to avoid letting forked child processes play with progress dialogs..
        self.showProgress = False
        if progressDialog is not None:
            self.showProgress = True
            if isinstance(progressDialog, basestring):
                progressDialog = {'labelText': progressDialog}
            import pyqtgraph as pg
            self.progressDlg = pg.ProgressDialog(**progressDialog)
        
        if workers is None:
            workers = self.suggestedWorkerCount()
        if not hasattr(os, 'fork'):
            workers = 1
        self.workers = workers
        if tasks is None:
            tasks = range(workers)
        self.tasks = list(tasks)
        self.reseed = randomReseed
        self.kwds = kwds.copy()
        self.kwds['_taskStarted'] = self._taskStarted
        
    def __enter__(self):
        self.proc = None
        if self.workers == 1: 
            return self.runSerial()
        else:
            return self.runParallel()
    
    def __exit__(self, *exc_info):
        
        if self.proc is not None:  ## worker 
            exceptOccurred = exc_info[0] is not None ## hit an exception during processing.
                
            try:
                if exceptOccurred:
                    sys.excepthook(*exc_info)
            finally:
                #print os.getpid(), 'exit'
                os._exit(1 if exceptOccurred else 0)
                
        else:  ## parent
            if self.showProgress:
                self.progressDlg.__exit__(None, None, None)

    def runSerial(self):
        if self.showProgress:
            self.progressDlg.__enter__()
            self.progressDlg.setMaximum(len(self.tasks))
        self.progress = {os.getpid(): []}
        return Tasker(self, None, self.tasks, self.kwds)

    
    def runParallel(self):
        self.childs = []
        
        ## break up tasks into one set per worker
        workers = self.workers
        chunks = [[] for i in xrange(workers)]
        i = 0
        for i in range(len(self.tasks)):
            chunks[i%workers].append(self.tasks[i])
        
        ## fork and assign tasks to each worker
        for i in range(workers):
            proc = ForkedProcess(target=None, preProxy=self.kwds, randomReseed=self.reseed)
            if not proc.isParent:
                self.proc = proc
                return Tasker(self, proc, chunks[i], proc.forkedProxies)
            else:
                self.childs.append(proc)
        
        ## Keep track of the progress of each worker independently.
        self.progress = dict([(ch.childPid, []) for ch in self.childs])
        ## for each child process, self.progress[pid] is a list
        ## of task indexes. The last index is the task currently being
        ## processed; all others are finished.
            
            
        try:
            if self.showProgress:
                self.progressDlg.__enter__()
                self.progressDlg.setMaximum(len(self.tasks))
            ## process events from workers until all have exited.
                
            activeChilds = self.childs[:]
            self.exitCodes = []
            pollInterval = 0.01
            while len(activeChilds) > 0:
                waitingChildren = 0
                rem = []
                for ch in activeChilds:
                    try:
                        n = ch.processRequests()
                        if n > 0:
                            waitingChildren += 1
                    except ClosedError:
                        #print ch.childPid, 'process finished'
                        rem.append(ch)
                        if self.showProgress:
                            self.progressDlg += 1
                #print "remove:", [ch.childPid for ch in rem]
                for ch in rem:
                    activeChilds.remove(ch)
                    while True:
                        try:
                            pid, exitcode = os.waitpid(ch.childPid, 0)
                            self.exitCodes.append(exitcode)
                            break
                        except OSError as ex:
                            if ex.errno == 4:  ## If we get this error, just try again
                                continue
                                #print "Ignored system call interruption"
                            else:
                                raise
                    
                    #print [ch.childPid for ch in activeChilds]
                    
                if self.showProgress and self.progressDlg.wasCanceled():
                    for ch in activeChilds:
                        ch.kill()
                    raise CanceledError()
                    
                ## adjust polling interval--prefer to get exactly 1 event per poll cycle.
                if waitingChildren > 1:
                    pollInterval *= 0.7
                elif waitingChildren == 0:
                    pollInterval /= 0.7
                pollInterval = max(min(pollInterval, 0.5), 0.0005) ## but keep it within reasonable limits
                
                time.sleep(pollInterval)
        finally:
            if self.showProgress:
                self.progressDlg.__exit__(None, None, None)
        if len(self.exitCodes) < len(self.childs):
            raise Exception("Parallelizer started %d processes but only received exit codes from %d." % (len(self.childs), len(self.exitCodes)))
        for code in self.exitCodes:
            if code != 0:
                raise Exception("Error occurred in parallel-executed subprocess (console output may have more information).")
        return []  ## no tasks for parent process.
    
    
    @staticmethod
    def suggestedWorkerCount():
        if 'linux' in sys.platform:
            ## I think we can do a little better here..
            ## cpu_count does not consider that there is little extra benefit to using hyperthreaded cores.
            try:
                cores = {}
                pid = None
                
                for line in open('/proc/cpuinfo'):
                    m = re.match(r'physical id\s+:\s+(\d+)', line)
                    if m is not None:
                        pid = m.groups()[0]
                    m = re.match(r'cpu cores\s+:\s+(\d+)', line)
                    if m is not None:
                        cores[pid] = int(m.groups()[0])
                return sum(cores.values())
            except:
                return multiprocessing.cpu_count()
                
        else:
            return multiprocessing.cpu_count()
        
    def _taskStarted(self, pid, i, **kwds):
        ## called remotely by tasker to indicate it has started working on task i
        #print pid, 'reported starting task', i
        if self.showProgress:
            if len(self.progress[pid]) > 0:
                self.progressDlg += 1
            if pid == os.getpid():  ## single-worker process
                if self.progressDlg.wasCanceled():
                    raise CanceledError()
        self.progress[pid].append(i)
    
    
class Tasker(object):
    def __init__(self, parallelizer, process, tasks, kwds):
        self.proc = process
        self.par = parallelizer
        self.tasks = tasks
        for k, v in kwds.iteritems():
            setattr(self, k, v)
        
    def __iter__(self):
        ## we could fix this up such that tasks are retrieved from the parent process one at a time..
        for i, task in enumerate(self.tasks):
            self.index = i
            #print os.getpid(), 'starting task', i
            self._taskStarted(os.getpid(), i, _callSync='off')
            yield task
        if self.proc is not None:
            #print os.getpid(), 'no more tasks'
            self.proc.close()
    
    def process(self):
        """
        Process requests from parent.
        Usually it is not necessary to call this unless you would like to 
        receive messages (such as exit requests) during an iteration.
        """
        if self.proc is not None:
            self.proc.processRequests()
    
    def numWorkers(self):
        """
        Return the number of parallel workers
        """
        return self.par.workers
    
#class Parallelizer:
    #"""
    #Use::
    
        #p = Parallelizer()
        #with p(4) as i:
            #p.finish(do_work(i))
        #print p.results()
    
    #"""
    #def __init__(self):
        #pass

    #def __call__(self, n):
        #self.replies = []
        #self.conn = None  ## indicates this is the parent process
        #return Session(self, n)
            
    #def finish(self, data):
        #if self.conn is None:
            #self.replies.append((self.i, data))
        #else:
            ##print "send", self.i, data
            #self.conn.send((self.i, data))
            #os._exit(0)
            
    #def result(self):
        #print self.replies
        
#class Session:
    #def __init__(self, par, n):
        #self.par = par
        #self.n = n
        
    #def __enter__(self):
        #self.childs = []
        #for i in range(1, self.n):
            #c1, c2 = multiprocessing.Pipe()
            #pid = os.fork()
            #if pid == 0:  ## child
                #self.par.i = i
                #self.par.conn = c2
                #self.childs = None
                #c1.close()
                #return i
            #else:
                #self.childs.append(c1)
                #c2.close()
        #self.par.i = 0
        #return 0
            
        
        
    #def __exit__(self, *exc_info):
        #if exc_info[0] is not None:
            #sys.excepthook(*exc_info)
        #if self.childs is not None:
            #self.par.replies.extend([conn.recv() for conn in self.childs])
        #else:
            #self.par.finish(None)
        
