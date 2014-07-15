# -*- coding: utf-8 -*-
"""
advancedTypes.py - Basic data structures not included with python 
Copyright 2010  Luke Campagnola
Distributed under MIT/X11 license. See license.txt for more infomation.

Includes:
  - OrderedDict - Dictionary which preserves the order of its elements
  - BiDict, ReverseDict - Bi-directional dictionaries
  - ThreadsafeDict, ThreadsafeList - Self-mutexed data structures
"""

import threading, sys, copy, collections
#from debug import *

try:
    from collections import OrderedDict
except ImportError:
    # fallback: try to use the ordereddict backport when using python 2.6
    from ordereddict import OrderedDict
        

class ReverseDict(dict):
    """extends dict so that reverse lookups are possible by requesting the key as a list of length 1:
       d = BiDict({'x': 1, 'y': 2})
       d['x']
         1
       d[[2]]
         'y'
    """
    def __init__(self, data=None):
        if data is None:
            data = {}
        self.reverse = {}
        for k in data:
            self.reverse[data[k]] = k
        dict.__init__(self, data)
        
    def __getitem__(self, item):
        if type(item) is list:
            return self.reverse[item[0]]
        else:
            return dict.__getitem__(self, item)

    def __setitem__(self, item, value):
        self.reverse[value] = item
        dict.__setitem__(self, item, value)

    def __deepcopy__(self, memo):
        raise Exception("deepcopy not implemented")
        
        
class BiDict(dict):
    """extends dict so that reverse lookups are possible by adding each reverse combination to the dict.
    This only works if all values and keys are unique."""
    def __init__(self, data=None):
        if data is None:
            data = {}
        dict.__init__(self)
        for k in data:
            self[data[k]] = k
        
    def __setitem__(self, item, value):
        dict.__setitem__(self, item, value)
        dict.__setitem__(self, value, item)
    
    def __deepcopy__(self, memo):
        raise Exception("deepcopy not implemented")

class ThreadsafeDict(dict):
    """Extends dict so that getitem, setitem, and contains are all thread-safe.
    Also adds lock/unlock functions for extended exclusive operations
    Converts all sub-dicts and lists to threadsafe as well.
    """
    
    def __init__(self, *args, **kwargs):
        self.mutex = threading.RLock()
        dict.__init__(self, *args, **kwargs)
        for k in self:
            if type(self[k]) is dict:
                self[k] = ThreadsafeDict(self[k])

    def __getitem__(self, attr):
        self.lock()
        try:
            val = dict.__getitem__(self, attr)
        finally:
            self.unlock()
        return val

    def __setitem__(self, attr, val):
        if type(val) is dict:
            val = ThreadsafeDict(val)
        self.lock()
        try:
            dict.__setitem__(self, attr, val)
        finally:
            self.unlock()
        
    def __contains__(self, attr):
        self.lock()
        try:
            val = dict.__contains__(self, attr)
        finally:
            self.unlock()
        return val

    def __len__(self):
        self.lock()
        try:
            val = dict.__len__(self)
        finally:
            self.unlock()
        return val

    def clear(self):
        self.lock()
        try:
            dict.clear(self)
        finally:
            self.unlock()

    def lock(self):
        self.mutex.acquire()
        
    def unlock(self):
        self.mutex.release()

    def __deepcopy__(self, memo):
        raise Exception("deepcopy not implemented")
        
class ThreadsafeList(list):
    """Extends list so that getitem, setitem, and contains are all thread-safe.
    Also adds lock/unlock functions for extended exclusive operations
    Converts all sub-lists and dicts to threadsafe as well.
    """
    
    def __init__(self, *args, **kwargs):
        self.mutex = threading.RLock()
        list.__init__(self, *args, **kwargs)
        for k in self:
            self[k] = mkThreadsafe(self[k])

    def __getitem__(self, attr):
        self.lock()
        try:
            val = list.__getitem__(self, attr)
        finally:
            self.unlock()
        return val

    def __setitem__(self, attr, val):
        val = makeThreadsafe(val)
        self.lock()
        try:
            list.__setitem__(self, attr, val)
        finally:
            self.unlock()
        
    def __contains__(self, attr):
        self.lock()
        try:
            val = list.__contains__(self, attr)
        finally:
            self.unlock()
        return val

    def __len__(self):
        self.lock()
        try:
            val = list.__len__(self)
        finally:
            self.unlock()
        return val
    
    def lock(self):
        self.mutex.acquire()
        
    def unlock(self):
        self.mutex.release()

    def __deepcopy__(self, memo):
        raise Exception("deepcopy not implemented")
        
        
def makeThreadsafe(obj):
    if type(obj) is dict:
        return ThreadsafeDict(obj)
    elif type(obj) is list:
        return ThreadsafeList(obj)
    elif type(obj) in [str, int, float, bool, tuple]:
        return obj
    else:
        raise Exception("Not sure how to make object of type %s thread-safe" % str(type(obj)))
        
        
