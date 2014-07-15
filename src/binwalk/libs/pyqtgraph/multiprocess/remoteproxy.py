import os, time, sys, traceback, weakref
import numpy as np
try:
    import __builtin__ as builtins
    import cPickle as pickle
except ImportError:
    import builtins
    import pickle

class ClosedError(Exception):
    """Raised when an event handler receives a request to close the connection
    or discovers that the connection has been closed."""
    pass

class NoResultError(Exception):
    """Raised when a request for the return value of a remote call fails
    because the call has not yet returned."""
    pass

    
class RemoteEventHandler(object):
    """
    This class handles communication between two processes. One instance is present on 
    each process and listens for communication from the other process. This enables
    (amongst other things) ObjectProxy instances to look up their attributes and call 
    their methods.
    
    This class is responsible for carrying out actions on behalf of the remote process.
    Each instance holds one end of a Connection which allows python
    objects to be passed between processes.
    
    For the most common operations, see _import(), close(), and transfer()
    
    To handle and respond to incoming requests, RemoteEventHandler requires that its
    processRequests method is called repeatedly (this is usually handled by the Process
    classes defined in multiprocess.processes).
    
    
    
    
    """
    handlers = {}   ## maps {process ID : handler}. This allows unpickler to determine which process
                    ## an object proxy belongs to
                         
    def __init__(self, connection, name, pid, debug=False):
        self.debug = debug
        self.conn = connection
        self.name = name
        self.results = {} ## reqId: (status, result); cache of request results received from the remote process
                          ## status is either 'result' or 'error'
                          ##   if 'error', then result will be (exception, formatted exceprion)
                          ##   where exception may be None if it could not be passed through the Connection.
                          
        self.proxies = {} ## maps {weakref(proxy): proxyId}; used to inform the remote process when a proxy has been deleted.
        
        ## attributes that affect the behavior of the proxy. 
        ## See ObjectProxy._setProxyOptions for description
        self.proxyOptions = {
            'callSync': 'sync',      ## 'sync', 'async', 'off'
            'timeout': 10,           ## float
            'returnType': 'auto',    ## 'proxy', 'value', 'auto'
            'autoProxy': False,      ## bool
            'deferGetattr': False,   ## True, False
            'noProxyTypes': [ type(None), str, int, float, tuple, list, dict, LocalObjectProxy, ObjectProxy ],
        }
        
        self.nextRequestId = 0
        self.exited = False
        
        RemoteEventHandler.handlers[pid] = self  ## register this handler as the one communicating with pid
    
    @classmethod
    def getHandler(cls, pid):
        try:
            return cls.handlers[pid]
        except:
            print(pid, cls.handlers)
            raise
    
    def debugMsg(self, msg):
        if not self.debug:
            return
        print("[%d] %s" % (os.getpid(), str(msg)))
    
    def getProxyOption(self, opt):
        return self.proxyOptions[opt]
        
    def setProxyOptions(self, **kwds):
        """
        Set the default behavior options for object proxies.
        See ObjectProxy._setProxyOptions for more info.
        """
        self.proxyOptions.update(kwds)
    
    def processRequests(self):
        """Process all pending requests from the pipe, return
        after no more events are immediately available. (non-blocking)
        Returns the number of events processed.
        """
        if self.exited:
            self.debugMsg('  processRequests: exited already; raise ClosedError.')
            raise ClosedError()
        
        numProcessed = 0
        while self.conn.poll():
            try:
                self.handleRequest()
                numProcessed += 1
            except ClosedError:
                self.debugMsg('processRequests: got ClosedError from handleRequest; setting exited=True.')
                self.exited = True
                raise
            #except IOError as err:  ## let handleRequest take care of this.
                #self.debugMsg('  got IOError from handleRequest; try again.')
                #if err.errno == 4:  ## interrupted system call; try again
                    #continue
                #else:
                    #raise
            except:
                print("Error in process %s" % self.name)
                sys.excepthook(*sys.exc_info())
                
        if numProcessed > 0:
            self.debugMsg('processRequests: finished %d requests' % numProcessed)
        return numProcessed
    
    def handleRequest(self):
        """Handle a single request from the remote process. 
        Blocks until a request is available."""
        result = None
        while True:
            try:
                ## args, kwds are double-pickled to ensure this recv() call never fails                
                cmd, reqId, nByteMsgs, optStr = self.conn.recv() 
                break
            except EOFError:
                self.debugMsg('  handleRequest: got EOFError from recv; raise ClosedError.')
                ## remote process has shut down; end event loop
                raise ClosedError()
            except IOError as err:
                if err.errno == 4:  ## interrupted system call; try again
                    self.debugMsg('  handleRequest: got IOError 4 from recv; try again.')
                    continue
                else:
                    self.debugMsg('  handleRequest: got IOError %d from recv (%s); raise ClosedError.' % (err.errno, err.strerror))
                    raise ClosedError()
        
        self.debugMsg("  handleRequest: received %s %s" % (str(cmd), str(reqId)))
            
        ## read byte messages following the main request
        byteData = []
        if nByteMsgs > 0:
            self.debugMsg("    handleRequest: reading %d byte messages" % nByteMsgs)
        for i in range(nByteMsgs):
            while True:
                try:
                    byteData.append(self.conn.recv_bytes())
                    break
                except EOFError:
                    self.debugMsg("    handleRequest: got EOF while reading byte messages; raise ClosedError.")
                    raise ClosedError()
                except IOError as err:
                    if err.errno == 4:
                        self.debugMsg("    handleRequest: got IOError 4 while reading byte messages; try again.")
                        continue
                    else:
                        self.debugMsg("    handleRequest: got IOError while reading byte messages; raise ClosedError.")
                        raise ClosedError()
            
        
        try:
            if cmd == 'result' or cmd == 'error':
                resultId = reqId
                reqId = None  ## prevents attempt to return information from this request
                              ## (this is already a return from a previous request)
            
            opts = pickle.loads(optStr)
            self.debugMsg("    handleRequest: id=%s opts=%s" % (str(reqId), str(opts)))
            #print os.getpid(), "received request:", cmd, reqId, opts
            returnType = opts.get('returnType', 'auto')
            
            if cmd == 'result':
                self.results[resultId] = ('result', opts['result'])
            elif cmd == 'error':
                self.results[resultId] = ('error', (opts['exception'], opts['excString']))
            elif cmd == 'getObjAttr':
                result = getattr(opts['obj'], opts['attr'])
            elif cmd == 'callObj':
                obj = opts['obj']
                fnargs = opts['args']
                fnkwds = opts['kwds']
                
                ## If arrays were sent as byte messages, they must be re-inserted into the 
                ## arguments
                if len(byteData) > 0:
                    for i,arg in enumerate(fnargs):
                        if isinstance(arg, tuple) and len(arg) > 0 and arg[0] == '__byte_message__':
                            ind = arg[1]
                            dtype, shape = arg[2]
                            fnargs[i] = np.fromstring(byteData[ind], dtype=dtype).reshape(shape)
                    for k,arg in fnkwds.items():
                        if isinstance(arg, tuple) and len(arg) > 0 and arg[0] == '__byte_message__':
                            ind = arg[1]
                            dtype, shape = arg[2]
                            fnkwds[k] = np.fromstring(byteData[ind], dtype=dtype).reshape(shape)
                
                if len(fnkwds) == 0:  ## need to do this because some functions do not allow keyword arguments.
                    try:
                        result = obj(*fnargs)
                    except:
                        print("Failed to call object %s: %d, %s" % (obj, len(fnargs), fnargs[1:]))
                        raise
                else:
                    result = obj(*fnargs, **fnkwds)
                    
            elif cmd == 'getObjValue':
                result = opts['obj']  ## has already been unpickled into its local value
                returnType = 'value'
            elif cmd == 'transfer':
                result = opts['obj']
                returnType = 'proxy'
            elif cmd == 'transferArray':
                ## read array data from next message:
                result = np.fromstring(byteData[0], dtype=opts['dtype']).reshape(opts['shape'])
                returnType = 'proxy'
            elif cmd == 'import':
                name = opts['module']
                fromlist = opts.get('fromlist', [])
                mod = builtins.__import__(name, fromlist=fromlist)
                
                if len(fromlist) == 0:
                    parts = name.lstrip('.').split('.')
                    result = mod
                    for part in parts[1:]:
                        result = getattr(result, part)
                else:
                    result = map(mod.__getattr__, fromlist)
                
            elif cmd == 'del':
                LocalObjectProxy.releaseProxyId(opts['proxyId'])
                #del self.proxiedObjects[opts['objId']]
                
            elif cmd == 'close':
                if reqId is not None:
                    result = True
                    returnType = 'value'
                    
            exc = None
        except:
            exc = sys.exc_info()

            
            
        if reqId is not None:
            if exc is None:
                self.debugMsg("    handleRequest: sending return value for %d: %s" % (reqId, str(result))) 
                #print "returnValue:", returnValue, result
                if returnType == 'auto':
                    result = self.autoProxy(result, self.proxyOptions['noProxyTypes'])
                elif returnType == 'proxy':
                    result = LocalObjectProxy(result)
                
                try:
                    self.replyResult(reqId, result)
                except:
                    sys.excepthook(*sys.exc_info())
                    self.replyError(reqId, *sys.exc_info())
            else:
                self.debugMsg("    handleRequest: returning exception for %d" % reqId) 
                self.replyError(reqId, *exc)
                    
        elif exc is not None:
            sys.excepthook(*exc)
    
        if cmd == 'close':
            if opts.get('noCleanup', False) is True:
                os._exit(0)  ## exit immediately, do not pass GO, do not collect $200.
                             ## (more importantly, do not call any code that would
                             ## normally be invoked at exit)
            else:
                raise ClosedError()
        
    
    
    def replyResult(self, reqId, result):
        self.send(request='result', reqId=reqId, callSync='off', opts=dict(result=result))
    
    def replyError(self, reqId, *exc):
        print("error: %s %s %s" % (self.name, str(reqId), str(exc[1])))
        excStr = traceback.format_exception(*exc)
        try:
            self.send(request='error', reqId=reqId, callSync='off', opts=dict(exception=exc[1], excString=excStr))
        except:
            self.send(request='error', reqId=reqId, callSync='off', opts=dict(exception=None, excString=excStr))
    
    def send(self, request, opts=None, reqId=None, callSync='sync', timeout=10, returnType=None, byteData=None, **kwds):
        """Send a request or return packet to the remote process.
        Generally it is not necessary to call this method directly; it is for internal use.
        (The docstring has information that is nevertheless useful to the programmer
        as it describes the internal protocol used to communicate between processes)
        
        ==========  ====================================================================
        Arguments:  
        request     String describing the type of request being sent (see below)
        reqId       Integer uniquely linking a result back to the request that generated
                    it. (most requests leave this blank)
        callSync    'sync':  return the actual result of the request
                    'async': return a Request object which can be used to look up the 
                             result later
                    'off':   return no result
        timeout     Time in seconds to wait for a response when callSync=='sync'
        opts        Extra arguments sent to the remote process that determine the way
                    the request will be handled (see below)
        returnType  'proxy', 'value', or 'auto'
        byteData    If specified, this is a list of objects to be sent as byte messages
                    to the remote process.
                    This is used to send large arrays without the cost of pickling.
        ==========  ====================================================================
        
        Description of request strings and options allowed for each:
        
        =============  =============  ========================================================
        request        option         description
        -------------  -------------  --------------------------------------------------------
        getObjAttr                    Request the remote process return (proxy to) an
                                      attribute of an object.
                       obj            reference to object whose attribute should be 
                                      returned
                       attr           string name of attribute to return
                       returnValue    bool or 'auto' indicating whether to return a proxy or
                                      the actual value. 
                       
        callObj                       Request the remote process call a function or 
                                      method. If a request ID is given, then the call's
                                      return value will be sent back (or information
                                      about the error that occurred while running the
                                      function)
                       obj            the (reference to) object to call
                       args           tuple of arguments to pass to callable
                       kwds           dict of keyword arguments to pass to callable
                       returnValue    bool or 'auto' indicating whether to return a proxy or
                                      the actual value. 
                       
        getObjValue                   Request the remote process return the value of
                                      a proxied object (must be picklable)
                       obj            reference to object whose value should be returned
                       
        transfer                      Copy an object to the remote process and request
                                      it return a proxy for the new object.
                       obj            The object to transfer.
                       
        import                        Request the remote process import new symbols
                                      and return proxy(ies) to the imported objects
                       module         the string name of the module to import
                       fromlist       optional list of string names to import from module
                       
        del                           Inform the remote process that a proxy has been 
                                      released (thus the remote process may be able to 
                                      release the original object)
                       proxyId        id of proxy which is no longer referenced by 
                                      remote host
                                      
        close                         Instruct the remote process to stop its event loop
                                      and exit. Optionally, this request may return a 
                                      confirmation.
            
        result                        Inform the remote process that its request has 
                                      been processed                        
                       result         return value of a request
                       
        error                         Inform the remote process that its request failed
                       exception      the Exception that was raised (or None if the 
                                      exception could not be pickled)
                       excString      string-formatted version of the exception and 
                                      traceback
        =============  =====================================================================
        """
        #if len(kwds) > 0:
            #print "Warning: send() ignored args:", kwds
            
        if opts is None:
            opts = {}
        
        assert callSync in ['off', 'sync', 'async'], 'callSync must be one of "off", "sync", or "async"'
        if reqId is None:
            if callSync != 'off': ## requested return value; use the next available request ID
                reqId = self.nextRequestId
                self.nextRequestId += 1
        else:
            ## If requestId is provided, this _must_ be a response to a previously received request.
            assert request in ['result', 'error']
        
        if returnType is not None:
            opts['returnType'] = returnType
            
        #print os.getpid(), "send request:", request, reqId, opts
        
        ## double-pickle args to ensure that at least status and request ID get through
        try:
            optStr = pickle.dumps(opts)
        except:
            print("====  Error pickling this object:  ====")
            print(opts)
            print("=======================================")
            raise
        
        nByteMsgs = 0
        if byteData is not None:
            nByteMsgs = len(byteData)
            
        ## Send primary request
        request = (request, reqId, nByteMsgs, optStr)
        self.debugMsg('send request: cmd=%s nByteMsgs=%d id=%s opts=%s' % (str(request[0]), nByteMsgs, str(reqId), str(opts)))
        self.conn.send(request)
        
        ## follow up by sending byte messages
        if byteData is not None:
            for obj in byteData:  ## Remote process _must_ be prepared to read the same number of byte messages!
                self.conn.send_bytes(obj)
            self.debugMsg('  sent %d byte messages' % len(byteData))
        
        self.debugMsg('  call sync: %s' % callSync)
        if callSync == 'off':
            return
        
        req = Request(self, reqId, description=str(request), timeout=timeout)
        if callSync == 'async':
            return req
            
        if callSync == 'sync':
            try:
                return req.result()
            except NoResultError:
                return req
        
    def close(self, callSync='off', noCleanup=False, **kwds):
        self.send(request='close', opts=dict(noCleanup=noCleanup), callSync=callSync, **kwds)
    
    def getResult(self, reqId):
        ## raises NoResultError if the result is not available yet
        #print self.results.keys(), os.getpid()
        if reqId not in self.results:
            try:
                self.processRequests()
            except ClosedError:  ## even if remote connection has closed, we may have 
                                 ## received new data during this call to processRequests()
                pass
        if reqId not in self.results:
            raise NoResultError()
        status, result = self.results.pop(reqId)
        if status == 'result': 
            return result
        elif status == 'error':
            #print ''.join(result)
            exc, excStr = result
            if exc is not None:
                print("===== Remote process raised exception on request: =====")
                print(''.join(excStr))
                print("===== Local Traceback to request follows: =====")
                raise exc
            else:
                print(''.join(excStr))
                raise Exception("Error getting result. See above for exception from remote process.")
                
        else:
            raise Exception("Internal error.")
    
    def _import(self, mod, **kwds):
        """
        Request the remote process import a module (or symbols from a module)
        and return the proxied results. Uses built-in __import__() function, but 
        adds a bit more processing:
        
            _import('module')  =>  returns module
            _import('module.submodule')  =>  returns submodule 
                                             (note this differs from behavior of __import__)
            _import('module', fromlist=[name1, name2, ...])  =>  returns [module.name1, module.name2, ...]
                                             (this also differs from behavior of __import__)
            
        """
        return self.send(request='import', callSync='sync', opts=dict(module=mod), **kwds)
        
    def getObjAttr(self, obj, attr, **kwds):
        return self.send(request='getObjAttr', opts=dict(obj=obj, attr=attr), **kwds)
        
    def getObjValue(self, obj, **kwds):
        return self.send(request='getObjValue', opts=dict(obj=obj), **kwds)
        
    def callObj(self, obj, args, kwds, **opts):
        opts = opts.copy()
        args = list(args)
        
        ## Decide whether to send arguments by value or by proxy
        noProxyTypes = opts.pop('noProxyTypes', None)
        if noProxyTypes is None:
            noProxyTypes = self.proxyOptions['noProxyTypes']
            
        autoProxy = opts.pop('autoProxy', self.proxyOptions['autoProxy'])
        if autoProxy is True:
            args = [self.autoProxy(v, noProxyTypes) for v in args]
            for k, v in kwds.iteritems():
                opts[k] = self.autoProxy(v, noProxyTypes)
        
        byteMsgs = []
        
        ## If there are arrays in the arguments, send those as byte messages.
        ## We do this because pickling arrays is too expensive.
        for i,arg in enumerate(args):
            if arg.__class__ == np.ndarray:
                args[i] = ("__byte_message__", len(byteMsgs), (arg.dtype, arg.shape))
                byteMsgs.append(arg)
        for k,v in kwds.items():
            if v.__class__ == np.ndarray:
                kwds[k] = ("__byte_message__", len(byteMsgs), (v.dtype, v.shape))
                byteMsgs.append(v)
        
        return self.send(request='callObj', opts=dict(obj=obj, args=args, kwds=kwds), byteData=byteMsgs, **opts)

    def registerProxy(self, proxy):
        ref = weakref.ref(proxy, self.deleteProxy)
        self.proxies[ref] = proxy._proxyId
    
    def deleteProxy(self, ref):
        proxyId = self.proxies.pop(ref)
        try:
            self.send(request='del', opts=dict(proxyId=proxyId), callSync='off')
        except IOError:  ## if remote process has closed down, there is no need to send delete requests anymore
            pass

    def transfer(self, obj, **kwds):
        """
        Transfer an object by value to the remote host (the object must be picklable) 
        and return a proxy for the new remote object.
        """
        if obj.__class__ is np.ndarray:
            opts = {'dtype': obj.dtype, 'shape': obj.shape}
            return self.send(request='transferArray', opts=opts, byteData=[obj], **kwds)            
        else:
            return self.send(request='transfer', opts=dict(obj=obj), **kwds)
        
    def autoProxy(self, obj, noProxyTypes):
        ## Return object wrapped in LocalObjectProxy _unless_ its type is in noProxyTypes.
        for typ in noProxyTypes:
            if isinstance(obj, typ):
                return obj
        return LocalObjectProxy(obj)
        
        
