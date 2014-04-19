# -*- coding: utf-8 -*-
"""
debug.py - Functions to aid in debugging 
Copyright 2010  Luke Campagnola
Distributed under MIT/X11 license. See license.txt for more infomation.
"""

import sys, traceback, time, gc, re, types, weakref, inspect, os, cProfile
from . import ptime
from numpy import ndarray
from .Qt import QtCore, QtGui

__ftraceDepth = 0
def ftrace(func):
    """Decorator used for marking the beginning and end of function calls.
    Automatically indents nested calls.
    """
    def w(*args, **kargs):
        global __ftraceDepth
        pfx = "  " * __ftraceDepth
        print(pfx + func.__name__ + " start")
        __ftraceDepth += 1
        try:
            rv = func(*args, **kargs)
        finally:
            __ftraceDepth -= 1
        print(pfx + func.__name__ + " done")
        return rv
    return w

def warnOnException(func):
    """Decorator which catches/ignores exceptions and prints a stack trace."""
    def w(*args, **kwds):
        try:
            func(*args, **kwds)
        except:
            printExc('Ignored exception:')
    return w

def getExc(indent=4, prefix='|  '):
    tb = traceback.format_exc()
    lines = []
    for l in tb.split('\n'):        
        lines.append(" "*indent + prefix + l)
    return '\n'.join(lines)

def printExc(msg='', indent=4, prefix='|'):
    """Print an error message followed by an indented exception backtrace
    (This function is intended to be called within except: blocks)"""
    exc = getExc(indent, prefix + '  ')
    print("[%s]  %s\n" % (time.strftime("%H:%M:%S"), msg))
    print(" "*indent + prefix + '='*30 + '>>')
    print(exc)
    print(" "*indent + prefix + '='*30 + '<<')
    
def printTrace(msg='', indent=4, prefix='|'):
    """Print an error message followed by an indented stack trace"""
    trace = backtrace(1)
    #exc = getExc(indent, prefix + '  ')
    print("[%s]  %s\n" % (time.strftime("%H:%M:%S"), msg))
    print(" "*indent + prefix + '='*30 + '>>')
    for line in trace.split('\n'):
        print(" "*indent + prefix + " " + line)
    print(" "*indent + prefix + '='*30 + '<<')
    

def backtrace(skip=0):
    return ''.join(traceback.format_stack()[:-(skip+1)])    
    
    
def listObjs(regex='Q', typ=None):
    """List all objects managed by python gc with class name matching regex.
    Finds 'Q...' classes by default."""
    if typ is not None:
        return [x for x in gc.get_objects() if isinstance(x, typ)]
    else:
        return [x for x in gc.get_objects() if re.match(regex, type(x).__name__)]
        

    
def findRefPath(startObj, endObj, maxLen=8, restart=True, seen={}, path=None, ignore=None):
    """Determine all paths of object references from startObj to endObj"""
    refs = []
    if path is None:
        path = [endObj]
    if ignore is None:
        ignore = {}
    ignore[id(sys._getframe())] = None
    ignore[id(path)] = None
    ignore[id(seen)] = None
    prefix = " "*(8-maxLen)
    #print prefix + str(map(type, path))
    prefix += " "
    if restart:
        #gc.collect()
        seen.clear()
    gc.collect()
    newRefs = [r for r in gc.get_referrers(endObj) if id(r) not in ignore]
    ignore[id(newRefs)] = None
    #fo = allFrameObjs()
    #newRefs = []
    #for r in gc.get_referrers(endObj):
        #try:
            #if r not in fo:
                #newRefs.append(r)
        #except:
            #newRefs.append(r)            
        
    for r in newRefs:
        #print prefix+"->"+str(type(r))
        if type(r).__name__ in ['frame', 'function', 'listiterator']:
            #print prefix+"  FRAME"
            continue
        try:
            if any([r is x for x in  path]):
                #print prefix+"  LOOP", objChainString([r]+path)
                continue
        except:
            print(r)
            print(path)
            raise
        if r is startObj:
            refs.append([r])
            print(refPathString([startObj]+path))
            continue
        if maxLen == 0:
            #print prefix+"  END:", objChainString([r]+path)
            continue
        ## See if we have already searched this node.
        ## If not, recurse.
        tree = None
        try:
            cache = seen[id(r)]
            if cache[0] >= maxLen:
                tree = cache[1]
                for p in tree:
                    print(refPathString(p+path))
        except KeyError:
            pass
        
        ignore[id(tree)] = None
        if tree is None:
            tree = findRefPath(startObj, r, maxLen-1, restart=False, path=[r]+path, ignore=ignore)
            seen[id(r)] = [maxLen, tree]
        ## integrate any returned results
        if len(tree) == 0:
            #print prefix+"  EMPTY TREE"
            continue
        else:
            for p in tree:
                refs.append(p+[r])
        #seen[id(r)] = [maxLen, refs]
    return refs


