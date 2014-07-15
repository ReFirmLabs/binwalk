# -*- coding: utf-8 -*-
"""
Magic Reload Library
Luke Campagnola   2010

Python reload function that actually works (the way you expect it to)
 - No re-importing necessary
 - Modules can be reloaded in any order
 - Replaces functions and methods with their updated code
 - Changes instances to use updated classes
 - Automatically decides which modules to update by comparing file modification times
 
Does NOT:
 - re-initialize exting instances, even if __init__ changes
 - update references to any module-level objects
   ie, this does not reload correctly:
       from module import someObject
       print someObject
   ..but you can use this instead: (this works even for the builtin reload)
       import module
       print module.someObject
"""


import inspect, os, sys, gc, traceback
try:
    import __builtin__ as builtins
except ImportError:
    import builtins
from .debug import printExc

def reloadAll(prefix=None, debug=False):
    """Automatically reload everything whose __file__ begins with prefix.
    - Skips reload if the file has not been updated (if .pyc is newer than .py)
    - if prefix is None, checks all loaded modules
    """
    failed = []
    changed = []
    for modName, mod in list(sys.modules.items()):  ## don't use iteritems; size may change during reload
        if not inspect.ismodule(mod):
            continue
        if modName == '__main__':
            continue
        
        ## Ignore if the file name does not start with prefix
        if not hasattr(mod, '__file__') or os.path.splitext(mod.__file__)[1] not in ['.py', '.pyc']:
            continue
        if prefix is not None and mod.__file__[:len(prefix)] != prefix:
            continue
        
        ## ignore if the .pyc is newer than the .py (or if there is no pyc or py)
        py = os.path.splitext(mod.__file__)[0] + '.py'
        pyc = py + 'c'
        if py not in changed and os.path.isfile(pyc) and os.path.isfile(py) and os.stat(pyc).st_mtime >= os.stat(py).st_mtime:
            #if debug:
                #print "Ignoring module %s; unchanged" % str(mod)
            continue
        changed.append(py)  ## keep track of which modules have changed to insure that duplicate-import modules get reloaded.
        
        try:
            reload(mod, debug=debug)
        except:
            printExc("Error while reloading module %s, skipping\n" % mod)
            failed.append(mod.__name__)
        
    if len(failed) > 0:
        raise Exception("Some modules failed to reload: %s" % ', '.join(failed))

def reload(module, debug=False, lists=False, dicts=False):
    """Replacement for the builtin reload function:
    - Reloads the module as usual
    - Updates all old functions and class methods to use the new code
    - Updates all instances of each modified class to use the new class
    - Can update lists and dicts, but this is disabled by default
    - Requires that class and function names have not changed
    """
    if debug:
        print("Reloading %s" % str(module))
        
    ## make a copy of the old module dictionary, reload, then grab the new module dictionary for comparison
    oldDict = module.__dict__.copy()
    builtins.reload(module)
    newDict = module.__dict__
    
    ## Allow modules access to the old dictionary after they reload
    if hasattr(module, '__reload__'):
        module.__reload__(oldDict)
    
    ## compare old and new elements from each dict; update where appropriate
    for k in oldDict:
        old = oldDict[k]
        new = newDict.get(k, None)
        if old is new or new is None:
            continue
        
        if inspect.isclass(old):
            if debug:
                print("  Updating class %s.%s (0x%x -> 0x%x)" % (module.__name__, k, id(old), id(new)))
            updateClass(old, new, debug)
                    
        elif inspect.isfunction(old):
            depth = updateFunction(old, new, debug)
            if debug:
                extra = ""
                if depth > 0:
                    extra = " (and %d previous versions)" % depth
                print("  Updating function %s.%s%s" % (module.__name__, k, extra))
        elif lists and isinstance(old, list):
            l = old.len()
            old.extend(new)
            for i in range(l):
                old.pop(0)
        elif dicts and isinstance(old, dict):
            old.update(new)
            for k in old:
                if k not in new:
                    del old[k]
        