class Request(object):
    """
    Request objects are returned when calling an ObjectProxy in asynchronous mode
    or if a synchronous call has timed out. Use hasResult() to ask whether
    the result of the call has been returned yet. Use result() to get
    the returned value.
    """
    def __init__(self, process, reqId, description=None, timeout=10):
        self.proc = process
        self.description = description
        self.reqId = reqId
        self.gotResult = False
        self._result = None
        self.timeout = timeout
        
    def result(self, block=True, timeout=None):
        """
        Return the result for this request. 
        
        If block is True, wait until the result has arrived or *timeout* seconds passes.
        If the timeout is reached, raise NoResultError. (use timeout=None to disable)
        If block is False, raise NoResultError immediately if the result has not arrived yet.
        
        If the process's connection has closed before the result arrives, raise ClosedError.
        """
        
        if self.gotResult:
            return self._result
            
        if timeout is None:
           timeout = self.timeout 
        
        if block:
            start = time.time()
            while not self.hasResult():
                if self.proc.exited:
                    raise ClosedError()
                time.sleep(0.005)
                if timeout >= 0 and time.time() - start > timeout:
                    print("Request timed out: %s" % self.description)
                    import traceback
                    traceback.print_stack()
                    raise NoResultError()
            return self._result
        else:
            self._result = self.proc.getResult(self.reqId)  ## raises NoResultError if result is not available yet
            self.gotResult = True
            return self._result
        
    def hasResult(self):
        """Returns True if the result for this request has arrived."""
        try:
            self.result(block=False)
        except NoResultError:
            pass
        
        return self.gotResult