class Locker(object):
    def __init__(self, lock):
        self.lock = lock
        self.lock.acquire()
    def __del__(self):
        try:
            self.lock.release()
        except:
            pass

class CaselessDict(OrderedDict):
    """Case-insensitive dict. Values can be set and retrieved using keys of any case.
    Note that when iterating, the original case is returned for each key."""
    def __init__(self, *args):
        OrderedDict.__init__(self, {}) ## requirement for the empty {} here seems to be a python bug?
        self.keyMap = OrderedDict([(k.lower(), k) for k in OrderedDict.keys(self)])
        if len(args) == 0:
            return
        elif len(args) == 1 and isinstance(args[0], dict):
            for k in args[0]:
                self[k] = args[0][k]
        else:
            raise Exception("CaselessDict may only be instantiated with a single dict.")
        
    #def keys(self):
        #return self.keyMap.values()
    
    def __setitem__(self, key, val):
        kl = key.lower()
        if kl in self.keyMap:
            OrderedDict.__setitem__(self, self.keyMap[kl], val)
        else:
            OrderedDict.__setitem__(self, key, val)
            self.keyMap[kl] = key
            
    def __getitem__(self, key):
        kl = key.lower()
        if kl not in self.keyMap:
            raise KeyError(key)
        return OrderedDict.__getitem__(self, self.keyMap[kl])
        
    def __contains__(self, key):
        return key.lower() in self.keyMap
    
    def update(self, d):
        for k, v in d.iteritems():
            self[k] = v
            
    def copy(self):
        return CaselessDict(OrderedDict.copy(self))
        
    def __delitem__(self, key):
        kl = key.lower()
        if kl not in self.keyMap:
            raise KeyError(key)
        OrderedDict.__delitem__(self, self.keyMap[kl])
        del self.keyMap[kl]
            
    def __deepcopy__(self, memo):
        raise Exception("deepcopy not implemented")

    def clear(self):
        OrderedDict.clear(self)
        self.keyMap.clear()



class ProtectedDict(dict):
    """
    A class allowing read-only 'view' of a dict. 
    The object can be treated like a normal dict, but will never modify the original dict it points to.
    Any values accessed from the dict will also be read-only.
    """
    def __init__(self, data):
        self._data_ = data
    
    ## List of methods to directly wrap from _data_
    wrapMethods = ['_cmp_', '__contains__', '__eq__', '__format__', '__ge__', '__gt__', '__le__', '__len__', '__lt__', '__ne__', '__reduce__', '__reduce_ex__', '__repr__', '__str__', 'count', 'has_key', 'iterkeys', 'keys', ]
    
    ## List of methods which wrap from _data_ but return protected results
    protectMethods = ['__getitem__', '__iter__', 'get', 'items', 'values']
    
    ## List of methods to disable
    disableMethods = ['__delitem__', '__setitem__', 'clear', 'pop', 'popitem', 'setdefault', 'update']
    
    
    ## Template methods 
    def wrapMethod(methodName):
        return lambda self, *a, **k: getattr(self._data_, methodName)(*a, **k)
        
    def protectMethod(methodName):
        return lambda self, *a, **k: protect(getattr(self._data_, methodName)(*a, **k))
    
    def error(self, *args, **kargs):
        raise Exception("Can not modify read-only list.")
    
    
    ## Directly (and explicitly) wrap some methods from _data_
    ## Many of these methods can not be intercepted using __getattribute__, so they
    ## must be implemented explicitly
    for methodName in wrapMethods:
        locals()[methodName] = wrapMethod(methodName)

    ## Wrap some methods from _data_ with the results converted to protected objects
    for methodName in protectMethods:
        locals()[methodName] = protectMethod(methodName)

    ## Disable any methods that could change data in the list
    for methodName in disableMethods:
        locals()[methodName] = error

    
    ## Add a few extra methods.
    def copy(self):
        raise Exception("It is not safe to copy protected dicts! (instead try deepcopy, but be careful.)")
    
    def itervalues(self):
        for v in self._data_.itervalues():
            yield protect(v)
        
    def iteritems(self):
        for k, v in self._data_.iteritems():
            yield (k, protect(v))
        
    def deepcopy(self):
        return copy.deepcopy(self._data_)
    
    def __deepcopy__(self, memo):
        return copy.deepcopy(self._data_, memo)


            
