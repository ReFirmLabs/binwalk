# -*- coding: utf-8 -*-
"""This module installs a wrapper around sys.excepthook which allows multiple
new exception handlers to be registered. 

Optionally, the wrapper also stops exceptions from causing long-term storage 
of local stack frames. This has two major effects:
  - Unhandled exceptions will no longer cause memory leaks
    (If an exception occurs while a lot of data is present on the stack, 
    such as when loading large files, the data would ordinarily be kept
    until the next exception occurs. We would rather release this memory 
    as soon as possible.)
  - Some debuggers may have a hard time handling uncaught exceptions
 
The module also provides a callback mechanism allowing others to respond 
to exceptions.
"""

import sys, time
#from lib.Manager import logMsg
import traceback
#from log import *

#logging = False

callbacks = []
clear_tracebacks = False

def register(fn):
    """
    Register a callable to be invoked when there is an unhandled exception.
    The callback will be passed the output of sys.exc_info(): (exception type, exception, traceback)
    Multiple callbacks will be invoked in the order they were registered.
    """
    callbacks.append(fn)
    
def unregister(fn):
    """Unregister a previously registered callback."""
    callbacks.remove(fn)

def setTracebackClearing(clear=True):
    """
    Enable or disable traceback clearing.
    By default, clearing is disabled and Python will indefinitely store unhandled exception stack traces.
    This function is provided since Python's default behavior can cause unexpected retention of 
    large memory-consuming objects.
    """
    global clear_tracebacks
    clear_tracebacks = clear
    
class ExceptionHandler(object):
    def __call__(self, *args):
        ## call original exception handler first (prints exception)
        global original_excepthook, callbacks, clear_tracebacks
        print("===== %s =====" % str(time.strftime("%Y.%m.%d %H:%m:%S", time.localtime(time.time()))))
        ret = original_excepthook(*args)
        
        for cb in callbacks:
            try:
                cb(*args)
            except:
                print("   --------------------------------------------------------------")
                print("      Error occurred during exception callback %s" % str(cb))
                print("   --------------------------------------------------------------")
                traceback.print_exception(*sys.exc_info())
            
        
        ## Clear long-term storage of last traceback to prevent memory-hogging.
        ## (If an exception occurs while a lot of data is present on the stack, 
        ## such as when loading large files, the data would ordinarily be kept
        ## until the next exception occurs. We would rather release this memory 
        ## as soon as possible.)
        if clear_tracebacks is True:
            sys.last_traceback = None           

    def implements(self, interface=None):
        ## this just makes it easy for us to detect whether an ExceptionHook is already installed.
        if interface is None:
            return ['ExceptionHandler']
        else:
            return interface == 'ExceptionHandler'
    


## replace built-in excepthook only if this has not already been done
if not (hasattr(sys.excepthook, 'implements') and sys.excepthook.implements('ExceptionHandler')):
    original_excepthook = sys.excepthook
    sys.excepthook = ExceptionHandler()