class LocalObjectProxy(object):
    """
    Used for wrapping local objects to ensure that they are send by proxy to a remote host.
    Note that 'proxy' is just a shorter alias for LocalObjectProxy.
    
    For example::
    
        data = [1,2,3,4,5]
        remotePlot.plot(data)         ## by default, lists are pickled and sent by value
        remotePlot.plot(proxy(data))  ## force the object to be sent by proxy
    
    """
    nextProxyId = 0
    proxiedObjects = {}  ## maps {proxyId: object}
    
    
    @classmethod
    def registerObject(cls, obj):
        ## assign it a unique ID so we can keep a reference to the local object
        
        pid = cls.nextProxyId
        cls.nextProxyId += 1
        cls.proxiedObjects[pid] = obj
        #print "register:", cls.proxiedObjects
        return pid
    
    @classmethod
    def lookupProxyId(cls, pid):
        return cls.proxiedObjects[pid]
    
    @classmethod
    def releaseProxyId(cls, pid):
        del cls.proxiedObjects[pid]
        #print "release:", cls.proxiedObjects 
    
    def __init__(self, obj, **opts):
        """
        Create a 'local' proxy object that, when sent to a remote host,
        will appear as a normal ObjectProxy to *obj*. 
        Any extra keyword arguments are passed to proxy._setProxyOptions()
        on the remote side.
        """
        self.processId = os.getpid()
        #self.objectId = id(obj)
        self.typeStr = repr(obj)
        #self.handler = handler
        self.obj = obj
        self.opts = opts
        
    def __reduce__(self):
        ## a proxy is being pickled and sent to a remote process.
        ## every time this happens, a new proxy will be generated in the remote process,
        ## so we keep a new ID so we can track when each is released.
        pid = LocalObjectProxy.registerObject(self.obj)
        return (unpickleObjectProxy, (self.processId, pid, self.typeStr, None, self.opts))
        