def objString(obj):
    """Return a short but descriptive string for any object"""
    try:
        if type(obj) in [int, float]:
            return str(obj)
        elif isinstance(obj, dict):
            if len(obj) > 5:
                return "<dict {%s,...}>" % (",".join(list(obj.keys())[:5]))
            else:
                return "<dict {%s}>" % (",".join(list(obj.keys())))
        elif isinstance(obj, str):
            if len(obj) > 50:
                return '"%s..."' % obj[:50]
            else:
                return obj[:]
        elif isinstance(obj, ndarray):
            return "<ndarray %s %s>" % (str(obj.dtype), str(obj.shape))
        elif hasattr(obj, '__len__'):
            if len(obj) > 5:
                return "<%s [%s,...]>" % (type(obj).__name__, ",".join([type(o).__name__ for o in obj[:5]]))
            else:
                return "<%s [%s]>" % (type(obj).__name__, ",".join([type(o).__name__ for o in obj]))
        else:
            return "<%s %s>" % (type(obj).__name__, obj.__class__.__name__)
    except:
        return str(type(obj))

def refPathString(chain):
    """Given a list of adjacent objects in a reference path, print the 'natural' path
    names (ie, attribute names, keys, and indexes) that follow from one object to the next ."""
    s = objString(chain[0])
    i = 0
    while i < len(chain)-1:
        #print " -> ", i
        i += 1
        o1 = chain[i-1]
        o2 = chain[i]
        cont = False
        if isinstance(o1, list) or isinstance(o1, tuple):
            if any([o2 is x for x in o1]):
                s += "[%d]" % o1.index(o2)
                continue
        #print "  not list"
        if isinstance(o2, dict) and hasattr(o1, '__dict__') and o2 == o1.__dict__:
            i += 1
            if i >= len(chain):
                s += ".__dict__"
                continue
            o3 = chain[i]
            for k in o2:
                if o2[k] is o3:
                    s += '.%s' % k
                    cont = True
                    continue
        #print "  not __dict__"
        if isinstance(o1, dict):
            try:
                if o2 in o1:
                    s += "[key:%s]" % objString(o2)
                    continue
            except TypeError:
                pass
            for k in o1:
                if o1[k] is o2:
                    s += "[%s]" % objString(k)
                    cont = True
                    continue
        #print "  not dict"
        #for k in dir(o1):  ## Not safe to request attributes like this.
            #if getattr(o1, k) is o2:
                #s += ".%s" % k
                #cont = True
                #continue
        #print "  not attr"
        if cont:
            continue
        s += " ? "
        sys.stdout.flush()
    return s

    
