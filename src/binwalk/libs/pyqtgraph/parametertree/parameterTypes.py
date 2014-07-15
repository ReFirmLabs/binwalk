from pyqtgraph.Qt import QtCore, QtGui
from pyqtgraph.python2_3 import asUnicode
from .Parameter import Parameter, registerParameterType
from .ParameterItem import ParameterItem
from pyqtgraph.widgets.SpinBox import SpinBox
from pyqtgraph.widgets.ColorButton import ColorButton
#from pyqtgraph.widgets.GradientWidget import GradientWidget ## creates import loop
import pyqtgraph as pg
import pyqtgraph.pixmaps as pixmaps
import os
from pyqtgraph.pgcollections import OrderedDict

class WidgetParameterItem(ParameterItem):
    """
    ParameterTree item with:
    
    * label in second column for displaying value
    * simple widget for editing value (displayed instead of label when item is selected)
    * button that resets value to default
    
    ================= =============================================================
    Registered Types:
    int               Displays a :class:`SpinBox <pyqtgraph.SpinBox>` in integer
                      mode.
    float             Displays a :class:`SpinBox <pyqtgraph.SpinBox>`.
    bool              Displays a QCheckBox
    str               Displays a QLineEdit
    color             Displays a :class:`ColorButton <pyqtgraph.ColorButton>`
    colormap          Displays a :class:`GradientWidget <pyqtgraph.GradientWidget>`
    ================= =============================================================
    
    This class can be subclassed by overriding makeWidget() to provide a custom widget.
    """
    def __init__(self, param, depth):
        ParameterItem.__init__(self, param, depth)
        
        self.hideWidget = True  ## hide edit widget, replace with label when not selected
                                ## set this to False to keep the editor widget always visible
        
        
        ## build widget into column 1 with a display label and default button.
        w = self.makeWidget()  
        self.widget = w
        self.eventProxy = EventProxy(w, self.widgetEventFilter)
        
        opts = self.param.opts
        if 'tip' in opts:
            w.setToolTip(opts['tip'])
        
        self.defaultBtn = QtGui.QPushButton()
        self.defaultBtn.setFixedWidth(20)
        self.defaultBtn.setFixedHeight(20)
        modDir = os.path.dirname(__file__)
        self.defaultBtn.setIcon(QtGui.QIcon(pixmaps.getPixmap('default')))
        self.defaultBtn.clicked.connect(self.defaultClicked)
        
        self.displayLabel = QtGui.QLabel()
        
        layout = QtGui.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.addWidget(w)
        layout.addWidget(self.displayLabel)
        layout.addWidget(self.defaultBtn)
        self.layoutWidget = QtGui.QWidget()
        self.layoutWidget.setLayout(layout)
        
        if w.sigChanged is not None:
            w.sigChanged.connect(self.widgetValueChanged)
            
        if hasattr(w, 'sigChanging'):
            w.sigChanging.connect(self.widgetValueChanging)
            
        ## update value shown in widget. 
        if opts.get('value', None) is not None:
            self.valueChanged(self, opts['value'], force=True)
        else:
            ## no starting value was given; use whatever the widget has
            self.widgetValueChanged()


    def makeWidget(self):
        """
        Return a single widget that should be placed in the second tree column.
        The widget must be given three attributes:
        
        ==========  ============================================================
        sigChanged  a signal that is emitted when the widget's value is changed
        value       a function that returns the value
        setValue    a function that sets the value
        ==========  ============================================================
            
        This is a good function to override in subclasses.
        """
        opts = self.param.opts
        t = opts['type']
        if t == 'int':
            defs = {
                'value': 0, 'min': None, 'max': None, 'int': True, 
                'step': 1.0, 'minStep': 1.0, 'dec': False, 
                'siPrefix': False, 'suffix': ''
            } 
            defs.update(opts)
            if 'limits' in opts:
                defs['bounds'] = opts['limits']
            w = SpinBox()
            w.setOpts(**defs)
            w.sigChanged = w.sigValueChanged
            w.sigChanging = w.sigValueChanging
        elif t == 'float':
            defs = {
                'value': 0, 'min': None, 'max': None, 
                'step': 1.0, 'dec': False, 
                'siPrefix': False, 'suffix': ''
            }
            defs.update(opts)
            if 'limits' in opts:
                defs['bounds'] = opts['limits']
            w = SpinBox()
            w.setOpts(**defs)
            w.sigChanged = w.sigValueChanged
            w.sigChanging = w.sigValueChanging
        elif t == 'bool':
            w = QtGui.QCheckBox()
            w.sigChanged = w.toggled
            w.value = w.isChecked
            w.setValue = w.setChecked
            self.hideWidget = False
        elif t == 'str':
            w = QtGui.QLineEdit()
            w.sigChanged = w.editingFinished
            w.value = lambda: asUnicode(w.text())
            w.setValue = lambda v: w.setText(asUnicode(v))
            w.sigChanging = w.textChanged
        elif t == 'color':
            w = ColorButton()
            w.sigChanged = w.sigColorChanged
            w.sigChanging = w.sigColorChanging
            w.value = w.color
            w.setValue = w.setColor
            self.hideWidget = False
            w.setFlat(True)
        elif t == 'colormap':
            from pyqtgraph.widgets.GradientWidget import GradientWidget ## need this here to avoid import loop
            w = GradientWidget(orientation='bottom')
            w.sigChanged = w.sigGradientChangeFinished
            w.sigChanging = w.sigGradientChanged
            w.value = w.colorMap
            w.setValue = w.setColorMap
            self.hideWidget = False
        else:
            raise Exception("Unknown type '%s'" % asUnicode(t))
        return w
        
    def widgetEventFilter(self, obj, ev):
        ## filter widget's events
        ## catch TAB to change focus
        ## catch focusOut to hide editor
        if ev.type() == ev.KeyPress:
            if ev.key() == QtCore.Qt.Key_Tab:
                self.focusNext(forward=True)
                return True ## don't let anyone else see this event
            elif ev.key() == QtCore.Qt.Key_Backtab:
                self.focusNext(forward=False)
                return True ## don't let anyone else see this event
            
        #elif ev.type() == ev.FocusOut:
            #self.hideEditor()
        return False
        
    def setFocus(self):
        self.showEditor()
        
    def isFocusable(self):
        return self.param.writable()        
        
    def valueChanged(self, param, val, force=False):
        ## called when the parameter's value has changed
        ParameterItem.valueChanged(self, param, val)
        self.widget.sigChanged.disconnect(self.widgetValueChanged)
        try:
            if force or val != self.widget.value():
                self.widget.setValue(val)
            self.updateDisplayLabel(val)  ## always make sure label is updated, even if values match!
        finally:
            self.widget.sigChanged.connect(self.widgetValueChanged)
        self.updateDefaultBtn()
        
    def updateDefaultBtn(self):
        ## enable/disable default btn 
        self.defaultBtn.setEnabled(not self.param.valueIsDefault() and self.param.writable())        

    def updateDisplayLabel(self, value=None):
        """Update the display label to reflect the value of the parameter."""
        if value is None:
            value = self.param.value()
        opts = self.param.opts
        if isinstance(self.widget, QtGui.QAbstractSpinBox):
            text = asUnicode(self.widget.lineEdit().text())
        elif isinstance(self.widget, QtGui.QComboBox):
            text = self.widget.currentText()
        else:
            text = asUnicode(value)
        self.displayLabel.setText(text)

    def widgetValueChanged(self):
        ## called when the widget's value has been changed by the user
        val = self.widget.value()
        newVal = self.param.setValue(val)

    def widgetValueChanging(self):
        """
        Called when the widget's value is changing, but not finalized.
        For example: editing text before pressing enter or changing focus.
        """
        pass
        
    def selected(self, sel):
        """Called when this item has been selected (sel=True) OR deselected (sel=False)"""
        ParameterItem.selected(self, sel)
        
        if self.widget is None:
            return
        if sel and self.param.writable():
            self.showEditor()
        elif self.hideWidget:
            self.hideEditor()

    def showEditor(self):
        self.widget.show()
        self.displayLabel.hide()
        self.widget.setFocus(QtCore.Qt.OtherFocusReason)

    def hideEditor(self):
        self.widget.hide()
        self.displayLabel.show()

    def limitsChanged(self, param, limits):
        """Called when the parameter's limits have changed"""
        ParameterItem.limitsChanged(self, param, limits)
        
        t = self.param.opts['type']
        if t == 'int' or t == 'float':
            self.widget.setOpts(bounds=limits)
        else:
            return  ## don't know what to do with any other types..

    def defaultChanged(self, param, value):
        self.updateDefaultBtn()

    def treeWidgetChanged(self):
        """Called when this item is added or removed from a tree."""
        ParameterItem.treeWidgetChanged(self)
        
        ## add all widgets for this item into the tree
        if self.widget is not None:
            tree = self.treeWidget()
            if tree is None:
                return
            tree.setItemWidget(self, 1, self.layoutWidget)
            self.displayLabel.hide()
            self.selected(False)            

    def defaultClicked(self):
        self.param.setToDefault()

    def optsChanged(self, param, opts):
        """Called when any options are changed that are not
        name, value, default, or limits"""
        #print "opts changed:", opts
        ParameterItem.optsChanged(self, param, opts)
        
        if 'readonly' in opts:
            self.updateDefaultBtn()
        
        ## If widget is a SpinBox, pass options straight through
        if isinstance(self.widget, SpinBox):
            if 'units' in opts and 'suffix' not in opts:
                opts['suffix'] = opts['units']
            self.widget.setOpts(**opts)
            self.updateDisplayLabel()
            