## For functions:
##  1) update the code and defaults to new versions.
##  2) keep a reference to the previous version so ALL versions get updated for every reload
def updateFunction(old, new, debug, depth=0, visited=None):
    #if debug and depth > 0:
        #print "    -> also updating previous version", old, " -> ", new
        
    old.__code__ = new.__code__
    old.__defaults__ = new.__defaults__
    
    if visited is None:
        visited = []
    if old in visited:
        return
    visited.append(old)
    
    ## finally, update any previous versions still hanging around..
    if hasattr(old, '__previous_reload_version__'):
        maxDepth = updateFunction(old.__previous_reload_version__, new, debug, depth=depth+1, visited=visited)
    else:
        maxDepth = depth
        
    ## We need to keep a pointer to the previous version so we remember to update BOTH
    ## when the next reload comes around.
    if depth == 0:
        new.__previous_reload_version__ = old
    return maxDepth



## For classes:
##  1) find all instances of the old class and set instance.__class__ to the new class
##  2) update all old class methods to use code from the new class methods
def updateClass(old, new, debug):

    ## Track town all instances and subclasses of old
    refs = gc.get_referrers(old)
    for ref in refs:
        try:
            if isinstance(ref, old) and ref.__class__ is old:
                ref.__class__ = new
                if debug:
                    print("    Changed class for %s" % safeStr(ref))
            elif inspect.isclass(ref) and issubclass(ref, old) and old in ref.__bases__:
                ind = ref.__bases__.index(old)
                
                ## Does not work:
                #ref.__bases__ = ref.__bases__[:ind] + (new,) + ref.__bases__[ind+1:]
                ## reason: Even though we change the code on methods, they remain bound
                ## to their old classes (changing im_class is not allowed). Instead,
                ## we have to update the __bases__ such that this class will be allowed
                ## as an argument to older methods.
                
                ## This seems to work. Is there any reason not to?
                ## Note that every time we reload, the class hierarchy becomes more complex.
                ## (and I presume this may slow things down?)
                ref.__bases__ = ref.__bases__[:ind] + (new,old) + ref.__bases__[ind+1:]
                if debug:
                    print("    Changed superclass for %s" % safeStr(ref))
            #else:
                #if debug:
                    #print "    Ignoring reference", type(ref)
        except:
            print("Error updating reference (%s) for class change (%s -> %s)" % (safeStr(ref), safeStr(old), safeStr(new)))
            raise
        
    ## update all class methods to use new code.
    ## Generally this is not needed since instances already know about the new class, 
    ## but it fixes a few specific cases (pyqt signals, for one)
    for attr in dir(old):
        oa = getattr(old, attr)
        if inspect.ismethod(oa):
            try:
                na = getattr(new, attr)
            except AttributeError:
                if debug:
                    print("    Skipping method update for %s; new class does not have this attribute" % attr)
                continue
                
            if hasattr(oa, 'im_func') and hasattr(na, 'im_func') and oa.__func__ is not na.__func__:
                depth = updateFunction(oa.__func__, na.__func__, debug)
                #oa.im_class = new  ## bind old method to new class  ## not allowed
                if debug:
                    extra = ""
                    if depth > 0:
                        extra = " (and %d previous versions)" % depth
                    print("    Updating method %s%s" % (attr, extra))
                
    ## And copy in new functions that didn't exist previously
    for attr in dir(new):
        if not hasattr(old, attr):
            if debug:
                print("    Adding missing attribute %s" % attr)
            setattr(old, attr, getattr(new, attr))
            
    ## finally, update any previous versions still hanging around..
    if hasattr(old, '__previous_reload_version__'):
        updateClass(old.__previous_reload_version__, new, debug)


## It is possible to build classes for which str(obj) just causes an exception.
## Avoid thusly:
def safeStr(obj):
    try:
        s = str(obj)
    except:
        try:
            s = repr(obj)
        except:
            s = "<instance of %s at 0x%x>" % (safeStr(type(obj)), id(obj))
    return s





