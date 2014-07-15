# -*- coding: utf-8 -*-
"""
PyQtGraph - Scientific Graphics and GUI Library for Python
www.pyqtgraph.org
"""

__version__ = '0.9.8'

### import all the goodies and add some helper functions for easy CLI use

## 'Qt' is a local module; it is intended mainly to cover up the differences
## between PyQt4 and PySide.
from .Qt import QtGui

## not really safe--If we accidentally create another QApplication, the process hangs (and it is very difficult to trace the cause)
#if QtGui.QApplication.instance() is None:
    #app = QtGui.QApplication([])

import numpy  ## pyqtgraph requires numpy
              ## (import here to avoid massive error dump later on if numpy is not available)

import os, sys

## check python version
## Allow anything >= 2.7
if sys.version_info[0] < 2 or (sys.version_info[0] == 2 and sys.version_info[1] < 6):
    raise Exception("Pyqtgraph requires Python version 2.6 or greater (this is %d.%d)" % (sys.version_info[0], sys.version_info[1]))

## helpers for 2/3 compatibility
from . import python2_3

## install workarounds for numpy bugs
from . import numpy_fix

## in general openGL is poorly supported with Qt+GraphicsView.
## we only enable it where the performance benefit is critical.
## Note this only applies to 2D graphics; 3D graphics always use OpenGL.
if 'linux' in sys.platform:  ## linux has numerous bugs in opengl implementation
    useOpenGL = False
elif 'darwin' in sys.platform: ## openGL can have a major impact on mac, but also has serious bugs
    useOpenGL = False
    if QtGui.QApplication.instance() is not None:
        print('Warning: QApplication was created before pyqtgraph was imported; there may be problems (to avoid bugs, call QApplication.setGraphicsSystem("raster") before the QApplication is created).')
    QtGui.QApplication.setGraphicsSystem('raster')  ## work around a variety of bugs in the native graphics system 
else:
    useOpenGL = False  ## on windows there's a more even performance / bugginess tradeoff. 
                
CONFIG_OPTIONS = {
    'useOpenGL': useOpenGL, ## by default, this is platform-dependent (see widgets/GraphicsView). Set to True or False to explicitly enable/disable opengl.
    'leftButtonPan': True,  ## if false, left button drags a rubber band for zooming in viewbox
    'foreground': (150, 150, 150),  ## default foreground color for axes, labels, etc.
    'background': (0, 0, 0),        ## default background for GraphicsWidget
    'antialias': False,
    'editorCommand': None,  ## command used to invoke code editor from ConsoleWidgets
    'useWeave': True,       ## Use weave to speed up some operations, if it is available
    'weaveDebug': False,    ## Print full error message if weave compile fails
    'exitCleanup': True,    ## Attempt to work around some exit crash bugs in PyQt and PySide
    'enableExperimental': False, ## Enable experimental features (the curious can search for this key in the code)
} 


def setConfigOption(opt, value):
    CONFIG_OPTIONS[opt] = value

def setConfigOptions(**opts):
    CONFIG_OPTIONS.update(opts)

def getConfigOption(opt):
    return CONFIG_OPTIONS[opt]


def systemInfo():
    print("sys.platform: %s" % sys.platform)
    print("sys.version: %s" % sys.version)
    from .Qt import VERSION_INFO
    print("qt bindings: %s" % VERSION_INFO)
    
    global __version__
    rev = None
    if __version__ is None:  ## this code was probably checked out from bzr; look up the last-revision file
        lastRevFile = os.path.join(os.path.dirname(__file__), '..', '.bzr', 'branch', 'last-revision')
        if os.path.exists(lastRevFile):
            rev = open(lastRevFile, 'r').read().strip()
    
    print("pyqtgraph: %s; %s" % (__version__, rev))
    print("config:")
    import pprint
    pprint.pprint(CONFIG_OPTIONS)