class EventProxy(QtCore.QObject):
    def __init__(self, qobj, callback):
        QtCore.QObject.__init__(self)
        self.callback = callback
        qobj.installEventFilter(self)
        
    def eventFilter(self, obj, ev):
        return self.callback(obj, ev)

        


class SimpleParameter(Parameter):
    itemClass = WidgetParameterItem
    
    def __init__(self, *args, **kargs):
        Parameter.__init__(self, *args, **kargs)
        
        ## override a few methods for color parameters
        if self.opts['type'] == 'color':
            self.value = self.colorValue
            self.saveState = self.saveColorState
    
    def colorValue(self):
        return pg.mkColor(Parameter.value(self))
    
    def saveColorState(self):
        state = Parameter.saveState(self)
        state['value'] = pg.colorTuple(self.value())
        return state
        
    
registerParameterType('int', SimpleParameter, override=True)
registerParameterType('float', SimpleParameter, override=True)
registerParameterType('bool', SimpleParameter, override=True)
registerParameterType('str', SimpleParameter, override=True)
registerParameterType('color', SimpleParameter, override=True)
registerParameterType('colormap', SimpleParameter, override=True)




class GroupParameterItem(ParameterItem):
    """
    Group parameters are used mainly as a generic parent item that holds (and groups!) a set
    of child parameters. It also provides a simple mechanism for displaying a button or combo
    that can be used to add new parameters to the group.
    """
    def __init__(self, param, depth):
        ParameterItem.__init__(self, param, depth)
        self.updateDepth(depth) 
                
        self.addItem = None
        if 'addText' in param.opts:
            addText = param.opts['addText']
            if 'addList' in param.opts:
                self.addWidget = QtGui.QComboBox()
                self.addWidget.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
                self.updateAddList()
                self.addWidget.currentIndexChanged.connect(self.addChanged)
            else:
                self.addWidget = QtGui.QPushButton(addText)
                self.addWidget.clicked.connect(self.addClicked)
            w = QtGui.QWidget()
            l = QtGui.QHBoxLayout()
            l.setContentsMargins(0,0,0,0)
            w.setLayout(l)
            l.addWidget(self.addWidget)
            l.addStretch()
            #l.addItem(QtGui.QSpacerItem(200, 10, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum))
            self.addWidgetBox = w
            self.addItem = QtGui.QTreeWidgetItem([])
            self.addItem.setFlags(QtCore.Qt.ItemIsEnabled)
            ParameterItem.addChild(self, self.addItem)
            
    def updateDepth(self, depth):
        ## Change item's appearance based on its depth in the tree
        ## This allows highest-level groups to be displayed more prominently.
        if depth == 0:
            for c in [0,1]:
                self.setBackground(c, QtGui.QBrush(QtGui.QColor(100,100,100)))
                self.setForeground(c, QtGui.QBrush(QtGui.QColor(220,220,255)))
                font = self.font(c)
                font.setBold(True)
                font.setPointSize(font.pointSize()+1)
                self.setFont(c, font)
                self.setSizeHint(0, QtCore.QSize(0, 25))
        else:
            for c in [0,1]:
                self.setBackground(c, QtGui.QBrush(QtGui.QColor(220,220,220)))
                font = self.font(c)
                font.setBold(True)
                #font.setPointSize(font.pointSize()+1)
                self.setFont(c, font)
                self.setSizeHint(0, QtCore.QSize(0, 20))
    
    def addClicked(self):
        """Called when "add new" button is clicked
        The parameter MUST have an 'addNew' method defined.
        """
        self.param.addNew()

    def addChanged(self):
        """Called when "add new" combo is changed
        The parameter MUST have an 'addNew' method defined.
        """
        if self.addWidget.currentIndex() == 0:
            return
        typ = asUnicode(self.addWidget.currentText())
        self.param.addNew(typ)
        self.addWidget.setCurrentIndex(0)

    def treeWidgetChanged(self):
        ParameterItem.treeWidgetChanged(self)
        self.treeWidget().setFirstItemColumnSpanned(self, True)
        if self.addItem is not None:
            self.treeWidget().setItemWidget(self.addItem, 0, self.addWidgetBox)
            self.treeWidget().setFirstItemColumnSpanned(self.addItem, True)
        
    def addChild(self, child):  ## make sure added childs are actually inserted before add btn
        if self.addItem is not None:
            ParameterItem.insertChild(self, self.childCount()-1, child)
        else:
            ParameterItem.addChild(self, child)
            
    def optsChanged(self, param, changed):
        if 'addList' in changed:
            self.updateAddList()
                
    def updateAddList(self):
        self.addWidget.blockSignals(True)
        try:
            self.addWidget.clear()
            self.addWidget.addItem(self.param.opts['addText'])
            for t in self.param.opts['addList']:
                self.addWidget.addItem(t)
        finally:
            self.addWidget.blockSignals(False)
            
