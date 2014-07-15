# -*- coding: utf-8 -*-
from pyqtgraph.Qt import QtGui, QtCore
from pyqtgraph.python2_3 import asUnicode
from pyqtgraph.SignalProxy import SignalProxy

import pyqtgraph.functions as fn
from math import log
from decimal import Decimal as D  ## Use decimal to avoid accumulating floating-point errors
from decimal import *
import weakref

__all__ = ['SpinBox']
class SpinBox(QtGui.QAbstractSpinBox):
    """
    **Bases:** QtGui.QAbstractSpinBox
    
    QSpinBox widget on steroids. Allows selection of numerical value, with extra features:
    
    - SI prefix notation (eg, automatically display "300 mV" instead of "0.003 V")
    - Float values with linear and decimal stepping (1-9, 10-90, 100-900, etc.)
    - Option for unbounded values
    - Delayed signals (allows multiple rapid changes with only one change signal)
    
    =============================  ==============================================
    **Signals:**
    valueChanged(value)            Same as QSpinBox; emitted every time the value 
                                   has changed.
    sigValueChanged(self)          Emitted when value has changed, but also combines
                                   multiple rapid changes into one signal (eg, 
                                   when rolling the mouse wheel).
    sigValueChanging(self, value)  Emitted immediately for all value changes.
    =============================  ==============================================
    """
    
    ## There's a PyQt bug that leaks a reference to the 
    ## QLineEdit returned from QAbstractSpinBox.lineEdit()
    ## This makes it possible to crash the entire program 
    ## by making accesses to the LineEdit after the spinBox has been deleted.
    ## I have no idea how to get around this..
    
    
    valueChanged = QtCore.Signal(object)     # (value)  for compatibility with QSpinBox
    sigValueChanged = QtCore.Signal(object)  # (self)
    sigValueChanging = QtCore.Signal(object, object)  # (self, value)  sent immediately; no delay.
    
    def __init__(self, parent=None, value=0.0, **kwargs):
        """
        ============== ========================================================================
        **Arguments:**
        parent         Sets the parent widget for this SpinBox (optional)
        value          (float/int) initial value
        bounds         (min,max) Minimum and maximum values allowed in the SpinBox. 
                       Either may be None to leave the value unbounded.
        suffix         (str) suffix (units) to display after the numerical value
        siPrefix       (bool) If True, then an SI prefix is automatically prepended
                       to the units and the value is scaled accordingly. For example,
                       if value=0.003 and suffix='V', then the SpinBox will display
                       "300 mV" (but a call to SpinBox.value will still return 0.003).
        step           (float) The size of a single step. This is used when clicking the up/
                       down arrows, when rolling the mouse wheel, or when pressing 
                       keyboard arrows while the widget has keyboard focus. Note that
                       the interpretation of this value is different when specifying
                       the 'dec' argument.
        dec            (bool) If True, then the step value will be adjusted to match 
                       the current size of the variable (for example, a value of 15
                       might step in increments of 1 whereas a value of 1500 would
                       step in increments of 100). In this case, the 'step' argument
                       is interpreted *relative* to the current value. The most common
                       'step' values when dec=True are 0.1, 0.2, 0.5, and 1.0.
        minStep        (float) When dec=True, this specifies the minimum allowable step size.
        int            (bool) if True, the value is forced to integer type
        decimals       (int) Number of decimal values to display
        ============== ========================================================================
        """
        QtGui.QAbstractSpinBox.__init__(self, parent)
        self.lastValEmitted = None
        self.lastText = ''
        self.textValid = True  ## If false, we draw a red border
        self.setMinimumWidth(0)
        self.setMaximumHeight(20)
        self.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred)
        self.opts = {
            'bounds': [None, None],
            
            ## Log scaling options   #### Log mode is no longer supported.
            #'step': 0.1,
            #'minStep': 0.001,
            #'log': True,
            #'dec': False,
            
            ## decimal scaling option - example
            #'step': 0.1,    
            #'minStep': .001,    
            #'log': False,
            #'dec': True,
           
            ## normal arithmetic step
            'step': D('0.01'),  ## if 'dec' is false, the spinBox steps by 'step' every time
                                ## if 'dec' is True, the step size is relative to the value
                                ## 'step' needs to be an integral divisor of ten, ie 'step'*n=10 for some integer value of n (but only if dec is True)
            'log': False,
            'dec': False,   ## if true, does decimal stepping. ie from 1-10 it steps by 'step', from 10 to 100 it steps by 10*'step', etc. 
                            ## if true, minStep must be set in order to cross zero.
            
            
            'int': False, ## Set True to force value to be integer
            
            'suffix': '',
            'siPrefix': False,   ## Set to True to display numbers with SI prefix (ie, 100pA instead of 1e-10A)
            
            'delay': 0.3, ## delay sending wheel update signals for 300ms
            
            'delayUntilEditFinished': True,   ## do not send signals until text editing has finished
            
            ## for compatibility with QDoubleSpinBox and QSpinBox
            'decimals': 2,
            
        }
        
        self.decOpts = ['step', 'minStep']
        
        self.val = D(asUnicode(value))  ## Value is precise decimal. Ordinary math not allowed.
        self.updateText()
        self.skipValidate = False
        self.setCorrectionMode(self.CorrectToPreviousValue)
        self.setKeyboardTracking(False)
        self.setOpts(**kwargs)
        
        
        self.editingFinished.connect(self.editingFinishedEvent)
        self.proxy = SignalProxy(self.sigValueChanging, slot=self.delayedChange, delay=self.opts['delay'])
        
    def event(self, ev):
        ret = QtGui.QAbstractSpinBox.event(self, ev)
        if ev.type() == QtCore.QEvent.KeyPress and ev.key() == QtCore.Qt.Key_Return:
            ret = True  ## For some reason, spinbox pretends to ignore return key press
        return ret
        
    ##lots of config options, just gonna stuff 'em all in here rather than do the get/set crap.
    def setOpts(self, **opts):
        """
        Changes the behavior of the SpinBox. Accepts most of the arguments 
        allowed in :func:`__init__ <pyqtgraph.SpinBox.__init__>`.
        
        """
        #print opts
        for k in opts:
            if k == 'bounds':
                #print opts[k]
                self.setMinimum(opts[k][0], update=False)
                self.setMaximum(opts[k][1], update=False)
                #for i in [0,1]:
                    #if opts[k][i] is None:
                        #self.opts[k][i] = None
                    #else:
                        #self.opts[k][i] = D(unicode(opts[k][i]))
            elif k in ['step', 'minStep']:
                self.opts[k] = D(asUnicode(opts[k]))
            elif k == 'value':
                pass   ## don't set value until bounds have been set
            else:
                self.opts[k] = opts[k]
        if 'value' in opts:
            self.setValue(opts['value'])
            
        ## If bounds have changed, update value to match
        if 'bounds' in opts and 'value' not in opts:
            self.setValue()   
            
        ## sanity checks:
        if self.opts['int']:
            if 'step' in opts:
                step = opts['step']
                ## not necessary..
                #if int(step) != step:
                    #raise Exception('Integer SpinBox must have integer step size.')
            else:
                self.opts['step'] = int(self.opts['step'])
            
            if 'minStep' in opts:
                step = opts['minStep']
                if int(step) != step:
                    raise Exception('Integer SpinBox must have integer minStep size.')
            else:
                ms = int(self.opts.get('minStep', 1))
                if ms < 1:
                    ms = 1
                self.opts['minStep'] = ms
        
        if 'delay' in opts:
            self.proxy.setDelay(opts['delay'])
        
        self.updateText()



    def setMaximum(self, m, update=True):
        """Set the maximum allowed value (or None for no limit)"""
        if m is not None:
            m = D(asUnicode(m))
        self.opts['bounds'][1] = m
        if update:
            self.setValue()
    
    def setMinimum(self, m, update=True):
        """Set the minimum allowed value (or None for no limit)"""
        if m is not None:
            m = D(asUnicode(m))
        self.opts['bounds'][0] = m
        if update:
            self.setValue()
        
    def setPrefix(self, p):
        self.setOpts(prefix=p)
    
    def setRange(self, r0, r1):
        self.setOpts(bounds = [r0,r1])
        
    def setProperty(self, prop, val):
        ## for QSpinBox compatibility
        if prop == 'value':
            #if type(val) is QtCore.QVariant:
                #val = val.toDouble()[0]
            self.setValue(val)
        else:
            print("Warning: SpinBox.setProperty('%s', ..) not supported." % prop)

    def setSuffix(self, suf):
        self.setOpts(suffix=suf)

    def setSingleStep(self, step):
        self.setOpts(step=step)
        
    def setDecimals(self, decimals):
        self.setOpts(decimals=decimals)

    def value(self):
        """
        Return the value of this SpinBox.
        
        """
        if self.opts['int']:
            return int(self.val)
        else:
            return float(self.val)

    def setValue(self, value=None, update=True, delaySignal=False):
        """
        Set the value of this spin. 
        If the value is out of bounds, it will be clipped to the nearest boundary.
        If the spin is integer type, the value will be coerced to int.
        Returns the actual value set.
        
        If value is None, then the current value is used (this is for resetting
        the value after bounds, etc. have changed)
        """
        
        if value is None:
            value = self.value()
        
        bounds = self.opts['bounds']
        if bounds[0] is not None and value < bounds[0]:
            value = bounds[0]
        if bounds[1] is not None and value > bounds[1]:
            value = bounds[1]

        if self.opts['int']:
            value = int(value)

        value = D(asUnicode(value))
        if value == self.val:
            return
        prev = self.val
        
        self.val = value
        if update:
            self.updateText(prev=prev)
            
        self.sigValueChanging.emit(self, float(self.val))  ## change will be emitted in 300ms if there are no subsequent changes.
        if not delaySignal:
            self.emitChanged()
        
        return value

    
    def emitChanged(self):
        self.lastValEmitted = self.val
        self.valueChanged.emit(float(self.val))
        self.sigValueChanged.emit(self)
    
    def delayedChange(self):
        try:
            if self.val != self.lastValEmitted:
                self.emitChanged()
        except RuntimeError:
            pass  ## This can happen if we try to handle a delayed signal after someone else has already deleted the underlying C++ object.
    
    def widgetGroupInterface(self):
        return (self.valueChanged, SpinBox.value, SpinBox.setValue)
    
    def sizeHint(self):
        return QtCore.QSize(120, 0)
    
    
    def stepEnabled(self):
        return self.StepUpEnabled | self.StepDownEnabled        
    
    #def fixup(self, *args):
        #print "fixup:", args
    
    def stepBy(self, n):
        n = D(int(n))   ## n must be integral number of steps.
        s = [D(-1), D(1)][n >= 0]  ## determine sign of step
        val = self.val
        
        for i in range(int(abs(n))):
            
            if self.opts['log']:
                raise Exception("Log mode no longer supported.")
            #    step = abs(val) * self.opts['step']
            #    if 'minStep' in self.opts:
            #        step = max(step, self.opts['minStep'])
            #    val += step * s
            if self.opts['dec']:
                if val == 0:
                    step = self.opts['minStep']
                    exp = None
                else:
                    vs = [D(-1), D(1)][val >= 0]
                    #exp = D(int(abs(val*(D('1.01')**(s*vs))).log10()))
                    fudge = D('1.01')**(s*vs) ## fudge factor. at some places, the step size depends on the step sign.
                    exp = abs(val * fudge).log10().quantize(1, ROUND_FLOOR)
                    step = self.opts['step'] * D(10)**exp
                if 'minStep' in self.opts:
                    step = max(step, self.opts['minStep'])
                val += s * step
                #print "Exp:", exp, "step", step, "val", val
            else:
                val += s*self.opts['step']
                
            if 'minStep' in self.opts and abs(val) < self.opts['minStep']:
                val = D(0)
        self.setValue(val, delaySignal=True)  ## note all steps (arrow buttons, wheel, up/down keys..) emit delayed signals only.
        

    def valueInRange(self, value):
        bounds = self.opts['bounds']
        if bounds[0] is not None and value < bounds[0]:
            return False
        if bounds[1] is not None and value > bounds[1]:
            return False
        if self.opts.get('int', False):
            if int(value) != value:
                return False
        return True
        

    def updateText(self, prev=None):
        #print "Update text."
        self.skipValidate = True
        if self.opts['siPrefix']:
            if self.val == 0 and prev is not None:
                (s, p) = fn.siScale(prev)
                txt = "0.0 %s%s" % (p, self.opts['suffix'])
            else:
                txt = fn.siFormat(float(self.val), suffix=self.opts['suffix'])
        else:
            txt = '%g%s' % (self.val , self.opts['suffix'])
        self.lineEdit().setText(txt)
        self.lastText = txt
        self.skipValidate = False
        
    def validate(self, strn, pos):
        if self.skipValidate:
            #print "skip validate"
            #self.textValid = False
            ret = QtGui.QValidator.Acceptable
        else:
            try:
                ## first make sure we didn't mess with the suffix
                suff = self.opts.get('suffix', '')
                if len(suff) > 0 and asUnicode(strn)[-len(suff):] != suff:
                    #print '"%s" != "%s"' % (unicode(strn)[-len(suff):], suff)
                    ret = QtGui.QValidator.Invalid
                    
                ## next see if we actually have an interpretable value
                else:
                    val = self.interpret()
                    if val is False:
                        #print "can't interpret"
                        #self.setStyleSheet('SpinBox {border: 2px solid #C55;}')
                        #self.textValid = False
                        ret = QtGui.QValidator.Intermediate
                    else:
                        if self.valueInRange(val):
                            if not self.opts['delayUntilEditFinished']:
                                self.setValue(val, update=False)
                            #print "  OK:", self.val
                            #self.setStyleSheet('')
                            #self.textValid = True
                            
                            ret = QtGui.QValidator.Acceptable
                        else:
                            ret = QtGui.QValidator.Intermediate
                        
            except:
                #print "  BAD"
                #import sys
                #sys.excepthook(*sys.exc_info())
                #self.textValid = False
                #self.setStyleSheet('SpinBox {border: 2px solid #C55;}')
                ret = QtGui.QValidator.Intermediate
            
        ## draw / clear border
        if ret == QtGui.QValidator.Intermediate:
            self.textValid = False
        elif ret == QtGui.QValidator.Acceptable:
            self.textValid = True
        ## note: if text is invalid, we don't change the textValid flag 
        ## since the text will be forced to its previous state anyway
        self.update()
        
        ## support 2 different pyqt APIs. Bleh.
        if hasattr(QtCore, 'QString'):
            return (ret, pos)
        else:
            return (ret, strn, pos)
        
    def paintEvent(self, ev):
        QtGui.QAbstractSpinBox.paintEvent(self, ev)
        
        ## draw red border if text is invalid
        if not self.textValid:
            p = QtGui.QPainter(self)
            p.setRenderHint(p.Antialiasing)
            p.setPen(fn.mkPen((200,50,50), width=2))
            p.drawRoundedRect(self.rect().adjusted(2, 2, -2, -2), 4, 4)
            p.end()


    def interpret(self):
        """Return value of text. Return False if text is invalid, raise exception if text is intermediate"""
        strn = self.lineEdit().text()
        suf = self.opts['suffix']
        if len(suf) > 0:
            if strn[-len(suf):] != suf:
                return False
            #raise Exception("Units are invalid.")
            strn = strn[:-len(suf)]
        try:
            val = fn.siEval(strn)
        except:
            #sys.excepthook(*sys.exc_info())
            #print "invalid"
            return False
        #print val
        return val
        
    #def interpretText(self, strn=None):
        #print "Interpret:", strn
        #if strn is None:
            #strn = self.lineEdit().text()
        #self.setValue(siEval(strn), update=False)
        ##QtGui.QAbstractSpinBox.interpretText(self)
        
        
    def editingFinishedEvent(self):
        """Edit has finished; set value."""
        #print "Edit finished."
        if asUnicode(self.lineEdit().text()) == self.lastText:
            #print "no text change."
            return
        try:
            val = self.interpret()
        except:
            return
        
        if val is False:
            #print "value invalid:", str(self.lineEdit().text())
            return
        if val == self.val:
            #print "no value change:", val, self.val
            return
        self.setValue(val, delaySignal=False)  ## allow text update so that values are reformatted pretty-like
        
    #def textChanged(self):
        #print "Text changed."
        
        
### Drop-in replacement for SpinBox; just for crash-testing
#class SpinBox(QtGui.QDoubleSpinBox):
    #valueChanged = QtCore.Signal(object)     # (value)  for compatibility with QSpinBox
    #sigValueChanged = QtCore.Signal(object)  # (self)
    #sigValueChanging = QtCore.Signal(object)  # (value)
    #def __init__(self, parent=None, *args, **kargs):
        #QtGui.QSpinBox.__init__(self, parent)
    
    #def  __getattr__(self, attr):
        #return lambda *args, **kargs: None
        
    #def widgetGroupInterface(self):
        #return (self.valueChanged, SpinBox.value, SpinBox.setValue)
    