## Rename orphaned .pyc files. This is *probably* safe :)
## We only do this if __version__ is None, indicating the code was probably pulled
## from the repository. 
def renamePyc(startDir):
    ### Used to rename orphaned .pyc files
    ### When a python file changes its location in the repository, usually the .pyc file
    ### is left behind, possibly causing mysterious and difficult to track bugs. 

    ### Note that this is no longer necessary for python 3.2; from PEP 3147:
    ### "If the py source file is missing, the pyc file inside __pycache__ will be ignored. 
    ### This eliminates the problem of accidental stale pyc file imports."
    
    printed = False
    startDir = os.path.abspath(startDir)
    for path, dirs, files in os.walk(startDir):
        if '__pycache__' in path:
            continue
        for f in files:
            fileName = os.path.join(path, f)
            base, ext = os.path.splitext(fileName)
            py = base + ".py"
            if ext == '.pyc' and not os.path.isfile(py):
                if not printed:
                    print("NOTE: Renaming orphaned .pyc files:")
                    printed = True
                n = 1
                while True:
                    name2 = fileName + ".renamed%d" % n
                    if not os.path.exists(name2):
                        break
                    n += 1
                print("  " + fileName + "  ==>")
                print("  " + name2)
                os.rename(fileName, name2)
                
path = os.path.split(__file__)[0]
if __version__ is None and not hasattr(sys, 'frozen') and sys.version_info[0] == 2: ## If we are frozen, there's a good chance we don't have the original .py files anymore.
    renamePyc(path)


## Import almost everything to make it available from a single namespace
## don't import the more complex systems--canvas, parametertree, flowchart, dockarea
## these must be imported separately.
from . import frozenSupport
def importModules(path, globals, locals, excludes=()):
    """Import all modules residing within *path*, return a dict of name: module pairs.
    
    Note that *path* MUST be relative to the module doing the import.    
    """
    d = os.path.join(os.path.split(globals['__file__'])[0], path)
    files = set()
    for f in frozenSupport.listdir(d):
        if frozenSupport.isdir(os.path.join(d, f)) and f not in ['__pycache__', 'tests']:
            files.add(f)
        elif f[-3:] == '.py' and f != '__init__.py':
            files.add(f[:-3])
        elif f[-4:] == '.pyc' and f != '__init__.pyc':
            files.add(f[:-4])
        
    mods = {}
    path = path.replace(os.sep, '.')
    for modName in files:
        if modName in excludes:
            continue
        try:
            if len(path) > 0:
                modName = path + '.' + modName
            #mod = __import__(modName, globals, locals, fromlist=['*'])
            mod = __import__(modName, globals, locals, ['*'], 1)
            mods[modName] = mod
        except:
            import traceback
            traceback.print_stack()
            sys.excepthook(*sys.exc_info())
            print("[Error importing module: %s]" % modName)
            
    return mods

def importAll(path, globals, locals, excludes=()):
    """Given a list of modules, import all names from each module into the global namespace."""
    mods = importModules(path, globals, locals, excludes)
    for mod in mods.values():
        if hasattr(mod, '__all__'):
            names = mod.__all__
        else:
            names = [n for n in dir(mod) if n[0] != '_']
        for k in names:
            if hasattr(mod, k):
                globals[k] = getattr(mod, k)

importAll('graphicsItems', globals(), locals())
importAll('widgets', globals(), locals(),
          excludes=['MatplotlibWidget', 'RawImageWidget', 'RemoteGraphicsView'])

from .imageview import *
from .WidgetGroup import *
from .Point import Point
from .Vector import Vector
from .SRTTransform import SRTTransform
from .Transform3D import Transform3D
from .SRTTransform3D import SRTTransform3D
from .functions import *
from .graphicsWindows import *
from .SignalProxy import *
from .colormap import *
from .ptime import time

##############################################################
## PyQt and PySide both are prone to crashing on exit. 
## There are two general approaches to dealing with this:
##  1. Install atexit handlers that assist in tearing down to avoid crashes.
##     This helps, but is never perfect.
##  2. Terminate the process before python starts tearing down
##     This is potentially dangerous

