from pyqtgraph.Qt import QtGui, QtCore
import os, weakref, re
from pyqtgraph.pgcollections import OrderedDict
from .ParameterItem import ParameterItem

PARAM_TYPES = {}
PARAM_NAMES = {}

def registerParameterType(name, cls, override=False):
    global PARAM_TYPES
    if name in PARAM_TYPES and not override:
        raise Exception("Parameter type '%s' already exists (use override=True to replace)" % name)
    PARAM_TYPES[name] = cls
    PARAM_NAMES[cls] = name



class Parameter(QtCore.QObject):
    """
    A Parameter is the basic unit of data in a parameter tree. Each parameter has
    a name, a type, a value, and several other properties that modify the behavior of the 
    Parameter. Parameters may have parent / child / sibling relationships to construct
    organized hierarchies. Parameters generally do not have any inherent GUI or visual
    interpretation; instead they manage ParameterItem instances which take care of
    display and user interaction.
    
    Note: It is fairly uncommon to use the Parameter class directly; mostly you 
    will use subclasses which provide specialized type and data handling. The static
    pethod Parameter.create(...) is an easy way to generate instances of these subclasses.
       
    For more Parameter types, see ParameterTree.parameterTypes module.
    
    ===================================  =========================================================
    **Signals:**
    sigStateChanged(self, change, info)  Emitted when anything changes about this parameter at 
                                         all.
                                         The second argument is a string indicating what changed 
                                         ('value', 'childAdded', etc..)
                                         The third argument can be any extra information about 
                                         the change
    sigTreeStateChanged(self, changes)   Emitted when any child in the tree changes state
                                         (but only if monitorChildren() is called)
                                         the format of *changes* is [(param, change, info), ...]
    sigValueChanged(self, value)         Emitted when value is finished changing
    sigValueChanging(self, value)        Emitted immediately for all value changes, 
                                         including during editing.
    sigChildAdded(self, child, index)    Emitted when a child is added
    sigChildRemoved(self, child)         Emitted when a child is removed
    sigParentChanged(self, parent)       Emitted when this parameter's parent has changed
    sigLimitsChanged(self, limits)       Emitted when this parameter's limits have changed
    sigDefaultChanged(self, default)     Emitted when this parameter's default value has changed
    sigNameChanged(self, name)           Emitted when this parameter's name has changed
    sigOptionsChanged(self, opts)        Emitted when any of this parameter's options have changed
    ===================================  =========================================================
    """
    ## name, type, limits, etc.
    ## can also carry UI hints (slider vs spinbox, etc.)
    
    sigValueChanged = QtCore.Signal(object, object)  ## self, value   emitted when value is finished being edited
    sigValueChanging = QtCore.Signal(object, object)  ## self, value  emitted as value is being edited
    
    sigChildAdded = QtCore.Signal(object, object, object)  ## self, child, index
    sigChildRemoved = QtCore.Signal(object, object)  ## self, child
    sigParentChanged = QtCore.Signal(object, object)  ## self, parent
    sigLimitsChanged = QtCore.Signal(object, object)  ## self, limits
    sigDefaultChanged = QtCore.Signal(object, object)  ## self, default
    sigNameChanged = QtCore.Signal(object, object)  ## self, name
    sigOptionsChanged = QtCore.Signal(object, object)  ## self, {opt:val, ...}
    
    ## Emitted when anything changes about this parameter at all.
    ## The second argument is a string indicating what changed ('value', 'childAdded', etc..)
    ## The third argument can be any extra information about the change
    sigStateChanged = QtCore.Signal(object, object, object) ## self, change, info
    
    ## emitted when any child in the tree changes state
    ## (but only if monitorChildren() is called)
    sigTreeStateChanged = QtCore.Signal(object, object)  # self, changes
                                                         # changes = [(param, change, info), ...]
    
    # bad planning.
    #def __new__(cls, *args, **opts):
        #try:
            #cls = PARAM_TYPES[opts['type']]
        #except KeyError:
            #pass
        #return QtCore.QObject.__new__(cls, *args, **opts)
    
    @staticmethod
    def create(**opts):
        """
        Static method that creates a new Parameter (or subclass) instance using 
        opts['type'] to select the appropriate class.
        
        All options are passed directly to the new Parameter's __init__ method.
        Use registerParameterType() to add new class types.
        """
        typ = opts.get('type', None)
        if typ is None:
            cls = Parameter
        else:
            cls = PARAM_TYPES[opts['type']]
        return cls(**opts)
    
    def __init__(self, **opts):
        """
        Initialize a Parameter object. Although it is rare to directly create a
        Parameter instance, the options available to this method are also allowed
        by most Parameter subclasses.
        
        ================= =========================================================
        Keyword Arguments
        name              The name to give this Parameter. This is the name that 
                          will appear in the left-most column of a ParameterTree
                          for this Parameter.
        value             The value to initially assign to this Parameter.
        default           The default value for this Parameter (most Parameters
                          provide an option to 'reset to default').
        children          A list of children for this Parameter. Children
                          may be given either as a Parameter instance or as a
                          dictionary to pass to Parameter.create(). In this way,
                          it is possible to specify complex hierarchies of
                          Parameters from a single nested data structure.
        readonly          If True, the user will not be allowed to edit this 
                          Parameter. (default=False)
        enabled           If False, any widget(s) for this parameter will appear
                          disabled. (default=True)
        visible           If False, the Parameter will not appear when displayed
                          in a ParameterTree. (default=True)
        renamable         If True, the user may rename this Parameter.
                          (default=False)
        removable         If True, the user may remove this Parameter.
                          (default=False)
        expanded          If True, the Parameter will appear expanded when 
                          displayed in a ParameterTree (its children will be 
                          visible). (default=True)
        ================= =========================================================
        """
        
        
        QtCore.QObject.__init__(self)
        
        self.opts = {
            'type': None,
            'readonly': False,
            'visible': True,
            'enabled': True,
            'renamable': False,
            'removable': False,
            'strictNaming': False,  # forces name to be usable as a python variable
            'expanded': True,
            #'limits': None,  ## This is a bad plan--each parameter type may have a different data type for limits.
        }
        self.opts.update(opts)
        
        self.childs = []
        self.names = {}   ## map name:child
        self.items = weakref.WeakKeyDictionary()  ## keeps track of tree items representing this parameter
        self._parent = None
        self.treeStateChanges = []  ## cache of tree state changes to be delivered on next emit
        self.blockTreeChangeEmit = 0
        #self.monitoringChildren = False  ## prevent calling monitorChildren more than once
        
        if 'value' not in self.opts:
            self.opts['value'] = None
        
        if 'name' not in self.opts or not isinstance(self.opts['name'], basestring):
            raise Exception("Parameter must have a string name specified in opts.")
        self.setName(opts['name'])
        
        self.addChildren(self.opts.get('children', []))
            
        if 'value' in self.opts and 'default' not in self.opts:
            self.opts['default'] = self.opts['value']
    
        ## Connect all state changed signals to the general sigStateChanged
        self.sigValueChanged.connect(lambda param, data: self.emitStateChanged('value', data))
        self.sigChildAdded.connect(lambda param, *data: self.emitStateChanged('childAdded', data))
        self.sigChildRemoved.connect(lambda param, data: self.emitStateChanged('childRemoved', data))
        self.sigParentChanged.connect(lambda param, data: self.emitStateChanged('parent', data))
        self.sigLimitsChanged.connect(lambda param, data: self.emitStateChanged('limits', data))
        self.sigDefaultChanged.connect(lambda param, data: self.emitStateChanged('default', data))
        self.sigNameChanged.connect(lambda param, data: self.emitStateChanged('name', data))
        self.sigOptionsChanged.connect(lambda param, data: self.emitStateChanged('options', data))
        
        #self.watchParam(self)  ## emit treechange signals if our own state changes
        
    def name(self):
        """Return the name of this Parameter."""
        return self.opts['name']

    def setName(self, name):
        """Attempt to change the name of this parameter; return the actual name. 
        (The parameter may reject the name change or automatically pick a different name)"""
        if self.opts['strictNaming']:
            if len(name) < 1 or re.search(r'\W', name) or re.match(r'\d', name[0]):
                raise Exception("Parameter name '%s' is invalid. (Must contain only alphanumeric and underscore characters and may not start with a number)" % name)
        parent = self.parent()
        if parent is not None:
            name = parent._renameChild(self, name)  ## first ask parent if it's ok to rename
        if self.opts['name'] != name:
            self.opts['name'] = name
            self.sigNameChanged.emit(self, name)
        return name

    def type(self):
        """Return the type string for this Parameter."""
        return self.opts['type']
        
    def isType(self, typ):
        """
        Return True if this parameter type matches the name *typ*.
        This can occur either of two ways:
        
        - If self.type() == *typ*
        - If this parameter's class is registered with the name *typ*
        """
        if self.type() == typ:
            return True
        global PARAM_TYPES
        cls = PARAM_TYPES.get(typ, None)
        if cls is None:
            raise Exception("Type name '%s' is not registered." % str(typ))
        return self.__class__ is cls
        
    def childPath(self, child):
        """
        Return the path of parameter names from self to child.
        If child is not a (grand)child of self, return None.
        """
        path = []
        while child is not self:
            path.insert(0, child.name())
            child = child.parent()
            if child is None:
                return None
        return path

    def setValue(self, value, blockSignal=None):
        """
        Set the value of this Parameter; return the actual value that was set.
        (this may be different from the value that was requested)
        """
        try:
            if blockSignal is not None:
                self.sigValueChanged.disconnect(blockSignal)
            if self.opts['value'] == value:
                return value
            self.opts['value'] = value
            self.sigValueChanged.emit(self, value)
        finally:
            if blockSignal is not None:
                self.sigValueChanged.connect(blockSignal)
            
        return value

    def value(self):
        """
        Return the value of this Parameter.
        """
        return self.opts['value']

    def getValues(self):
        """Return a tree of all values that are children of this parameter"""
        vals = OrderedDict()
        for ch in self:
            vals[ch.name()] = (ch.value(), ch.getValues())
        return vals
    
    def saveState(self):
        """
        Return a structure representing the entire state of the parameter tree.
        The tree state may be restored from this structure using restoreState()
        """
        state = self.opts.copy()
        state['children'] = OrderedDict([(ch.name(), ch.saveState()) for ch in self])
        if state['type'] is None:
            global PARAM_NAMES
            state['type'] = PARAM_NAMES.get(type(self), None)
        return state

    def restoreState(self, state, recursive=True, addChildren=True, removeChildren=True, blockSignals=True):
        """
        Restore the state of this parameter and its children from a structure generated using saveState()
        If recursive is True, then attempt to restore the state of child parameters as well.
        If addChildren is True, then any children which are referenced in the state object will be
        created if they do not already exist.
        If removeChildren is True, then any children which are not referenced in the state object will 
        be removed.
        If blockSignals is True, no signals will be emitted until the tree has been completely restored. 
        This prevents signal handlers from responding to a partially-rebuilt network.
        """
        childState = state.get('children', [])
        
        ## list of children may be stored either as list or dict.
        if isinstance(childState, dict):
            childState = childState.values()
            
        
        if blockSignals:
            self.blockTreeChangeSignal()
            
        try:
            self.setOpts(**state)
            
            if not recursive:
                return
            
            ptr = 0  ## pointer to first child that has not been restored yet
            foundChilds = set()
            #print "==============", self.name()
            
            for ch in childState:
                name = ch['name']
                typ = ch['type']
                #print('child: %s, %s' % (self.name()+'.'+name, typ))
                
                ## First, see if there is already a child with this name and type
                gotChild = False
                for i, ch2 in enumerate(self.childs[ptr:]):
                    #print "  ", ch2.name(), ch2.type()
                    if ch2.name() != name or not ch2.isType(typ):
                        continue
                    gotChild = True
                    #print "    found it"
                    if i != 0:  ## move parameter to next position
                        #self.removeChild(ch2)
                        self.insertChild(ptr, ch2)
                        #print "  moved to position", ptr
                    ch2.restoreState(ch, recursive=recursive, addChildren=addChildren, removeChildren=removeChildren)
                    foundChilds.add(ch2)
                    
                    break
                
                if not gotChild:
                    if not addChildren:
                        #print "  ignored child"
                        continue
                    #print "    created new"
                    ch2 = Parameter.create(**ch)
                    self.insertChild(ptr, ch2)
                    foundChilds.add(ch2)
                    
                ptr += 1
                
            if removeChildren:
                for ch in self.childs[:]:
                    if ch not in foundChilds:
                        #print "  remove:", ch
                        self.removeChild(ch)
        finally:
            if blockSignals:
                self.unblockTreeChangeSignal()
            
            
        
    def defaultValue(self):
        """Return the default value for this parameter."""
        return self.opts['default']
        
    def setDefault(self, val):
        """Set the default value for this parameter."""
        if self.opts['default'] == val:
            return
        self.opts['default'] = val
        self.sigDefaultChanged.emit(self, val)

    def setToDefault(self):
        """Set this parameter's value to the default."""
        if self.hasDefault():
            self.setValue(self.defaultValue())

    def hasDefault(self):
        """Returns True if this parameter has a default value."""
        return 'default' in self.opts
        
    def valueIsDefault(self):
        """Returns True if this parameter's value is equal to the default value."""
        return self.value() == self.defaultValue()
        
    def setLimits(self, limits):
        """Set limits on the acceptable values for this parameter. 
        The format of limits depends on the type of the parameter and
        some parameters do not make use of limits at all."""
        if 'limits' in self.opts and self.opts['limits'] == limits:
            return
        self.opts['limits'] = limits
        self.sigLimitsChanged.emit(self, limits)
        return limits

    def writable(self):
        """
        Returns True if this parameter's value can be changed by the user.
        Note that the value of the parameter can *always* be changed by
        calling setValue().
        """
        return not self.opts.get('readonly', False)

    def setWritable(self, writable=True):
        """Set whether this Parameter should be editable by the user. (This is 
        exactly the opposite of setReadonly)."""
        self.setOpts(readonly=not writable)
        
    def setReadonly(self, readonly=True):
        """Set whether this Parameter's value may be edited by the user."""
        self.setOpts(readonly=readonly)
        
    def setOpts(self, **opts):
        """
        Set any arbitrary options on this parameter.
        The exact behavior of this function will depend on the parameter type, but
        most parameters will accept a common set of options: value, name, limits,
        default, readonly, removable, renamable, visible, enabled, and expanded.
        
        See :func:`Parameter.__init__ <pyqtgraph.parametertree.Parameter.__init__>`
        for more information on default options.
        """
        changed = OrderedDict()
        for k in opts:
            if k == 'value':
                self.setValue(opts[k])
            elif k == 'name':
                self.setName(opts[k])
            elif k == 'limits':
                self.setLimits(opts[k])
            elif k == 'default':
                self.setDefault(opts[k])
            elif k not in self.opts or self.opts[k] != opts[k]:
                self.opts[k] = opts[k]
                changed[k] = opts[k]
                
        if len(changed) > 0:
            self.sigOptionsChanged.emit(self, changed)
        
    def emitStateChanged(self, changeDesc, data):
        ## Emits stateChanged signal and 
        ## requests emission of new treeStateChanged signal
        self.sigStateChanged.emit(self, changeDesc, data)
        #self.treeStateChanged(self, changeDesc, data)
        self.treeStateChanges.append((self, changeDesc, data))
        self.emitTreeChanges()

    def makeTreeItem(self, depth):
        """
        Return a TreeWidgetItem suitable for displaying/controlling the content of 
        this parameter. This is called automatically when a ParameterTree attempts
        to display this Parameter.
        Most subclasses will want to override this function.
        """
        if hasattr(self, 'itemClass'):
            #print "Param:", self, "Make item from itemClass:", self.itemClass
            return self.itemClass(self, depth)
        else:
            return ParameterItem(self, depth=depth)


    def addChild(self, child):
        """Add another parameter to the end of this parameter's child list."""
        return self.insertChild(len(self.childs), child)

    def addChildren(self, children):
        ## If children was specified as dict, then assume keys are the names.
        if isinstance(children, dict):
            ch2 = []
            for name, opts in children.items():
                if isinstance(opts, dict) and 'name' not in opts:
                    opts = opts.copy()
                    opts['name'] = name
                ch2.append(opts)
            children = ch2
        
        for chOpts in children:
            #print self, "Add child:", type(chOpts), id(chOpts)
            self.addChild(chOpts)
        
        
    def insertChild(self, pos, child):
        """
        Insert a new child at pos.
        If pos is a Parameter, then insert at the position of that Parameter.
        If child is a dict, then a parameter is constructed using
        :func:`Parameter.create <pyqtgraph.parametertree.Parameter.create>`.
        """
        if isinstance(child, dict):
            child = Parameter.create(**child)
        
        name = child.name()
        if name in self.names and child is not self.names[name]:
            if child.opts.get('autoIncrementName', False):
                name = self.incrementName(name)
                child.setName(name)
            else:
                raise Exception("Already have child named %s" % str(name))
        if isinstance(pos, Parameter):
            pos = self.childs.index(pos)
            
        with self.treeChangeBlocker():
            if child.parent() is not None:
                child.remove()
                
            self.names[name] = child
            self.childs.insert(pos, child)
            
            child.parentChanged(self)
            self.sigChildAdded.emit(self, child, pos)
            child.sigTreeStateChanged.connect(self.treeStateChanged)
        return child
        
    def removeChild(self, child):
        """Remove a child parameter."""
        name = child.name()
        if name not in self.names or self.names[name] is not child:
            raise Exception("Parameter %s is not my child; can't remove." % str(child))
        del self.names[name]
        self.childs.pop(self.childs.index(child))
        child.parentChanged(None)
        self.sigChildRemoved.emit(self, child)
        try:
            child.sigTreeStateChanged.disconnect(self.treeStateChanged)
        except TypeError:  ## already disconnected
            pass

    def clearChildren(self):
        """Remove all child parameters."""
        for ch in self.childs[:]:
            self.removeChild(ch)

    def children(self):  
        """Return a list of this parameter's children.
        Warning: this overrides QObject.children
        """
        return self.childs[:]
    
    def hasChildren(self):
        """Return True if this Parameter has children."""
        return len(self.childs) > 0

    def parentChanged(self, parent):
        """This method is called when the parameter's parent has changed.
        It may be useful to extend this method in subclasses."""
        self._parent = parent
        self.sigParentChanged.emit(self, parent)
        
    def parent(self):
        """Return the parent of this parameter."""
        return self._parent
        
    def remove(self):
        """Remove this parameter from its parent's child list"""
        parent = self.parent()
        if parent is None:
            raise Exception("Cannot remove; no parent.")
        parent.removeChild(self)

    def incrementName(self, name):
        ## return an unused name by adding a number to the name given
        base, num = re.match('(.*)(\d*)', name).groups()
        numLen = len(num)
        if numLen == 0:
            num = 2
            numLen = 1
        else:
            num = int(num)
        while True:
            newName = base + ("%%0%dd"%numLen) % num
            if newName not in self.names:
                return newName
            num += 1

    def __iter__(self):
        for ch in self.childs:
            yield ch

    def __getitem__(self, names):
        """Get the value of a child parameter. The name may also be a tuple giving
        the path to a sub-parameter::
        
            value = param[('child', 'grandchild')]
        """
        if not isinstance(names, tuple):
            names = (names,)
        return self.param(*names).value()

    def __setitem__(self, names, value):
        """Set the value of a child parameter. The name may also be a tuple giving
        the path to a sub-parameter::
        
            param[('child', 'grandchild')] = value
        """
        if isinstance(names, basestring):
            names = (names,)
        return self.param(*names).setValue(value)

    def param(self, *names):
        """Return a child parameter. 
        Accepts the name of the child or a tuple (path, to, child)"""
        try:
            param = self.names[names[0]]
        except KeyError:
            raise Exception("Parameter %s has no child named %s" % (self.name(), names[0]))
        
        if len(names) > 1:
            return param.param(*names[1:])
        else:
            return param
        
    def __repr__(self):
        return "<%s '%s' at 0x%x>" % (self.__class__.__name__, self.name(), id(self))
       
    def __getattr__(self, attr):
        ## Leaving this undocumented because I might like to remove it in the future..
        #print type(self), attr
        
        if 'names' not in self.__dict__:
            raise AttributeError(attr)
        if attr in self.names:
            import traceback
            traceback.print_stack()
            print("Warning: Use of Parameter.subParam is deprecated. Use Parameter.param(name) instead.")
            return self.param(attr)
        else:
            raise AttributeError(attr)
       
    def _renameChild(self, child, name):
        ## Only to be called from Parameter.rename
        if name in self.names:
            return child.name()
        self.names[name] = child
        del self.names[child.name()]
        return name

    def registerItem(self, item):
        self.items[item] = None
        
    def hide(self):
        """Hide this parameter. It and its children will no longer be visible in any ParameterTree
        widgets it is connected to."""
        self.show(False)
        
    def show(self, s=True):
        """Show this parameter. """
        self.opts['visible'] = s
        self.sigOptionsChanged.emit(self, {'visible': s})


    def treeChangeBlocker(self):
        """
        Return an object that can be used to temporarily block and accumulate
        sigTreeStateChanged signals. This is meant to be used when numerous changes are 
        about to be made to the tree and only one change signal should be
        emitted at the end.
        
        Example::

            with param.treeChangeBlocker():
                param.addChild(...)
                param.removeChild(...)
                param.setValue(...)
        """
        return SignalBlocker(self.blockTreeChangeSignal, self.unblockTreeChangeSignal)

    def blockTreeChangeSignal(self):
        """
        Used to temporarily block and accumulate tree change signals.
        *You must remember to unblock*, so it is advisable to use treeChangeBlocker() instead.
        """
        self.blockTreeChangeEmit += 1

    def unblockTreeChangeSignal(self):
        """Unblocks enission of sigTreeStateChanged and flushes the changes out through a single signal."""
        self.blockTreeChangeEmit -= 1
        self.emitTreeChanges()
        
        
    def treeStateChanged(self, param, changes):
        """
        Called when the state of any sub-parameter has changed. 
        
        ==========  ================================================================
        Arguments:
        param       The immediate child whose tree state has changed.
                    note that the change may have originated from a grandchild.
        changes     List of tuples describing all changes that have been made
                    in this event: (param, changeDescr, data)
        ==========  ================================================================
                     
        This function can be extended to react to tree state changes.
        """
        self.treeStateChanges.extend(changes)
        self.emitTreeChanges()
    
    def emitTreeChanges(self):
        if self.blockTreeChangeEmit == 0:
            changes = self.treeStateChanges
            self.treeStateChanges = []
            self.sigTreeStateChanged.emit(self, changes)


class SignalBlocker(object):
    def __init__(self, enterFn, exitFn):
        self.enterFn = enterFn
        self.exitFn = exitFn
        
    def __enter__(self):
        self.enterFn()
        
    def __exit__(self, exc_type, exc_value, tb):
        self.exitFn()
    
    
    