def objectSize(obj, ignore=None, verbose=False, depth=0, recursive=False):
    """Guess how much memory an object is using"""
    ignoreTypes = [types.MethodType, types.UnboundMethodType, types.BuiltinMethodType, types.FunctionType, types.BuiltinFunctionType]
    ignoreRegex = re.compile('(method-wrapper|Flag|ItemChange|Option|Mode)')
    
    
    if ignore is None:
        ignore = {}
        
    indent = '  '*depth
    
    try:
        hash(obj)
        hsh = obj
    except:
        hsh = "%s:%d" % (str(type(obj)), id(obj))
        
    if hsh in ignore:
        return 0
    ignore[hsh] = 1
    
    try:
        size = sys.getsizeof(obj)
    except TypeError:
        size = 0
        
    if isinstance(obj, ndarray):
        try:
            size += len(obj.data)
        except:
            pass
            
        
    if recursive:
        if type(obj) in [list, tuple]:
            if verbose:
                print(indent+"list:")
            for o in obj:
                s = objectSize(o, ignore=ignore, verbose=verbose, depth=depth+1)
                if verbose:
                    print(indent+'  +', s)
                size += s
        elif isinstance(obj, dict):
            if verbose:
                print(indent+"list:")
            for k in obj:
                s = objectSize(obj[k], ignore=ignore, verbose=verbose, depth=depth+1)
                if verbose:
                    print(indent+'  +', k, s)
                size += s
        #elif isinstance(obj, QtCore.QObject):
            #try:
                #childs = obj.children()
                #if verbose:
                    #print indent+"Qt children:"
                #for ch in childs:
                    #s = objectSize(obj, ignore=ignore, verbose=verbose, depth=depth+1)
                    #size += s
                    #if verbose:
                        #print indent + '  +', ch.objectName(), s
                    
            #except:
                #pass
    #if isinstance(obj, types.InstanceType):
        gc.collect()
        if verbose:
            print(indent+'attrs:')
        for k in dir(obj):
            if k in ['__dict__']:
                continue
            o = getattr(obj, k)
            if type(o) in ignoreTypes:
                continue
            strtyp = str(type(o))
            if ignoreRegex.search(strtyp):
                continue
            #if isinstance(o, types.ObjectType) and strtyp == "<type 'method-wrapper'>":
                #continue
            
            #if verbose:
                #print indent, k, '?'
            refs = [r for r in gc.get_referrers(o) if type(r) != types.FrameType]
            if len(refs) == 1:
                s = objectSize(o, ignore=ignore, verbose=verbose, depth=depth+1)
                size += s
                if verbose:
                    print(indent + "  +", k, s)
            #else:
                #if verbose:
                    #print indent + '  -', k, len(refs)
    return size

class GarbageWatcher(object):
    """
    Convenient dictionary for holding weak references to objects.
    Mainly used to check whether the objects have been collect yet or not.
    
    Example:
        gw = GarbageWatcher()
        gw['objName'] = obj
        gw['objName2'] = obj2
        gw.check()  
        
    
    """
    def __init__(self):
        self.objs = weakref.WeakValueDictionary()
        self.allNames = []
        
    def add(self, obj, name):
        self.objs[name] = obj
        self.allNames.append(name)
        
    def __setitem__(self, name, obj):
        self.add(obj, name)
        
    def check(self):
        """Print a list of all watched objects and whether they have been collected."""
        gc.collect()
        dead = self.allNames[:]
        alive = []
        for k in self.objs:
            dead.remove(k)
            alive.append(k)
        print("Deleted objects:", dead)
        print("Live objects:", alive)
        
    def __getitem__(self, item):
        return self.objs[item]

    
class Profiler:
    """Simple profiler allowing measurement of multiple time intervals.
    Arguments:
        msg: message to print at start and finish of profiling
        disabled: If true, profiler does nothing (so you can leave it in place)
        delayed: If true, all messages are printed after call to finish()
                 (this can result in more accurate time step measurements)
        globalDelay: if True, all nested profilers delay printing until the top level finishes
    
    Example:
        prof = Profiler('Function')
          ... do stuff ...
        prof.mark('did stuff')
          ... do other stuff ...
        prof.mark('did other stuff')
        prof.finish()
    """
    depth = 0
    msgs = []
    
    def __init__(self, msg="Profiler", disabled=False, delayed=True, globalDelay=True):
        self.disabled = disabled
        if disabled: 
            return
        
        self.markCount = 0
        self.finished = False
        self.depth = Profiler.depth 
        Profiler.depth += 1
        if not globalDelay:
            self.msgs = []
        self.delayed = delayed
        self.msg = "  "*self.depth + msg
        msg2 = self.msg + " >>> Started"
        if self.delayed:
            self.msgs.append(msg2)
        else:
            print(msg2)
        self.t0 = ptime.time()
        self.t1 = self.t0
    
    def mark(self, msg=None):
        if self.disabled: 
            return
        
        if msg is None:
            msg = str(self.markCount)
        self.markCount += 1
        
        t1 = ptime.time()
        msg2 = "  "+self.msg+" "+msg+" "+"%gms" % ((t1-self.t1)*1000)
        if self.delayed:
            self.msgs.append(msg2)
        else:
            print(msg2)
        self.t1 = ptime.time()  ## don't measure time it took to print
        
    def finish(self, msg=None):
        if self.disabled or self.finished: 
            return
        
        if msg is not None:
            self.mark(msg)
        t1 = ptime.time()
        msg = self.msg + ' <<< Finished, total time: %gms' % ((t1-self.t0)*1000)
        if self.delayed:
            self.msgs.append(msg)
            if self.depth == 0:
                for line in self.msgs:
                    print(line)
                Profiler.msgs = []
        else:
            print(msg)
        Profiler.depth = self.depth
        self.finished = True
        
            
        