## Attempts to work around exit crashes:
import atexit
def cleanup():
    if not getConfigOption('exitCleanup'):
        return
    
    ViewBox.quit()  ## tell ViewBox that it doesn't need to deregister views anymore.
    
    ## Workaround for Qt exit crash:
    ## ALL QGraphicsItems must have a scene before they are deleted.
    ## This is potentially very expensive, but preferred over crashing.
    ## Note: this appears to be fixed in PySide as of 2012.12, but it should be left in for a while longer..
    if QtGui.QApplication.instance() is None:
        return
    import gc
    s = QtGui.QGraphicsScene()
    for o in gc.get_objects():
        try:
            if isinstance(o, QtGui.QGraphicsItem) and o.scene() is None:
                s.addItem(o)
        except RuntimeError:  ## occurs if a python wrapper no longer has its underlying C++ object
            continue
atexit.register(cleanup)


## Optional function for exiting immediately (with some manual teardown)
def exit():
    """
    Causes python to exit without garbage-collecting any objects, and thus avoids
    calling object destructor methods. This is a sledgehammer workaround for 
    a variety of bugs in PyQt and Pyside that cause crashes on exit.
    
    This function does the following in an attempt to 'safely' terminate
    the process:
    
    * Invoke atexit callbacks
    * Close all open file handles
    * os._exit()
    
    Note: there is some potential for causing damage with this function if you
    are using objects that _require_ their destructors to be called (for example,
    to properly terminate log files, disconnect from devices, etc). Situations
    like this are probably quite rare, but use at your own risk.
    """
    
    ## first disable our own cleanup function; won't be needing it.
    setConfigOptions(exitCleanup=False)
    
    ## invoke atexit callbacks
    atexit._run_exitfuncs()
    
    ## close file handles
    os.closerange(3, 4096) ## just guessing on the maximum descriptor count..
    
    os._exit(0)
    


## Convenience functions for command-line use

plots = []
images = []
QAPP = None

def plot(*args, **kargs):
    """
    Create and return a :class:`PlotWindow <pyqtgraph.PlotWindow>` 
    (this is just a window with :class:`PlotWidget <pyqtgraph.PlotWidget>` inside), plot data in it.
    Accepts a *title* argument to set the title of the window.
    All other arguments are used to plot data. (see :func:`PlotItem.plot() <pyqtgraph.PlotItem.plot>`)
    """
    mkQApp()
    #if 'title' in kargs:
        #w = PlotWindow(title=kargs['title'])
        #del kargs['title']
    #else:
        #w = PlotWindow()
    #if len(args)+len(kargs) > 0:
        #w.plot(*args, **kargs)
        
    pwArgList = ['title', 'labels', 'name', 'left', 'right', 'top', 'bottom', 'background']
    pwArgs = {}
    dataArgs = {}
    for k in kargs:
        if k in pwArgList:
            pwArgs[k] = kargs[k]
        else:
            dataArgs[k] = kargs[k]
        
    w = PlotWindow(**pwArgs)
    w.plot(*args, **dataArgs)
    plots.append(w)
    w.show()
    return w
    
def image(*args, **kargs):
    """
    Create and return an :class:`ImageWindow <pyqtgraph.ImageWindow>` 
    (this is just a window with :class:`ImageView <pyqtgraph.ImageView>` widget inside), show image data inside.
    Will show 2D or 3D image data.
    Accepts a *title* argument to set the title of the window.
    All other arguments are used to show data. (see :func:`ImageView.setImage() <pyqtgraph.ImageView.setImage>`)
    """
    mkQApp()
    w = ImageWindow(*args, **kargs)
    images.append(w)
    w.show()
    return w
show = image  ## for backward compatibility

def dbg(*args, **kwds):
    """
    Create a console window and begin watching for exceptions.
    
    All arguments are passed to :func:`ConsoleWidget.__init__() <pyqtgraph.console.ConsoleWidget.__init__>`.
    """
    mkQApp()
    from . import console
    c = console.ConsoleWidget(*args, **kwds)
    c.catchAllExceptions()
    c.show()
    global consoles
    try:
        consoles.append(c)
    except NameError:
        consoles = [c]
    
    
def mkQApp():
    global QAPP
    inst = QtGui.QApplication.instance()
    if inst is None:
        QAPP = QtGui.QApplication([])
    else:
        QAPP = inst
    return QAPP
        