class GroupParameter(Parameter):
    """
    Group parameters are used mainly as a generic parent item that holds (and groups!) a set
    of child parameters. 
    
    It also provides a simple mechanism for displaying a button or combo
    that can be used to add new parameters to the group. To enable this, the group 
    must be initialized with the 'addText' option (the text will be displayed on
    a button which, when clicked, will cause addNew() to be called). If the 'addList'
    option is specified as well, then a dropdown-list of addable items will be displayed
    instead of a button.
    """
    itemClass = GroupParameterItem

    def addNew(self, typ=None):
        """
        This method is called when the user has requested to add a new item to the group.
        """
        raise Exception("Must override this function in subclass.")
    
    def setAddList(self, vals):
        """Change the list of options available for the user to add to the group."""
        self.setOpts(addList=vals)

    

registerParameterType('group', GroupParameter, override=True)





class ListParameterItem(WidgetParameterItem):
    """
    WidgetParameterItem subclass providing comboBox that lets the user select from a list of options.
    
    """
    def __init__(self, param, depth):
        self.targetValue = None
        WidgetParameterItem.__init__(self, param, depth)
        
        
    def makeWidget(self):
        opts = self.param.opts
        t = opts['type']
        w = QtGui.QComboBox()
        w.setMaximumHeight(20)  ## set to match height of spin box and line edit
        w.sigChanged = w.currentIndexChanged
        w.value = self.value
        w.setValue = self.setValue
        self.widget = w  ## needs to be set before limits are changed
        self.limitsChanged(self.param, self.param.opts['limits'])
        if len(self.forward) > 0:
            self.setValue(self.param.value())
        return w
        
    def value(self):
        key = asUnicode(self.widget.currentText())
        
        return self.forward.get(key, None)
            
    def setValue(self, val):
        self.targetValue = val
        if val not in self.reverse[0]:
            self.widget.setCurrentIndex(0)
        else:
            key = self.reverse[1][self.reverse[0].index(val)]
            ind = self.widget.findText(key)
            self.widget.setCurrentIndex(ind)

    def limitsChanged(self, param, limits):
        # set up forward / reverse mappings for name:value
        
        if len(limits) == 0:
            limits = ['']  ## Can never have an empty list--there is always at least a singhe blank item.
        
        self.forward, self.reverse = ListParameter.mapping(limits)
        try:
            self.widget.blockSignals(True)
            val = self.targetValue  #asUnicode(self.widget.currentText())
            
            self.widget.clear()
            for k in self.forward:
                self.widget.addItem(k)
                if k == val:
                    self.widget.setCurrentIndex(self.widget.count()-1)
                    self.updateDisplayLabel()
        finally:
            self.widget.blockSignals(False)
            