## alias
proxy = LocalObjectProxy

def unpickleObjectProxy(processId, proxyId, typeStr, attributes=None, opts=None):
    if processId == os.getpid():
        obj = LocalObjectProxy.lookupProxyId(proxyId)
        if attributes is not None:
            for attr in attributes:
                obj = getattr(obj, attr)
        return obj
    else:
        proxy = ObjectProxy(processId, proxyId=proxyId, typeStr=typeStr)
        if opts is not None:
            proxy._setProxyOptions(**opts)
        return proxy
    
class ObjectProxy(object):
    """
    Proxy to an object stored by the remote process. Proxies are created
    by calling Process._import(), Process.transfer(), or by requesting/calling
    attributes on existing proxy objects.
    
    For the most part, this object can be used exactly as if it
    were a local object::
    
        rsys = proc._import('sys')   # returns proxy to sys module on remote process
        rsys.stdout                  # proxy to remote sys.stdout
        rsys.stdout.write            # proxy to remote sys.stdout.write
        rsys.stdout.write('hello')   # calls sys.stdout.write('hello') on remote machine
                                     # and returns the result (None)
    
    When calling a proxy to a remote function, the call can be made synchronous
    (result of call is returned immediately), asynchronous (result is returned later),
    or return can be disabled entirely::
    
        ros = proc._import('os')
        
        ## synchronous call; result is returned immediately
        pid = ros.getpid()
        
        ## asynchronous call
        request = ros.getpid(_callSync='async')
        while not request.hasResult():
            time.sleep(0.01)
        pid = request.result()
        
        ## disable return when we know it isn't needed
        rsys.stdout.write('hello', _callSync='off')
    
    Additionally, values returned from a remote function call are automatically
    returned either by value (must be picklable) or by proxy. 
    This behavior can be forced::
    
        rnp = proc._import('numpy')
        arrProxy = rnp.array([1,2,3,4], _returnType='proxy')
        arrValue = rnp.array([1,2,3,4], _returnType='value')
    
    The default callSync and returnType behaviors (as well as others) can be set 
    for each proxy individually using ObjectProxy._setProxyOptions() or globally using 
    proc.setProxyOptions(). 
    
    """
    def __init__(self, processId, proxyId, typeStr='', parent=None):
        object.__init__(self)
        ## can't set attributes directly because setattr is overridden.
        self.__dict__['_processId'] = processId
        self.__dict__['_typeStr'] = typeStr
        self.__dict__['_proxyId'] = proxyId
        self.__dict__['_attributes'] = ()
        ## attributes that affect the behavior of the proxy. 
        ## in all cases, a value of None causes the proxy to ask
        ## its parent event handler to make the decision
        self.__dict__['_proxyOptions'] = {
            'callSync': None,      ## 'sync', 'async', None 
            'timeout': None,       ## float, None
            'returnType': None,    ## 'proxy', 'value', 'auto', None
            'deferGetattr': None,  ## True, False, None
            'noProxyTypes': None,  ## list of types to send by value instead of by proxy
        }
        
        self.__dict__['_handler'] = RemoteEventHandler.getHandler(processId)
        self.__dict__['_handler'].registerProxy(self)  ## handler will watch proxy; inform remote process when the proxy is deleted.
    
    def _setProxyOptions(self, **kwds):
        """
        Change the behavior of this proxy. For all options, a value of None
        will cause the proxy to instead use the default behavior defined
        by its parent Process.
        
        Options are:
        
        =============  =============================================================
        callSync       'sync', 'async', 'off', or None. 
                       If 'async', then calling methods will return a Request object
                       which can be used to inquire later about the result of the 
                       method call.
                       If 'sync', then calling a method
                       will block until the remote process has returned its result
                       or the timeout has elapsed (in this case, a Request object
                       is returned instead).
                       If 'off', then the remote process is instructed _not_ to 
                       reply and the method call will return None immediately.
        returnType     'auto', 'proxy', 'value', or None. 
                       If 'proxy', then the value returned when calling a method
                       will be a proxy to the object on the remote process.
                       If 'value', then attempt to pickle the returned object and
                       send it back.
                       If 'auto', then the decision is made by consulting the
                       'noProxyTypes' option.
        autoProxy      bool or None. If True, arguments to __call__ are 
                       automatically converted to proxy unless their type is 
                       listed in noProxyTypes (see below). If False, arguments
                       are left untouched. Use proxy(obj) to manually convert
                       arguments before sending. 
        timeout        float or None. Length of time to wait during synchronous 
                       requests before returning a Request object instead.
        deferGetattr   True, False, or None. 
                       If False, all attribute requests will be sent to the remote 
                       process immediately and will block until a response is
                       received (or timeout has elapsed).
                       If True, requesting an attribute from the proxy returns a
                       new proxy immediately. The remote process is _not_ contacted
                       to make this request. This is faster, but it is possible to 
                       request an attribute that does not exist on the proxied
                       object. In this case, AttributeError will not be raised
                       until an attempt is made to look up the attribute on the
                       remote process.
        noProxyTypes   List of object types that should _not_ be proxied when
                       sent to the remote process.
        =============  =============================================================
        """
        self._proxyOptions.update(kwds)
    
    def _getValue(self):
        """
        Return the value of the proxied object
        (the remote object must be picklable)
        """
        return self._handler.getObjValue(self)
        
    def _getProxyOption(self, opt):
        val = self._proxyOptions[opt]
        if val is None:
            return self._handler.getProxyOption(opt)
        return val
    
    def _getProxyOptions(self):
        return dict([(k, self._getProxyOption(k)) for k in self._proxyOptions])
    
    def __reduce__(self):
        return (unpickleObjectProxy, (self._processId, self._proxyId, self._typeStr, self._attributes))
    
    def __repr__(self):
        #objRepr = self.__getattr__('__repr__')(callSync='value')
        return "<ObjectProxy for process %d, object 0x%x: %s >" % (self._processId, self._proxyId, self._typeStr)
        
        
    def __getattr__(self, attr, **kwds):
        """
        Calls __getattr__ on the remote object and returns the attribute
        by value or by proxy depending on the options set (see
        ObjectProxy._setProxyOptions and RemoteEventHandler.setProxyOptions)
        
        If the option 'deferGetattr' is True for this proxy, then a new proxy object
        is returned _without_ asking the remote object whether the named attribute exists.
        This can save time when making multiple chained attribute requests,
        but may also defer a possible AttributeError until later, making
        them more difficult to debug.
        """
        opts = self._getProxyOptions()
        for k in opts:
            if '_'+k in kwds:
                opts[k] = kwds.pop('_'+k)
        if opts['deferGetattr'] is True:
            return self._deferredAttr(attr)
        else:
            #opts = self._getProxyOptions()
            return self._handler.getObjAttr(self, attr, **opts)
    
    def _deferredAttr(self, attr):
        return DeferredObjectProxy(self, attr)
    
    def __call__(self, *args, **kwds):
        """
        Attempts to call the proxied object from the remote process.
        Accepts extra keyword arguments:
        
            _callSync    'off', 'sync', or 'async'
            _returnType   'value', 'proxy', or 'auto'
        
        If the remote call raises an exception on the remote process,
        it will be re-raised on the local process.
        
        """
        opts = self._getProxyOptions()
        for k in opts:
            if '_'+k in kwds:
                opts[k] = kwds.pop('_'+k)
        return self._handler.callObj(obj=self, args=args, kwds=kwds, **opts)
    
    
    ## Explicitly proxy special methods. Is there a better way to do this??
    
    def _getSpecialAttr(self, attr):
        ## this just gives us an easy way to change the behavior of the special methods
        return self._deferredAttr(attr)
    
    def __getitem__(self, *args):
        return self._getSpecialAttr('__getitem__')(*args)
    
    def __setitem__(self, *args):
        return self._getSpecialAttr('__setitem__')(*args, _callSync='off')
        
    def __setattr__(self, *args):
        return self._getSpecialAttr('__setattr__')(*args, _callSync='off')
        
    def __str__(self, *args):
        return self._getSpecialAttr('__str__')(*args, _returnType='value')
        
    def __len__(self, *args):
        return self._getSpecialAttr('__len__')(*args)
    
    def __add__(self, *args):
        return self._getSpecialAttr('__add__')(*args)
    
    def __sub__(self, *args):
        return self._getSpecialAttr('__sub__')(*args)
        
    def __div__(self, *args):
        return self._getSpecialAttr('__div__')(*args)
        
    def __truediv__(self, *args):
        return self._getSpecialAttr('__truediv__')(*args)
        
    def __floordiv__(self, *args):
        return self._getSpecialAttr('__floordiv__')(*args)
        
    def __mul__(self, *args):
        return self._getSpecialAttr('__mul__')(*args)
        
    def __pow__(self, *args):
        return self._getSpecialAttr('__pow__')(*args)
        
    def __iadd__(self, *args):
        return self._getSpecialAttr('__iadd__')(*args, _callSync='off')
    
    def __isub__(self, *args):
        return self._getSpecialAttr('__isub__')(*args, _callSync='off')
        
    def __idiv__(self, *args):
        return self._getSpecialAttr('__idiv__')(*args, _callSync='off')
        
    def __itruediv__(self, *args):
        return self._getSpecialAttr('__itruediv__')(*args, _callSync='off')
        
    def __ifloordiv__(self, *args):
        return self._getSpecialAttr('__ifloordiv__')(*args, _callSync='off')
        
    def __imul__(self, *args):
        return self._getSpecialAttr('__imul__')(*args, _callSync='off')
        
    def __ipow__(self, *args):
        return self._getSpecialAttr('__ipow__')(*args, _callSync='off')
        
    def __rshift__(self, *args):
        return self._getSpecialAttr('__rshift__')(*args)
        
    def __lshift__(self, *args):
        return self._getSpecialAttr('__lshift__')(*args)
        
    def __irshift__(self, *args):
        return self._getSpecialAttr('__irshift__')(*args, _callSync='off')
        
    def __ilshift__(self, *args):
        return self._getSpecialAttr('__ilshift__')(*args, _callSync='off')
        
    def __eq__(self, *args):
        return self._getSpecialAttr('__eq__')(*args)
    
    def __ne__(self, *args):
        return self._getSpecialAttr('__ne__')(*args)
        
    def __lt__(self, *args):
        return self._getSpecialAttr('__lt__')(*args)
    
    def __gt__(self, *args):
        return self._getSpecialAttr('__gt__')(*args)
        
    def __le__(self, *args):
        return self._getSpecialAttr('__le__')(*args)
    
    def __ge__(self, *args):
        return self._getSpecialAttr('__ge__')(*args)
        
    def __and__(self, *args):
        return self._getSpecialAttr('__and__')(*args)
        
    def __or__(self, *args):
        return self._getSpecialAttr('__or__')(*args)
        
    def __xor__(self, *args):
        return self._getSpecialAttr('__xor__')(*args)
        
    def __iand__(self, *args):
        return self._getSpecialAttr('__iand__')(*args, _callSync='off')
        
    def __ior__(self, *args):
        return self._getSpecialAttr('__ior__')(*args, _callSync='off')
        
    def __ixor__(self, *args):
        return self._getSpecialAttr('__ixor__')(*args, _callSync='off')
        
    def __mod__(self, *args):
        return self._getSpecialAttr('__mod__')(*args)
        
    def __radd__(self, *args):
        return self._getSpecialAttr('__radd__')(*args)
    
    def __rsub__(self, *args):
        return self._getSpecialAttr('__rsub__')(*args)
        
    def __rdiv__(self, *args):
        return self._getSpecialAttr('__rdiv__')(*args)
        
    def __rfloordiv__(self, *args):
        return self._getSpecialAttr('__rfloordiv__')(*args)
        
    def __rtruediv__(self, *args):
        return self._getSpecialAttr('__rtruediv__')(*args)
        
    def __rmul__(self, *args):
        return self._getSpecialAttr('__rmul__')(*args)
        
    def __rpow__(self, *args):
        return self._getSpecialAttr('__rpow__')(*args)
        
    def __rrshift__(self, *args):
        return self._getSpecialAttr('__rrshift__')(*args)
        
    def __rlshift__(self, *args):
        return self._getSpecialAttr('__rlshift__')(*args)
        
    def __rand__(self, *args):
        return self._getSpecialAttr('__rand__')(*args)
        
    def __ror__(self, *args):
        return self._getSpecialAttr('__ror__')(*args)
        
    def __rxor__(self, *args):
        return self._getSpecialAttr('__ror__')(*args)
        
    def __rmod__(self, *args):
        return self._getSpecialAttr('__rmod__')(*args)
        
    def __hash__(self):
        ## Required for python3 since __eq__ is defined.
        return id(self)
        