## Tests:
#  write modules to disk, import, then re-write and run again
if __name__ == '__main__':
    doQtTest = True
    try:
        from PyQt4 import QtCore
        if not hasattr(QtCore, 'Signal'):
            QtCore.Signal = QtCore.pyqtSignal
        #app = QtGui.QApplication([])
        class Btn(QtCore.QObject):
            sig = QtCore.Signal()
            def emit(self):
                self.sig.emit()
        btn = Btn()
    except:
        raise
        print("Error; skipping Qt tests")
        doQtTest = False



    import os
    if not os.path.isdir('test1'):
        os.mkdir('test1')
    open('test1/__init__.py', 'w')
    modFile1 = "test1/test1.py"
    modCode1 = """
import sys
class A(object):
    def __init__(self, msg):
        object.__init__(self)
        self.msg = msg
    def fn(self, pfx = ""):
        print(pfx+"A class: %%s %%s" %% (str(self.__class__), str(id(self.__class__))))
        print(pfx+"  %%s: %d" %% self.msg)

class B(A):
    def fn(self, pfx=""):
        print(pfx+"B class:", self.__class__, id(self.__class__))
        print(pfx+"  %%s: %d" %% self.msg)
        print(pfx+"  calling superclass.. (%%s)" %% id(A) )
        A.fn(self, "  ")
"""

    modFile2 = "test2.py"
    modCode2 = """
from test1.test1 import A
from test1.test1 import B

a1 = A("ax1")
b1 = B("bx1")
class C(A):
    def __init__(self, msg):
        #print "| C init:"
        #print "|   C.__bases__ = ", map(id, C.__bases__)
        #print "|   A:", id(A)
        #print "|   A.__init__ = ", id(A.__init__.im_func), id(A.__init__.im_func.__code__), id(A.__init__.im_class)
        A.__init__(self, msg + "(init from C)")
        
def fn():
    print("fn: %s")
""" 

    open(modFile1, 'w').write(modCode1%(1,1))
    open(modFile2, 'w').write(modCode2%"message 1")
    import test1.test1 as test1
    import test2
    print("Test 1 originals:")
    A1 = test1.A
    B1 = test1.B
    a1 = test1.A("a1")
    b1 = test1.B("b1")
    a1.fn()
    b1.fn()
    #print "function IDs  a1 bound method: %d a1 func: %d  a1 class: %d  b1 func: %d  b1 class: %d" % (id(a1.fn), id(a1.fn.im_func), id(a1.fn.im_class), id(b1.fn.im_func), id(b1.fn.im_class))


    from test2 import fn, C
    
    if doQtTest:
        print("Button test before:")
        btn.sig.connect(fn)
        btn.sig.connect(a1.fn)
        btn.emit()
        #btn.sig.emit()
        print("")
    
    #print "a1.fn referrers:", sys.getrefcount(a1.fn.im_func), gc.get_referrers(a1.fn.im_func)
    
    
    print("Test2 before reload:")
    
    fn()
    oldfn = fn
    test2.a1.fn()
    test2.b1.fn()
    c1 = test2.C('c1')
    c1.fn()
    
    os.remove(modFile1+'c')
    open(modFile1, 'w').write(modCode1%(2,2))
    print("\n----RELOAD test1-----\n")
    reloadAll(os.path.abspath(__file__)[:10], debug=True)
    
    
    print("Subclass test:")
    c2 = test2.C('c2')
    c2.fn()
    
    
    os.remove(modFile2+'c')
    open(modFile2, 'w').write(modCode2%"message 2")
    print("\n----RELOAD test2-----\n")
    reloadAll(os.path.abspath(__file__)[:10], debug=True)

    if doQtTest:
        print("Button test after:")
        btn.emit()
        #btn.sig.emit()

    #print "a1.fn referrers:", sys.getrefcount(a1.fn.im_func), gc.get_referrers(a1.fn.im_func)

    print("Test2 after reload:")
    fn()
    test2.a1.fn()
    test2.b1.fn()
    
    print("\n==> Test 1 Old instances:")
    a1.fn()
    b1.fn()
    c1.fn()
    #print "function IDs  a1 bound method: %d a1 func: %d  a1 class: %d  b1 func: %d  b1 class: %d" % (id(a1.fn), id(a1.fn.im_func), id(a1.fn.im_class), id(b1.fn.im_func), id(b1.fn.im_class))

    print("\n==> Test 1 New instances:")
    a2 = test1.A("a2")
    b2 = test1.B("b2")
    a2.fn()
    b2.fn()
    c2 = test2.C('c2')
    c2.fn()
    #print "function IDs  a1 bound method: %d a1 func: %d  a1 class: %d  b1 func: %d  b1 class: %d" % (id(a1.fn), id(a1.fn.im_func), id(a1.fn.im_class), id(b1.fn.im_func), id(b1.fn.im_class))




    os.remove(modFile1+'c')
    os.remove(modFile2+'c')
    open(modFile1, 'w').write(modCode1%(3,3))
    open(modFile2, 'w').write(modCode2%"message 3")
    
    print("\n----RELOAD-----\n")
    reloadAll(os.path.abspath(__file__)[:10], debug=True)

    if doQtTest:
        print("Button test after:")
        btn.emit()
        #btn.sig.emit()

    #print "a1.fn referrers:", sys.getrefcount(a1.fn.im_func), gc.get_referrers(a1.fn.im_func)

    print("Test2 after reload:")
    fn()
    test2.a1.fn()
    test2.b1.fn()
    
    print("\n==> Test 1 Old instances:")
    a1.fn()
    b1.fn()
    print("function IDs  a1 bound method: %d a1 func: %d  a1 class: %d  b1 func: %d  b1 class: %d" % (id(a1.fn), id(a1.fn.__func__), id(a1.fn.__self__.__class__), id(b1.fn.__func__), id(b1.fn.__self__.__class__)))

    print("\n==> Test 1 New instances:")
    a2 = test1.A("a2")
    b2 = test1.B("b2")
    a2.fn()
    b2.fn()
    print("function IDs  a1 bound method: %d a1 func: %d  a1 class: %d  b1 func: %d  b1 class: %d" % (id(a1.fn), id(a1.fn.__func__), id(a1.fn.__self__.__class__), id(b1.fn.__func__), id(b1.fn.__self__.__class__)))


    os.remove(modFile1)
    os.remove(modFile2)
    os.remove(modFile1+'c')
    os.remove(modFile2+'c')
    os.system('rm -r test1')