def profile(code, name='profile_run', sort='cumulative', num=30):
    """Common-use for cProfile"""
    cProfile.run(code, name)
    stats = pstats.Stats(name)
    stats.sort_stats(sort)
    stats.print_stats(num)
    return stats
        
        
  
#### Code for listing (nearly) all objects in the known universe
#### http://utcc.utoronto.ca/~cks/space/blog/python/GetAllObjects
# Recursively expand slist's objects
# into olist, using seen to track
# already processed objects.
def _getr(slist, olist, first=True):
    i = 0 
    for e in slist:
        
        oid = id(e)
        typ = type(e)
        if oid in olist or typ is int:    ## or e in olist:     ## since we're excluding all ints, there is no longer a need to check for olist keys
            continue
        olist[oid] = e
        if first and (i%1000) == 0:
            gc.collect()
        tl = gc.get_referents(e)
        if tl:
            _getr(tl, olist, first=False)
        i += 1        
# The public function.
def get_all_objects():
    """Return a list of all live Python objects (excluding int and long), not including the list itself."""
    gc.collect()
    gcl = gc.get_objects()
    olist = {}
    _getr(gcl, olist)
    
    del olist[id(olist)]
    del olist[id(gcl)]
    del olist[id(sys._getframe())]
    return olist


def lookup(oid, objects=None):
    """Return an object given its ID, if it exists."""
    if objects is None:
        objects = get_all_objects()
    return objects[oid]
        
        
                    
        