class DeferredObjectProxy(ObjectProxy):
    """
    This class represents an attribute (or sub-attribute) of a proxied object.
    It is used to speed up attribute requests. Take the following scenario::
    
        rsys = proc._import('sys')
        rsys.stdout.write('hello')
        
    For this simple example, a total of 4 synchronous requests are made to 
    the remote process: 
    
    1) import sys
    2) getattr(sys, 'stdout')
    3) getattr(stdout, 'write')
    4) write('hello')
    
    This takes a lot longer than running the equivalent code locally. To
    speed things up, we can 'defer' the two attribute lookups so they are
    only carried out when neccessary::
    
        rsys = proc._import('sys')
        rsys._setProxyOptions(deferGetattr=True)
        rsys.stdout.write('hello')
        
    This example only makes two requests to the remote process; the two 
    attribute lookups immediately return DeferredObjectProxy instances 
    immediately without contacting the remote process. When the call 
    to write() is made, all attribute requests are processed at the same time.
    
    Note that if the attributes requested do not exist on the remote object, 
    making the call to write() will raise an AttributeError.
    """
    def __init__(self, parentProxy, attribute):
        ## can't set attributes directly because setattr is overridden.
        for k in ['_processId', '_typeStr', '_proxyId', '_handler']:
            self.__dict__[k] = getattr(parentProxy, k)
        self.__dict__['_parent'] = parentProxy  ## make sure parent stays alive
        self.__dict__['_attributes'] = parentProxy._attributes + (attribute,)
        self.__dict__['_proxyOptions'] = parentProxy._proxyOptions.copy()
    
    def __repr__(self):
        return ObjectProxy.__repr__(self) + '.' + '.'.join(self._attributes)
    
    def _undefer(self):
        """
        Return a non-deferred ObjectProxy referencing the same object
        """
        return self._parent.__getattr__(self._attributes[-1], _deferGetattr=False)