class ListParameter(Parameter):
    itemClass = ListParameterItem

    def __init__(self, **opts):
        self.forward = OrderedDict()  ## {name: value, ...}
        self.reverse = ([], [])       ## ([value, ...], [name, ...])
        
        ## Parameter uses 'limits' option to define the set of allowed values
        if 'values' in opts:
            opts['limits'] = opts['values']
        if opts.get('limits', None) is None:
            opts['limits'] = []
        Parameter.__init__(self, **opts)
        self.setLimits(opts['limits'])
        
    def setLimits(self, limits):
        self.forward, self.reverse = self.mapping(limits)
        
        Parameter.setLimits(self, limits)
        #print self.name(), self.value(), limits
        if len(self.reverse) > 0 and self.value() not in self.reverse[0]:
            self.setValue(self.reverse[0][0])
            
    #def addItem(self, name, value=None):
        #if name in self.forward:
            #raise Exception("Name '%s' is already in use for this parameter" % name)
        #limits = self.opts['limits']
        #if isinstance(limits, dict):
            #limits = limits.copy()
            #limits[name] = value
            #self.setLimits(limits)
        #else:
            #if value is not None:
                #raise Exception  ## raise exception or convert to dict?
            #limits = limits[:]
            #limits.append(name)
        ## what if limits == None?
            
    @staticmethod
    def mapping(limits):
        ## Return forward and reverse mapping objects given a limit specification
        forward = OrderedDict()  ## {name: value, ...}
        reverse = ([], [])       ## ([value, ...], [name, ...])
        if isinstance(limits, dict):
            for k, v in limits.items():
                forward[k] = v
                reverse[0].append(v)
                reverse[1].append(k)
        else:
            for v in limits:
                n = asUnicode(v)
                forward[n] = v
                reverse[0].append(v)
                reverse[1].append(n)
        return forward, reverse