#
#        Failure graveyard ahead:
#


"""Reload Importer:
Hooks into import system to 
1) keep a record of module dependencies as they are imported
2) make sure modules are always reloaded in correct order
3) update old classes and functions to use reloaded code"""

#import imp, sys

## python's import hook mechanism doesn't work since we need to be 
## informed every time there is an import statement, not just for new imports
#class ReloadImporter:
    #def __init__(self):
        #self.depth = 0
        
    #def find_module(self, name, path):
        #print "  "*self.depth + "find: ", name, path
        ##if name == 'PyQt4' and path is None:
            ##print "PyQt4 -> PySide"
            ##self.modData = imp.find_module('PySide')
            ##return self
        ##return None ## return none to allow the import to proceed normally; return self to intercept with load_module
        #self.modData = imp.find_module(name, path)
        #self.depth += 1
        ##sys.path_importer_cache = {}
        #return self
        
    #def load_module(self, name):
        #mod =  imp.load_module(name, *self.modData)
        #self.depth -= 1
        #print "  "*self.depth + "load: ", name
        #return mod

#def pathHook(path):
    #print "path hook:", path
    #raise ImportError
#sys.path_hooks.append(pathHook)

#sys.meta_path.append(ReloadImporter())


### replace __import__ with a wrapper that tracks module dependencies
#modDeps = {}
#reloadModule = None
#origImport = __builtins__.__import__
#def _import(name, globals=None, locals=None, fromlist=None, level=-1, stack=[]):
    ### Note that stack behaves as a static variable.
    ##print "  "*len(importStack) + "import %s" % args[0]
    #stack.append(set())
    #mod = origImport(name, globals, locals, fromlist, level)
    #deps = stack.pop()
    #if len(stack) > 0:
        #stack[-1].add(mod)
    #elif reloadModule is not None:     ## If this is the top level import AND we're inside a module reload
        #modDeps[reloadModule].add(mod)
            
    #if mod in modDeps:
        #modDeps[mod] |= deps
    #else:
        #modDeps[mod] = deps
        
    
    #return mod
    
#__builtins__.__import__ = _import

### replace 
#origReload = __builtins__.reload
#def _reload(mod):
    #reloadModule = mod
    #ret = origReload(mod)
    #reloadModule = None
    #return ret
#__builtins__.reload = _reload


#def reload(mod, visited=None):
    #if visited is None:
        #visited = set()
    #if mod in visited:
        #return
    #visited.add(mod)
    #for dep in modDeps.get(mod, []):
        #reload(dep, visited)
    #__builtins__.reload(mod)
