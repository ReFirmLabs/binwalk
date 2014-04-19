# -*- coding: utf-8 -*-
from pyqtgraph.pgcollections import OrderedDict
from pyqtgraph import importModules
import os, types
from pyqtgraph.debug import printExc
from ..Node import Node
import pyqtgraph.reload as reload


NODE_LIST = OrderedDict()  ## maps name:class for all registered Node subclasses
NODE_TREE = OrderedDict()  ## categorized tree of Node subclasses

def getNodeType(name):
    try:
        return NODE_LIST[name]
    except KeyError:
        raise Exception("No node type called '%s'" % name)

def getNodeTree():
    return NODE_TREE

def registerNodeType(cls, paths, override=False):
    """
    Register a new node type. If the type's name is already in use,
    an exception will be raised (unless override=True).
    
    Arguments:
        cls - a subclass of Node (must have typ.nodeName)
        paths - list of tuples specifying the location(s) this 
                type will appear in the library tree.
        override - if True, overwrite any class having the same name
    """
    if not isNodeClass(cls):
        raise Exception("Object %s is not a Node subclass" % str(cls))
    
    name = cls.nodeName
    if not override and name in NODE_LIST:
        raise Exception("Node type name '%s' is already registered." % name)
    
    NODE_LIST[name] = cls
    for path in paths:
        root = NODE_TREE
        for n in path:
            if n not in root:
                root[n] = OrderedDict()
            root = root[n]
        root[name] = cls



def isNodeClass(cls):
    try:
        if not issubclass(cls, Node):
            return False
    except:
        return False
    return hasattr(cls, 'nodeName')

def loadLibrary(reloadLibs=False, libPath=None):
    """Import all Node subclasses found within files in the library module."""

    global NODE_LIST, NODE_TREE
    #if libPath is None:
        #libPath = os.path.dirname(os.path.abspath(__file__))
    
    if reloadLibs:
        reload.reloadAll(libPath)
        
    mods = importModules('', globals(), locals())
    #for f in frozenSupport.listdir(libPath):
        #pathName, ext = os.path.splitext(f)
        #if ext not in ('.py', '.pyc') or '__init__' in pathName or '__pycache__' in pathName:
            #continue
        #try:
            ##print "importing from", f
            #mod = __import__(pathName, globals(), locals())
        #except:
            #printExc("Error loading flowchart library %s:" % pathName)
            #continue
        
    for name, mod in mods.items():
        nodes = []
        for n in dir(mod):
            o = getattr(mod, n)
            if isNodeClass(o):
                #print "  ", str(o)
                registerNodeType(o, [(name,)], override=reloadLibs)
                #nodes.append((o.nodeName, o))
        #if len(nodes) > 0:
            #NODE_TREE[name] = OrderedDict(nodes)
            #NODE_LIST.extend(nodes)
    #NODE_LIST = OrderedDict(NODE_LIST)
    
def reloadLibrary():
    loadLibrary(reloadLibs=True)
    
loadLibrary()
#NODE_LIST = []
#for o in locals().values():
    #if type(o) is type(AddNode) and issubclass(o, Node) and o is not Node and hasattr(o, 'nodeName'):
            #NODE_LIST.append((o.nodeName, o))
#NODE_LIST.sort(lambda a,b: cmp(a[0], b[0]))
#NODE_LIST = OrderedDict(NODE_LIST)