registerParameterType('list', ListParameter, override=True)



class ActionParameterItem(ParameterItem):
    def __init__(self, param, depth):
        ParameterItem.__init__(self, param, depth)
        self.layoutWidget = QtGui.QWidget()
        self.layout = QtGui.QHBoxLayout()
        self.layoutWidget.setLayout(self.layout)
        self.button = QtGui.QPushButton(param.name())
        #self.layout.addSpacing(100)
        self.layout.addWidget(self.button)
        self.layout.addStretch()
        self.button.clicked.connect(self.buttonClicked)
        param.sigNameChanged.connect(self.paramRenamed)
        self.setText(0, '')
        
    def treeWidgetChanged(self):
        ParameterItem.treeWidgetChanged(self)
        tree = self.treeWidget()
        if tree is None:
            return
        
        tree.setFirstItemColumnSpanned(self, True)
        tree.setItemWidget(self, 0, self.layoutWidget)
        
    def paramRenamed(self, param, name):
        self.button.setText(name)
        
    def buttonClicked(self):
        self.param.activate()
        
class ActionParameter(Parameter):
    """Used for displaying a button within the tree."""
    itemClass = ActionParameterItem
    sigActivated = QtCore.Signal(object)
    
    def activate(self):
        self.sigActivated.emit(self)
        self.emitStateChanged('activated', None)
        
registerParameterType('action', ActionParameter, override=True)



class TextParameterItem(WidgetParameterItem):
    def __init__(self, param, depth):
        WidgetParameterItem.__init__(self, param, depth)
        self.hideWidget = False
        self.subItem = QtGui.QTreeWidgetItem()
        self.addChild(self.subItem)

    def treeWidgetChanged(self):
        ## TODO: fix so that superclass method can be called
        ## (WidgetParameter should just natively support this style)
        #WidgetParameterItem.treeWidgetChanged(self)
        self.treeWidget().setFirstItemColumnSpanned(self.subItem, True)
        self.treeWidget().setItemWidget(self.subItem, 0, self.textBox)
        
        # for now, these are copied from ParameterItem.treeWidgetChanged
        self.setHidden(not self.param.opts.get('visible', True))
        self.setExpanded(self.param.opts.get('expanded', True))
        
    def makeWidget(self):
        self.textBox = QtGui.QTextEdit()
        self.textBox.setMaximumHeight(100)
        self.textBox.value = lambda: str(self.textBox.toPlainText())
        self.textBox.setValue = self.textBox.setPlainText
        self.textBox.sigChanged = self.textBox.textChanged
        return self.textBox
        
class TextParameter(Parameter):
    """Editable string; displayed as large text box in the tree."""
    itemClass = TextParameterItem

    
    
registerParameterType('text', TextParameter, override=True)