class ObjTracker(object):
    """
    Tracks all objects under the sun, reporting the changes between snapshots: what objects are created, deleted, and persistent.
    This class is very useful for tracking memory leaks. The class goes to great (but not heroic) lengths to avoid tracking 
    its own internal objects.
    
    Example:
        ot = ObjTracker()   # takes snapshot of currently existing objects
           ... do stuff ...
        ot.diff()           # prints lists of objects created and deleted since ot was initialized
           ... do stuff ...
        ot.diff()           # prints lists of objects created and deleted since last call to ot.diff()
                            # also prints list of items that were created since initialization AND have not been deleted yet
                            #   (if done correctly, this list can tell you about objects that were leaked)
           
        arrays = ot.findPersistent('ndarray')  ## returns all objects matching 'ndarray' (string match, not instance checking)
                                               ## that were considered persistent when the last diff() was run
                                               
        describeObj(arrays[0])    ## See if we can determine who has references to this array
    """
    
    
    allObjs = {} ## keep track of all objects created and stored within class instances
    allObjs[id(allObjs)] = None
    
    def __init__(self):
        self.startRefs = {}        ## list of objects that exist when the tracker is initialized {oid: weakref}
                                   ##   (If it is not possible to weakref the object, then the value is None)
        self.startCount = {}       
        self.newRefs = {}          ## list of objects that have been created since initialization
        self.persistentRefs = {}   ## list of objects considered 'persistent' when the last diff() was called
        self.objTypes = {}
            
        ObjTracker.allObjs[id(self)] = None
        self.objs = [self.__dict__, self.startRefs, self.startCount, self.newRefs, self.persistentRefs, self.objTypes]
        self.objs.append(self.objs)
        for v in self.objs:
            ObjTracker.allObjs[id(v)] = None
            
        self.start()

    def findNew(self, regex):
        """Return all objects matching regex that were considered 'new' when the last diff() was run."""
        return self.findTypes(self.newRefs, regex)
    
    def findPersistent(self, regex):
        """Return all objects matching regex that were considered 'persistent' when the last diff() was run."""
        return self.findTypes(self.persistentRefs, regex)
        
    
    def start(self):
        """
        Remember the current set of objects as the comparison for all future calls to diff()
        Called automatically on init, but can be called manually as well.
        """
        refs, count, objs = self.collect()
        for r in self.startRefs:
            self.forgetRef(self.startRefs[r])
        self.startRefs.clear()
        self.startRefs.update(refs)
        for r in refs:
            self.rememberRef(r)
        self.startCount.clear()
        self.startCount.update(count)
        #self.newRefs.clear()
        #self.newRefs.update(refs)

    def diff(self, **kargs):
        """
        Compute all differences between the current object set and the reference set.
        Print a set of reports for created, deleted, and persistent objects
        """
        refs, count, objs = self.collect()   ## refs contains the list of ALL objects
        
        ## Which refs have disappeared since call to start()  (these are only displayed once, then forgotten.)
        delRefs = {}
        for i in self.startRefs.keys():
            if i not in refs:
                delRefs[i] = self.startRefs[i]
                del self.startRefs[i]
                self.forgetRef(delRefs[i])
        for i in self.newRefs.keys():
            if i not in refs:
                delRefs[i] = self.newRefs[i]
                del self.newRefs[i]
                self.forgetRef(delRefs[i])
        #print "deleted:", len(delRefs)
                
        ## Which refs have appeared since call to start() or diff()
        persistentRefs = {}      ## created since start(), but before last diff()
        createRefs = {}          ## created since last diff()
        for o in refs:
            if o not in self.startRefs:       
                if o not in self.newRefs:     
                    createRefs[o] = refs[o]          ## object has been created since last diff()
                else:
                    persistentRefs[o] = refs[o]      ## object has been created since start(), but before last diff() (persistent)
        #print "new:", len(newRefs)
                
        ## self.newRefs holds the entire set of objects created since start()
        for r in self.newRefs:
            self.forgetRef(self.newRefs[r])
        self.newRefs.clear()
        self.newRefs.update(persistentRefs)
        self.newRefs.update(createRefs)
        for r in self.newRefs:
            self.rememberRef(self.newRefs[r])
        #print "created:", len(createRefs)
        
        ## self.persistentRefs holds all objects considered persistent.
        self.persistentRefs.clear()
        self.persistentRefs.update(persistentRefs)
        
                
        print("----------- Count changes since start: ----------")
        c1 = count.copy()
        for k in self.startCount:
            c1[k] = c1.get(k, 0) - self.startCount[k]
        typs = list(c1.keys())
        typs.sort(lambda a,b: cmp(c1[a], c1[b]))
        for t in typs:
            if c1[t] == 0:
                continue
            num = "%d" % c1[t]
            print("  " + num + " "*(10-len(num)) + str(t))
            
        print("-----------  %d Deleted since last diff: ------------" % len(delRefs))
        self.report(delRefs, objs, **kargs)
        print("-----------  %d Created since last diff: ------------" % len(createRefs))
        self.report(createRefs, objs, **kargs)
        print("-----------  %d Created since start (persistent): ------------" % len(persistentRefs))
        self.report(persistentRefs, objs, **kargs)
        
        
    def __del__(self):
        self.startRefs.clear()
        self.startCount.clear()
        self.newRefs.clear()
        self.persistentRefs.clear()
        
        del ObjTracker.allObjs[id(self)]
        for v in self.objs:
            del ObjTracker.allObjs[id(v)]
            
    @classmethod
    def isObjVar(cls, o):
        return type(o) is cls or id(o) in cls.allObjs
            
    def collect(self):
        print("Collecting list of all objects...")
        gc.collect()
        objs = get_all_objects()
        frame = sys._getframe()
        del objs[id(frame)]  ## ignore the current frame 
        del objs[id(frame.f_code)]
        
        ignoreTypes = [int]
        refs = {}
        count = {}
        for k in objs:
            o = objs[k]
            typ = type(o)
            oid = id(o)
            if ObjTracker.isObjVar(o) or typ in ignoreTypes:
                continue
            
            try:
                ref = weakref.ref(obj)
            except:
                ref = None
            refs[oid] = ref
            typ = type(o)
            typStr = typeStr(o)
            self.objTypes[oid] = typStr
            ObjTracker.allObjs[id(typStr)] = None
            count[typ] = count.get(typ, 0) + 1
            
        print("All objects: %d   Tracked objects: %d" % (len(objs), len(refs)))
        return refs, count, objs
        
    def forgetRef(self, ref):
        if ref is not None:
            del ObjTracker.allObjs[id(ref)]
        
    def rememberRef(self, ref):
        ## Record the address of the weakref object so it is not included in future object counts.
        if ref is not None:
            ObjTracker.allObjs[id(ref)] = None
            
        
    def lookup(self, oid, ref, objs=None):
        if ref is None or ref() is None:
            try:
                obj = lookup(oid, objects=objs)
            except:
                obj = None
        else:
            obj = ref()
        return obj
                    
                    
    def report(self, refs, allobjs=None, showIDs=False):
        if allobjs is None:
            allobjs = get_all_objects()
        
        count = {}
        rev = {}
        for oid in refs:
            obj = self.lookup(oid, refs[oid], allobjs)
            if obj is None:
                typ = "[del] " + self.objTypes[oid]
            else:
                typ = typeStr(obj)
            if typ not in rev:
                rev[typ] = []
            rev[typ].append(oid)
            c = count.get(typ, [0,0])
            count[typ] =  [c[0]+1, c[1]+objectSize(obj)]
        typs = list(count.keys())
        typs.sort(lambda a,b: cmp(count[a][1], count[b][1]))
        
        for t in typs:
            line = "  %d\t%d\t%s" % (count[t][0], count[t][1], t)
            if showIDs:
                line += "\t"+",".join(map(str,rev[t]))
            print(line)
        
    def findTypes(self, refs, regex):
        allObjs = get_all_objects()
        ids = {}
        objs = []
        r = re.compile(regex)
        for k in refs:
            if r.search(self.objTypes[k]):
                objs.append(self.lookup(k, refs[k], allObjs))
        return objs
        

    
    