class ProtectedList(collections.Sequence):
    """
    A class allowing read-only 'view' of a list or dict. 
    The object can be treated like a normal list, but will never modify the original list it points to.
    Any values accessed from the list will also be read-only.
    
    Note: It would be nice if we could inherit from list or tuple so that isinstance checks would work.
          However, doing this causes tuple(obj) to return unprotected results (importantly, this means
          unpacking into function arguments will also fail)
    """
    def __init__(self, data):
        self._data_ = data
        #self.__mro__ = (ProtectedList, object)
        
    ## List of methods to directly wrap from _data_
    wrapMethods = ['__contains__', '__eq__', '__format__', '__ge__', '__gt__', '__le__', '__len__', '__lt__', '__ne__', '__reduce__', '__reduce_ex__', '__repr__', '__str__', 'count', 'index']
    
    ## List of methods which wrap from _data_ but return protected results
    protectMethods = ['__getitem__', '__getslice__', '__mul__', '__reversed__', '__rmul__']
    
    ## List of methods to disable
    disableMethods = ['__delitem__', '__delslice__', '__iadd__', '__imul__', '__setitem__', '__setslice__', 'append', 'extend', 'insert', 'pop', 'remove', 'reverse', 'sort']
    
    
    ## Template methods 
    def wrapMethod(methodName):
        return lambda self, *a, **k: getattr(self._data_, methodName)(*a, **k)
        
    def protectMethod(methodName):
        return lambda self, *a, **k: protect(getattr(self._data_, methodName)(*a, **k))
    
    def error(self, *args, **kargs):
        raise Exception("Can not modify read-only list.")
    
    
    ## Directly (and explicitly) wrap some methods from _data_
    ## Many of these methods can not be intercepted using __getattribute__, so they
    ## must be implemented explicitly
    for methodName in wrapMethods:
        locals()[methodName] = wrapMethod(methodName)

    ## Wrap some methods from _data_ with the results converted to protected objects
    for methodName in protectMethods:
        locals()[methodName] = protectMethod(methodName)

    ## Disable any methods that could change data in the list
    for methodName in disableMethods:
        locals()[methodName] = error

    
    ## Add a few extra methods.
    def __iter__(self):
        for item in self._data_:
            yield protect(item)
    
    
    def __add__(self, op):
        if isinstance(op, ProtectedList):
            return protect(self._data_.__add__(op._data_))
        elif isinstance(op, list):
            return protect(self._data_.__add__(op))
        else:
            raise TypeError("Argument must be a list.")
    
    def __radd__(self, op):
        if isinstance(op, ProtectedList):
            return protect(op._data_.__add__(self._data_))
        elif isinstance(op, list):
            return protect(op.__add__(self._data_))
        else:
            raise TypeError("Argument must be a list.")
        
    def deepcopy(self):
        return copy.deepcopy(self._data_)
    
    def __deepcopy__(self, memo):
        return copy.deepcopy(self._data_, memo)
    
    def poop(self):
        raise Exception("This is a list. It does not poop.")


class ProtectedTuple(collections.Sequence):
    """
    A class allowing read-only 'view' of a tuple.
    The object can be treated like a normal tuple, but its contents will be returned as protected objects.
    
    Note: It would be nice if we could inherit from list or tuple so that isinstance checks would work.
          However, doing this causes tuple(obj) to return unprotected results (importantly, this means
          unpacking into function arguments will also fail)
    """
    def __init__(self, data):
        self._data_ = data
    
    ## List of methods to directly wrap from _data_
    wrapMethods = ['__contains__', '__eq__', '__format__', '__ge__', '__getnewargs__', '__gt__', '__hash__', '__le__', '__len__', '__lt__', '__ne__', '__reduce__', '__reduce_ex__', '__repr__', '__str__', 'count', 'index']
    
    ## List of methods which wrap from _data_ but return protected results
    protectMethods = ['__getitem__', '__getslice__', '__iter__', '__add__', '__mul__', '__reversed__', '__rmul__']
    
    
    ## Template methods 
    def wrapMethod(methodName):
        return lambda self, *a, **k: getattr(self._data_, methodName)(*a, **k)
        
    def protectMethod(methodName):
        return lambda self, *a, **k: protect(getattr(self._data_, methodName)(*a, **k))
    
    
    ## Directly (and explicitly) wrap some methods from _data_
    ## Many of these methods can not be intercepted using __getattribute__, so they
    ## must be implemented explicitly
    for methodName in wrapMethods:
        locals()[methodName] = wrapMethod(methodName)

    ## Wrap some methods from _data_ with the results converted to protected objects
    for methodName in protectMethods:
        locals()[methodName] = protectMethod(methodName)

    
    ## Add a few extra methods.
    def deepcopy(self):
        return copy.deepcopy(self._data_)
    
    def __deepcopy__(self, memo):
        return copy.deepcopy(self._data_, memo)
    


def protect(obj):
    if isinstance(obj, dict):
        return ProtectedDict(obj)
    elif isinstance(obj, list):
        return ProtectedList(obj)
    elif isinstance(obj, tuple):
        return ProtectedTuple(obj)
    else:
        return obj
    
    
if __name__ == '__main__':
    d = {'x': 1, 'y': [1,2], 'z': ({'a': 2, 'b': [3,4], 'c': (5,6)}, 1, 2)}
    dp = protect(d)
    
    l = [1, 'x', ['a', 'b'], ('c', 'd'), {'x': 1, 'y': 2}]
    lp = protect(l)
    
    t = (1, 'x', ['a', 'b'], ('c', 'd'), {'x': 1, 'y': 2})
    tp = protect(t)