def describeObj(obj, depth=4, path=None, ignore=None):
    """
    Trace all reference paths backward, printing a list of different ways this object can be accessed.
    Attempts to answer the question "who has a reference to this object"
    """
    if path is None:
        path = [obj]
    if ignore is None:
        ignore = {}   ## holds IDs of objects used within the function.
    ignore[id(sys._getframe())] = None
    ignore[id(path)] = None
    gc.collect()
    refs = gc.get_referrers(obj)
    ignore[id(refs)] = None
    printed=False
    for ref in refs:
        if id(ref) in ignore:
            continue
        if id(ref) in list(map(id, path)):
            print("Cyclic reference: " + refPathString([ref]+path))
            printed = True
            continue
        newPath = [ref]+path
        if len(newPath) >= depth:
            refStr = refPathString(newPath)
            if '[_]' not in refStr:           ## ignore '_' references generated by the interactive shell
                print(refStr)
            printed = True
        else:
            describeObj(ref, depth, newPath, ignore)
            printed = True
    if not printed:
        print("Dead end: " + refPathString(path))
        
    
    
def typeStr(obj):
    """Create a more useful type string by making <instance> types report their class."""
    typ = type(obj)
    if typ == types.InstanceType:
        return "<instance of %s>" % obj.__class__.__name__
    else:
        return str(typ)
    
def searchRefs(obj, *args):
    """Pseudo-interactive function for tracing references backward.
    Arguments:
        obj:   The initial object from which to start searching
        args:  A set of string or int arguments.
               each integer selects one of obj's referrers to be the new 'obj'
               each string indicates an action to take on the current 'obj':
                  t:  print the types of obj's referrers
                  l:  print the lengths of obj's referrers (if they have __len__)
                  i:  print the IDs of obj's referrers
                  o:  print obj
                  ro: return obj
                  rr: return list of obj's referrers
    
    Examples:
       searchRefs(obj, 't')                    ## Print types of all objects referring to obj
       searchRefs(obj, 't', 0, 't')            ##   ..then select the first referrer and print the types of its referrers
       searchRefs(obj, 't', 0, 't', 'l')       ##   ..also print lengths of the last set of referrers
       searchRefs(obj, 0, 1, 'ro')             ## Select index 0 from obj's referrer, then select index 1 from the next set of referrers, then return that object
       
    """
    ignore = {id(sys._getframe()): None}
    gc.collect()
    refs = gc.get_referrers(obj)
    ignore[id(refs)] = None
    refs = [r for r in refs if id(r) not in ignore]
    for a in args:
        
        #fo = allFrameObjs()
        #refs = [r for r in refs if r not in fo]
        
        if type(a) is int:
            obj = refs[a]
            gc.collect()
            refs = gc.get_referrers(obj)
            ignore[id(refs)] = None
            refs = [r for r in refs if id(r) not in ignore]
        elif a == 't':
            print(list(map(typeStr, refs)))
        elif a == 'i':
            print(list(map(id, refs)))
        elif a == 'l':
            def slen(o):
                if hasattr(o, '__len__'):
                    return len(o)
                else:
                    return None
            print(list(map(slen, refs)))
        elif a == 'o':
            print(obj)
        elif a == 'ro':
            return obj
        elif a == 'rr':
            return refs
    
def allFrameObjs():
    """Return list of frame objects in current stack. Useful if you want to ignore these objects in refernece searches"""
    f = sys._getframe()
    objs = []
    while f is not None:
        objs.append(f)
        objs.append(f.f_code)
        #objs.append(f.f_locals)
        #objs.append(f.f_globals)
        #objs.append(f.f_builtins)
        f = f.f_back
    return objs
        
    
def findObj(regex):
    """Return a list of objects whose typeStr matches regex"""
    allObjs = get_all_objects()
    objs = []
    r = re.compile(regex)
    for i in allObjs:
        obj = allObjs[i]
        if r.search(typeStr(obj)):
            objs.append(obj)
    return objs
    


def listRedundantModules():
    """List modules that have been imported more than once via different paths."""
    mods = {}
    for name, mod in sys.modules.items():
        if not hasattr(mod, '__file__'):
            continue
        mfile = os.path.abspath(mod.__file__)
        if mfile[-1] == 'c':
            mfile = mfile[:-1]
        if mfile in mods:
            print("module at %s has 2 names: %s, %s" % (mfile, name, mods[mfile]))
        else:
            mods[mfile] = name
            

def walkQObjectTree(obj, counts=None, verbose=False, depth=0):
    """
    Walk through a tree of QObjects, doing nothing to them.
    The purpose of this function is to find dead objects and generate a crash
    immediately rather than stumbling upon them later.
    Prints a count of the objects encountered, for fun. (or is it?)
    """
    
    if verbose:
        print("  "*depth + typeStr(obj))
    report = False
    if counts is None:
        counts = {}
        report = True
    typ = str(type(obj))
    try:
        counts[typ] += 1
    except KeyError:
        counts[typ] = 1
    for child in obj.children():
        walkQObjectTree(child, counts, verbose, depth+1)
        
    return counts

QObjCache = {}
def qObjectReport(verbose=False):
    """Generate a report counting all QObjects and their types"""
    global qObjCache
    count = {}
    for obj in findObj('PyQt'):
        if isinstance(obj, QtCore.QObject):
            oid = id(obj)
            if oid not in QObjCache:
                QObjCache[oid] = typeStr(obj) + "  " + obj.objectName()
                try:
                    QObjCache[oid] += "  " + obj.parent().objectName()
                    QObjCache[oid] += "  " + obj.text()
                except:
                    pass
            print("check obj", oid, str(QObjCache[oid]))
            if obj.parent() is None:
                walkQObjectTree(obj, count, verbose)
            
    typs = list(count.keys())
    typs.sort()
    for t in typs:
        print(count[t], "\t", t)
        

class PrintDetector(object):
    def __init__(self):
        self.stdout = sys.stdout
        sys.stdout = self
    
    def remove(self):
        sys.stdout = self.stdout
        
    def __del__(self):
        self.remove()
    
    def write(self, x):
        self.stdout.write(x)
        traceback.print_stack()
        
    def flush(self):
        self.stdout.flush()