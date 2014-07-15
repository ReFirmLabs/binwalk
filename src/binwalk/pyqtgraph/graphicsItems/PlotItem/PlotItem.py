# -*- coding: utf-8 -*-
"""
PlotItem.py -  Graphics item implementing a scalable ViewBox with plotting powers.
Copyright 2010  Luke Campagnola
Distributed under MIT/X11 license. See license.txt for more infomation.

This class is one of the workhorses of pyqtgraph. It implements a graphics item with 
plots, labels, and scales which can be viewed inside a QGraphicsScene. If you want
a widget that can be added to your GUI, see PlotWidget instead.

This class is very heavily featured:
  - Automatically creates and manages PlotCurveItems
  - Fast display and update of plots
  - Manages zoom/pan ViewBox, scale, and label elements
  - Automatic scaling when data changes
  - Control panel with a huge feature set including averaging, decimation,
    display, power spectrum, svg/png export, plot linking, and more.
"""
from pyqtgraph.Qt import QtGui, QtCore, QtSvg, USE_PYSIDE
import pyqtgraph.pixmaps

if USE_PYSIDE:
    from .plotConfigTemplate_pyside import *
else:
    from .plotConfigTemplate_pyqt import *

import pyqtgraph.functions as fn
from pyqtgraph.widgets.FileDialog import FileDialog
import weakref
import numpy as np
import os
from .. PlotDataItem import PlotDataItem
from .. ViewBox import ViewBox
from .. AxisItem import AxisItem
from .. LabelItem import LabelItem
from .. LegendItem import LegendItem
from .. GraphicsWidget import GraphicsWidget
from .. ButtonItem import ButtonItem
from .. InfiniteLine import InfiniteLine
from pyqtgraph.WidgetGroup import WidgetGroup

__all__ = ['PlotItem']

try:
    from metaarray import *
    HAVE_METAARRAY = True
except:
    HAVE_METAARRAY = False




class PlotItem(GraphicsWidget):
    
    """
    **Bases:** :class:`GraphicsWidget <pyqtgraph.GraphicsWidget>`
    
    Plot graphics item that can be added to any graphics scene. Implements axes, titles, and interactive viewbox. 
    PlotItem also provides some basic analysis functionality that may be accessed from the context menu.
    Use :func:`plot() <pyqtgraph.PlotItem.plot>` to create a new PlotDataItem and add it to the view.
    Use :func:`addItem() <pyqtgraph.PlotItem.addItem>` to add any QGraphicsItem to the view.
    
    This class wraps several methods from its internal ViewBox:
    :func:`setXRange <pyqtgraph.ViewBox.setXRange>`,
    :func:`setYRange <pyqtgraph.ViewBox.setYRange>`,
    :func:`setRange <pyqtgraph.ViewBox.setRange>`,
    :func:`autoRange <pyqtgraph.ViewBox.autoRange>`,
    :func:`setXLink <pyqtgraph.ViewBox.setXLink>`,
    :func:`setYLink <pyqtgraph.ViewBox.setYLink>`,
    :func:`setAutoPan <pyqtgraph.ViewBox.setAutoPan>`,
    :func:`setAutoVisible <pyqtgraph.ViewBox.setAutoVisible>`,
    :func:`viewRect <pyqtgraph.ViewBox.viewRect>`,
    :func:`viewRange <pyqtgraph.ViewBox.viewRange>`,
    :func:`setMouseEnabled <pyqtgraph.ViewBox.setMouseEnabled>`,
    :func:`enableAutoRange <pyqtgraph.ViewBox.enableAutoRange>`,
    :func:`disableAutoRange <pyqtgraph.ViewBox.disableAutoRange>`,
    :func:`setAspectLocked <pyqtgraph.ViewBox.setAspectLocked>`,
    :func:`invertY <pyqtgraph.ViewBox.invertY>`,
    :func:`register <pyqtgraph.ViewBox.register>`,
    :func:`unregister <pyqtgraph.ViewBox.unregister>`
    
    The ViewBox itself can be accessed by calling :func:`getViewBox() <pyqtgraph.PlotItem.getViewBox>` 
    
    ==================== =======================================================================
    **Signals**
    sigYRangeChanged     wrapped from :class:`ViewBox <pyqtgraph.ViewBox>`
    sigXRangeChanged     wrapped from :class:`ViewBox <pyqtgraph.ViewBox>`
    sigRangeChanged      wrapped from :class:`ViewBox <pyqtgraph.ViewBox>`
    ==================== =======================================================================
    """
    
    sigRangeChanged = QtCore.Signal(object, object)    ## Emitted when the ViewBox range has changed
    sigYRangeChanged = QtCore.Signal(object, object)   ## Emitted when the ViewBox Y range has changed
    sigXRangeChanged = QtCore.Signal(object, object)   ## Emitted when the ViewBox X range has changed
    
    
    lastFileDir = None
    managers = {}
    
    def __init__(self, parent=None, name=None, labels=None, title=None, viewBox=None, axisItems=None, enableMenu=True, **kargs):
        """
        Create a new PlotItem. All arguments are optional.
        Any extra keyword arguments are passed to PlotItem.plot().
        
        ==============  ==========================================================================================
        **Arguments**
        *title*         Title to display at the top of the item. Html is allowed.
        *labels*        A dictionary specifying the axis labels to display::
                   
                            {'left': (args), 'bottom': (args), ...}
                     
                        The name of each axis and the corresponding arguments are passed to 
                        :func:`PlotItem.setLabel() <pyqtgraph.PlotItem.setLabel>`
                        Optionally, PlotItem my also be initialized with the keyword arguments left,
                        right, top, or bottom to achieve the same effect.
        *name*          Registers a name for this view so that others may link to it
        *viewBox*       If specified, the PlotItem will be constructed with this as its ViewBox.
        *axisItems*     Optional dictionary instructing the PlotItem to use pre-constructed items
                        for its axes. The dict keys must be axis names ('left', 'bottom', 'right', 'top')
                        and the values must be instances of AxisItem (or at least compatible with AxisItem).
        ==============  ==========================================================================================
        """
        
        GraphicsWidget.__init__(self, parent)
        
        self.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        
        ## Set up control buttons
        path = os.path.dirname(__file__)
        #self.autoImageFile = os.path.join(path, 'auto.png')
        #self.lockImageFile = os.path.join(path, 'lock.png')
        self.autoBtn = ButtonItem(pyqtgraph.pixmaps.getPixmap('auto'), 14, self)
        self.autoBtn.mode = 'auto'
        self.autoBtn.clicked.connect(self.autoBtnClicked)
        #self.autoBtn.hide()
        self.buttonsHidden = False ## whether the user has requested buttons to be hidden
        self.mouseHovering = False
        
        self.layout = QtGui.QGraphicsGridLayout()
        self.layout.setContentsMargins(1,1,1,1)
        self.setLayout(self.layout)
        self.layout.setHorizontalSpacing(0)
        self.layout.setVerticalSpacing(0)
        
        if viewBox is None:
            viewBox = ViewBox()
        self.vb = viewBox
        self.vb.sigStateChanged.connect(self.viewStateChanged)
        self.setMenuEnabled(enableMenu, enableMenu) ## en/disable plotitem and viewbox menus
        
        if name is not None:
            self.vb.register(name)
        self.vb.sigRangeChanged.connect(self.sigRangeChanged)
        self.vb.sigXRangeChanged.connect(self.sigXRangeChanged)
        self.vb.sigYRangeChanged.connect(self.sigYRangeChanged)
        
        self.layout.addItem(self.vb, 2, 1)
        self.alpha = 1.0
        self.autoAlpha = True
        self.spectrumMode = False
        
        self.legend = None
        
        ## Create and place axis items
        if axisItems is None:
            axisItems = {}
        self.axes = {}
        for k, pos in (('top', (1,1)), ('bottom', (3,1)), ('left', (2,0)), ('right', (2,2))):
            axis = axisItems.get(k, AxisItem(orientation=k))
            axis.linkToView(self.vb)
            self.axes[k] = {'item': axis, 'pos': pos}
            self.layout.addItem(axis, *pos)
            axis.setZValue(-1000)
            axis.setFlag(axis.ItemNegativeZStacksBehindParent)
        
        self.titleLabel = LabelItem('', size='11pt')
        self.layout.addItem(self.titleLabel, 0, 1)
        self.setTitle(None)  ## hide
        
        
        for i in range(4):
            self.layout.setRowPreferredHeight(i, 0)
            self.layout.setRowMinimumHeight(i, 0)
            self.layout.setRowSpacing(i, 0)
            self.layout.setRowStretchFactor(i, 1)
            
        for i in range(3):
            self.layout.setColumnPreferredWidth(i, 0)
            self.layout.setColumnMinimumWidth(i, 0)
            self.layout.setColumnSpacing(i, 0)
            self.layout.setColumnStretchFactor(i, 1)
        self.layout.setRowStretchFactor(2, 100)
        self.layout.setColumnStretchFactor(1, 100)
        

        ## Wrap a few methods from viewBox
        for m in [
            'setXRange', 'setYRange', 'setXLink', 'setYLink', 'setAutoPan', 'setAutoVisible',
            'setRange', 'autoRange', 'viewRect', 'viewRange', 'setMouseEnabled',
            'enableAutoRange', 'disableAutoRange', 'setAspectLocked', 'invertY',
            'register', 'unregister']:  ## NOTE: If you update this list, please update the class docstring as well.
            setattr(self, m, getattr(self.vb, m))
            
        self.items = []
        self.curves = []
        self.itemMeta = weakref.WeakKeyDictionary()
        self.dataItems = []
        self.paramList = {}
        self.avgCurves = {}
        
        ### Set up context menu
        
        w = QtGui.QWidget()
        self.ctrl = c = Ui_Form()
        c.setupUi(w)
        dv = QtGui.QDoubleValidator(self)
        
        menuItems = [
            ('Transforms', c.transformGroup),
            ('Downsample', c.decimateGroup),
            ('Average', c.averageGroup),
            ('Alpha', c.alphaGroup),
            ('Grid', c.gridGroup),
            ('Points', c.pointsGroup),
        ]
        
        
        self.ctrlMenu = QtGui.QMenu()
        
        self.ctrlMenu.setTitle('Plot Options')
        self.subMenus = []
        for name, grp in menuItems:
            sm = QtGui.QMenu(name)
            act = QtGui.QWidgetAction(self)
            act.setDefaultWidget(grp)
            sm.addAction(act)
            self.subMenus.append(sm)
            self.ctrlMenu.addMenu(sm)
        
        self.stateGroup = WidgetGroup()
        for name, w in menuItems:
            self.stateGroup.autoAdd(w)
        
        self.fileDialog = None
        
        c.alphaGroup.toggled.connect(self.updateAlpha)
        c.alphaSlider.valueChanged.connect(self.updateAlpha)
        c.autoAlphaCheck.toggled.connect(self.updateAlpha)

        c.xGridCheck.toggled.connect(self.updateGrid)
        c.yGridCheck.toggled.connect(self.updateGrid)
        c.gridAlphaSlider.valueChanged.connect(self.updateGrid)

        c.fftCheck.toggled.connect(self.updateSpectrumMode)
        c.logXCheck.toggled.connect(self.updateLogMode)
        c.logYCheck.toggled.connect(self.updateLogMode)

        c.downsampleSpin.valueChanged.connect(self.updateDownsampling)
        c.downsampleCheck.toggled.connect(self.updateDownsampling)
        c.autoDownsampleCheck.toggled.connect(self.updateDownsampling)
        c.subsampleRadio.toggled.connect(self.updateDownsampling)
        c.meanRadio.toggled.connect(self.updateDownsampling)
        c.clipToViewCheck.toggled.connect(self.updateDownsampling)

        self.ctrl.avgParamList.itemClicked.connect(self.avgParamListClicked)
        self.ctrl.averageGroup.toggled.connect(self.avgToggled)
        
        self.ctrl.maxTracesCheck.toggled.connect(self.updateDecimation)
        self.ctrl.maxTracesSpin.valueChanged.connect(self.updateDecimation)
        
        self.hideAxis('right')
        self.hideAxis('top')
        self.showAxis('left')
        self.showAxis('bottom')
        
        if labels is None:
            labels = {}
        for label in list(self.axes.keys()):
            if label in kargs:
                labels[label] = kargs[label]
                del kargs[label]
        for k in labels:
            if isinstance(labels[k], basestring):
                labels[k] = (labels[k],)
            self.setLabel(k, *labels[k])
                
        if title is not None:
            self.setTitle(title)
        
        if len(kargs) > 0:
            self.plot(**kargs)
        
        
    def implements(self, interface=None):
        return interface in ['ViewBoxWrapper']

    def getViewBox(self):
        """Return the :class:`ViewBox <pyqtgraph.ViewBox>` contained within."""
        return self.vb
    
    
    
    def setLogMode(self, x=None, y=None):
        """
        Set log scaling for x and/or y axes.
        This informs PlotDataItems to transform logarithmically and switches
        the axes to use log ticking. 
        
        Note that *no other items* in the scene will be affected by
        this; there is (currently) no generic way to redisplay a GraphicsItem
        with log coordinates.
        
        """
        if x is not None:
            self.ctrl.logXCheck.setChecked(x)
        if y is not None:
            self.ctrl.logYCheck.setChecked(y)
        
    def showGrid(self, x=None, y=None, alpha=None):
        """
        Show or hide the grid for either axis.
        
        ==============  =====================================
        **Arguments:**
        x               (bool) Whether to show the X grid
        y               (bool) Whether to show the Y grid
        alpha           (0.0-1.0) Opacity of the grid
        ==============  =====================================
        """
        if x is None and y is None and alpha is None:
            raise Exception("Must specify at least one of x, y, or alpha.")  ## prevent people getting confused if they just call showGrid()
        
        if x is not None:
            self.ctrl.xGridCheck.setChecked(x)
        if y is not None:
            self.ctrl.yGridCheck.setChecked(y)
        if alpha is not None:
            v = np.clip(alpha, 0, 1)*self.ctrl.gridAlphaSlider.maximum()
            self.ctrl.gridAlphaSlider.setValue(v)
        
    #def paint(self, *args):
        #prof = debug.Profiler('PlotItem.paint', disabled=True)
        #QtGui.QGraphicsWidget.paint(self, *args)
        #prof.finish()
        
    ## bad idea. 
    #def __getattr__(self, attr):  ## wrap ms
        #return getattr(self.vb, attr)
        
    def close(self):
        #print "delete", self
        ## Most of this crap is needed to avoid PySide trouble. 
        ## The problem seems to be whenever scene.clear() leads to deletion of widgets (either through proxies or qgraphicswidgets)
        ## the solution is to manually remove all widgets before scene.clear() is called
        if self.ctrlMenu is None: ## already shut down
            return
        self.ctrlMenu.setParent(None)
        self.ctrlMenu = None
        
        #self.ctrlBtn.setParent(None)
        #self.ctrlBtn = None
        #self.autoBtn.setParent(None)
        #self.autoBtn = None
        
        for k in self.axes:
            i = self.axes[k]['item']
            i.close()
            
        self.axes = None
        self.scene().removeItem(self.vb)
        self.vb = None
        
        ## causes invalid index errors:
        #for i in range(self.layout.count()):
            #self.layout.removeAt(i)
            
        #for p in self.proxies:
            #try:
                #p.setWidget(None)
            #except RuntimeError:
                #break
            #self.scene().removeItem(p)
        #self.proxies = []
        
        #self.menuAction.releaseWidget(self.menuAction.defaultWidget())
        #self.menuAction.setParent(None)
        #self.menuAction = None
        
        #if self.manager is not None:
            #self.manager.sigWidgetListChanged.disconnect(self.updatePlotList)
            #self.manager.removeWidget(self.name)
        #else:
            #print "no manager"

    def registerPlot(self, name):   ## for backward compatibility
        self.vb.register(name)
        
    def updateGrid(self, *args):
        alpha = self.ctrl.gridAlphaSlider.value()
        x = alpha if self.ctrl.xGridCheck.isChecked() else False
        y = alpha if self.ctrl.yGridCheck.isChecked() else False
        self.getAxis('top').setGrid(x)
        self.getAxis('bottom').setGrid(x)
        self.getAxis('left').setGrid(y)
        self.getAxis('right').setGrid(y)

    def viewGeometry(self):
        """Return the screen geometry of the viewbox"""
        v = self.scene().views()[0]
        b = self.vb.mapRectToScene(self.vb.boundingRect())
        wr = v.mapFromScene(b).boundingRect()
        pos = v.mapToGlobal(v.pos())
        wr.adjust(pos.x(), pos.y(), pos.x(), pos.y())
        return wr


    def avgToggled(self, b):
        if b:
            self.recomputeAverages()
        for k in self.avgCurves:
            self.avgCurves[k][1].setVisible(b)
        
    def avgParamListClicked(self, item):
        name = str(item.text())
        self.paramList[name] = (item.checkState() == QtCore.Qt.Checked)
        self.recomputeAverages()
        
    def recomputeAverages(self):
        if not self.ctrl.averageGroup.isChecked():
            return
        for k in self.avgCurves:
            self.removeItem(self.avgCurves[k][1])
        self.avgCurves = {}
        for c in self.curves:
            self.addAvgCurve(c)
        self.replot()
        
    def addAvgCurve(self, curve):
        ## Add a single curve into the pool of curves averaged together
        
        ## If there are plot parameters, then we need to determine which to average together.
        remKeys = []
        addKeys = []
        if self.ctrl.avgParamList.count() > 0:
        
            ### First determine the key of the curve to which this new data should be averaged
            for i in range(self.ctrl.avgParamList.count()):
                item = self.ctrl.avgParamList.item(i)
                if item.checkState() == QtCore.Qt.Checked:
                    remKeys.append(str(item.text()))
                else:
                    addKeys.append(str(item.text()))
                    
            if len(remKeys) < 1:  ## In this case, there would be 1 average plot for each data plot; not useful.
                return
                
        p = self.itemMeta.get(curve,{}).copy()
        for k in p:
            if type(k) is tuple:
                p['.'.join(k)] = p[k]
                del p[k]
        for rk in remKeys:
            if rk in p:
                del p[rk]
        for ak in addKeys:
            if ak not in p:
                p[ak] = None
        key = tuple(p.items())
        
        ### Create a new curve if needed
        if key not in self.avgCurves:
            plot = PlotDataItem()
            plot.setPen(fn.mkPen([0, 200, 0]))
            plot.setShadowPen(fn.mkPen([0, 0, 0, 100], width=3))
            plot.setAlpha(1.0, False)
            plot.setZValue(100)
            self.addItem(plot, skipAverage=True)
            self.avgCurves[key] = [0, plot]
        self.avgCurves[key][0] += 1
        (n, plot) = self.avgCurves[key]
        
        ### Average data together
        (x, y) = curve.getData()
        if plot.yData is not None:
            newData = plot.yData * (n-1) / float(n) + y * 1.0 / float(n)
            plot.setData(plot.xData, newData)
        else:
            plot.setData(x, y)
        
    def autoBtnClicked(self):
        if self.autoBtn.mode == 'auto':
            self.enableAutoRange()
            self.autoBtn.hide()
        else:
            self.disableAutoRange()
            
    def viewStateChanged(self):
        self.updateButtons()
            
    def enableAutoScale(self):
        """
        Enable auto-scaling. The plot will continuously scale to fit the boundaries of its data.
        """
        print("Warning: enableAutoScale is deprecated. Use enableAutoRange(axis, enable) instead.")
        self.vb.enableAutoRange(self.vb.XYAxes)

    def addItem(self, item, *args, **kargs):
        """
        Add a graphics item to the view box. 
        If the item has plot data (PlotDataItem, PlotCurveItem, ScatterPlotItem), it may
        be included in analysis performed by the PlotItem.
        """
        self.items.append(item)
        vbargs = {}
        if 'ignoreBounds' in kargs:
            vbargs['ignoreBounds'] = kargs['ignoreBounds']
        self.vb.addItem(item, *args, **vbargs)
        if hasattr(item, 'implements') and item.implements('plotData'):
            self.dataItems.append(item)
            #self.plotChanged()
            
            params = kargs.get('params', {})
            self.itemMeta[item] = params
            #item.setMeta(params)
            self.curves.append(item)
            #self.addItem(c)
            
        if hasattr(item, 'setLogMode'):
            item.setLogMode(self.ctrl.logXCheck.isChecked(), self.ctrl.logYCheck.isChecked())
            
        if isinstance(item, PlotDataItem):
            ## configure curve for this plot
            (alpha, auto) = self.alphaState()
            item.setAlpha(alpha, auto)
            item.setFftMode(self.ctrl.fftCheck.isChecked())
            item.setDownsampling(*self.downsampleMode())
            item.setClipToView(self.clipToViewMode())
            item.setPointMode(self.pointMode())
            
            ## Hide older plots if needed
            self.updateDecimation()
            
            ## Add to average if needed
            self.updateParamList()
            if self.ctrl.averageGroup.isChecked() and 'skipAverage' not in kargs:
                self.addAvgCurve(item)
                
            #c.connect(c, QtCore.SIGNAL('plotChanged'), self.plotChanged)
            #item.sigPlotChanged.connect(self.plotChanged)
            #self.plotChanged()
        name = kargs.get('name', getattr(item, 'opts', {}).get('name', None))
        if name is not None and hasattr(self, 'legend') and self.legend is not None:
            self.legend.addItem(item, name=name)
            

    def addDataItem(self, item, *args):
        print("PlotItem.addDataItem is deprecated. Use addItem instead.")
        self.addItem(item, *args)
        
    def listDataItems(self):
        """Return a list of all data items (PlotDataItem, PlotCurveItem, ScatterPlotItem, etc)
        contained in this PlotItem."""
        return self.dataItems[:]
        
    def addCurve(self, c, params=None):
        print("PlotItem.addCurve is deprecated. Use addItem instead.")
        self.addItem(c, params)

    def addLine(self, x=None, y=None, z=None, **kwds):
        """
        Create an InfiniteLine and add to the plot. 
        
        If *x* is specified,
        the line will be vertical. If *y* is specified, the line will be
        horizontal. All extra keyword arguments are passed to
        :func:`InfiniteLine.__init__() <pyqtgraph.InfiniteLine.__init__>`.
        Returns the item created.
        """
        pos = kwds.get('pos', x if x is not None else y)
        angle = kwds.get('angle', 0 if x is None else 90)
        line = InfiniteLine(pos, angle, **kwds)
        self.addItem(line)
        if z is not None:
            line.setZValue(z)
        return line
        
        

    def removeItem(self, item):
        """
        Remove an item from the internal ViewBox.
        """
        if not item in self.items:
            return
        self.items.remove(item)
        if item in self.dataItems:
            self.dataItems.remove(item)
            
        if item.scene() is not None:
            self.vb.removeItem(item)
        if item in self.curves:
            self.curves.remove(item)
            self.updateDecimation()
            self.updateParamList()
            #item.connect(item, QtCore.SIGNAL('plotChanged'), self.plotChanged)
            #item.sigPlotChanged.connect(self.plotChanged)

    def clear(self):
        """
        Remove all items from the ViewBox.
        """
        for i in self.items[:]:
            self.removeItem(i)
        self.avgCurves = {}
    
    def clearPlots(self):
        for i in self.curves[:]:
            self.removeItem(i)
        self.avgCurves = {}
        
    
    def plot(self, *args, **kargs):
        """
        Add and return a new plot.
        See :func:`PlotDataItem.__init__ <pyqtgraph.PlotDataItem.__init__>` for data arguments
        
        Extra allowed arguments are:
            clear    - clear all plots before displaying new data
            params   - meta-parameters to associate with this data
        """
        
        
        clear = kargs.get('clear', False)
        params = kargs.get('params', None)
          
        if clear:
            self.clear()
            
        item = PlotDataItem(*args, **kargs)
            
        if params is None:
            params = {}
        self.addItem(item, params=params)
        
        return item

    def addLegend(self, size=None, offset=(30, 30)):
        """
        Create a new LegendItem and anchor it over the internal ViewBox.
        Plots will be automatically displayed in the legend if they
        are created with the 'name' argument.
        """
        self.legend = LegendItem(size, offset)
        self.legend.setParentItem(self.vb)
        return self.legend
        
    def scatterPlot(self, *args, **kargs):
        if 'pen' in kargs:
            kargs['symbolPen'] = kargs['pen']
        kargs['pen'] = None
            
        if 'brush' in kargs:
            kargs['symbolBrush'] = kargs['brush']
            del kargs['brush']
            
        if 'size' in kargs:
            kargs['symbolSize'] = kargs['size']
            del kargs['size']

        return self.plot(*args, **kargs)
                
    def replot(self):
        self.update()

    def updateParamList(self):
        self.ctrl.avgParamList.clear()
        ## Check to see that each parameter for each curve is present in the list
        for c in self.curves:
            for p in list(self.itemMeta.get(c, {}).keys()):
                if type(p) is tuple:
                    p = '.'.join(p)
                    
                ## If the parameter is not in the list, add it.
                matches = self.ctrl.avgParamList.findItems(p, QtCore.Qt.MatchExactly)
                if len(matches) == 0:
                    i = QtGui.QListWidgetItem(p)
                    if p in self.paramList and self.paramList[p] is True:
                        i.setCheckState(QtCore.Qt.Checked)
                    else:
                        i.setCheckState(QtCore.Qt.Unchecked)
                    self.ctrl.avgParamList.addItem(i)
                else:
                    i = matches[0]
                    
                self.paramList[p] = (i.checkState() == QtCore.Qt.Checked)


    ## Qt's SVG-writing capabilities are pretty terrible. 
    def writeSvgCurves(self, fileName=None):
        if fileName is None:
            self.fileDialog = FileDialog()
            if PlotItem.lastFileDir is not None:
                self.fileDialog.setDirectory(PlotItem.lastFileDir)
            self.fileDialog.setFileMode(QtGui.QFileDialog.AnyFile)
            self.fileDialog.setAcceptMode(QtGui.QFileDialog.AcceptSave) 
            self.fileDialog.show()
            self.fileDialog.fileSelected.connect(self.writeSvg)
            return
        #if fileName is None:
            #fileName = QtGui.QFileDialog.getSaveFileName()
        if isinstance(fileName, tuple):
            raise Exception("Not implemented yet..")
        fileName = str(fileName)
        PlotItem.lastFileDir = os.path.dirname(fileName)
        
        rect = self.vb.viewRect()
        xRange = rect.left(), rect.right() 
        
        svg = ""
        fh = open(fileName, 'w')

        dx = max(rect.right(),0) - min(rect.left(),0)
        ymn = min(rect.top(), rect.bottom())
        ymx = max(rect.top(), rect.bottom())
        dy = max(ymx,0) - min(ymn,0)
        sx = 1.
        sy = 1.
        while dx*sx < 10:
            sx *= 1000
        while dy*sy < 10:
            sy *= 1000
        sy *= -1

        #fh.write('<svg viewBox="%f %f %f %f">\n' % (rect.left()*sx, rect.top()*sx, rect.width()*sy, rect.height()*sy))
        fh.write('<svg>\n')
        fh.write('<path fill="none" stroke="#000000" stroke-opacity="0.5" stroke-width="1" d="M%f,0 L%f,0"/>\n' % (rect.left()*sx, rect.right()*sx))
        fh.write('<path fill="none" stroke="#000000" stroke-opacity="0.5" stroke-width="1" d="M0,%f L0,%f"/>\n' % (rect.top()*sy, rect.bottom()*sy))


        for item in self.curves:
            if isinstance(item, PlotCurveItem):
                color = fn.colorStr(item.pen.color())
                opacity = item.pen.color().alpha() / 255.
                color = color[:6]
                x, y = item.getData()
                mask = (x > xRange[0]) * (x < xRange[1])
                mask[:-1] += mask[1:]
                m2 = mask.copy()
                mask[1:] += m2[:-1]
                x = x[mask]
                y = y[mask]
                
                x *= sx
                y *= sy
                
                #fh.write('<g fill="none" stroke="#%s" stroke-opacity="1" stroke-width="1">\n' % color)
                fh.write('<path fill="none" stroke="#%s" stroke-opacity="%f" stroke-width="1" d="M%f,%f ' % (color, opacity, x[0], y[0]))
                for i in range(1, len(x)):
                    fh.write('L%f,%f ' % (x[i], y[i]))
                
                fh.write('"/>')
                #fh.write("</g>")
        for item in self.dataItems:
            if isinstance(item, ScatterPlotItem):
                
                pRect = item.boundingRect()
                vRect = pRect.intersected(rect)
                
                for point in item.points():
                    pos = point.pos()
                    if not rect.contains(pos):
                        continue
                    color = fn.colorStr(point.brush.color())
                    opacity = point.brush.color().alpha() / 255.
                    color = color[:6]
                    x = pos.x() * sx
                    y = pos.y() * sy
                    
                    fh.write('<circle cx="%f" cy="%f" r="1" fill="#%s" stroke="none" fill-opacity="%f"/>\n' % (x, y, color, opacity))
                    #fh.write('<path fill="none" stroke="#%s" stroke-opacity="%f" stroke-width="1" d="M%f,%f ' % (color, opacity, x[0], y[0]))
                    #for i in xrange(1, len(x)):
                        #fh.write('L%f,%f ' % (x[i], y[i]))
                    
                    #fh.write('"/>')
            
        ## get list of curves, scatter plots
        
        
        fh.write("</svg>\n")
        
        
    
    def writeSvg(self, fileName=None):
        if fileName is None:
            fileName = QtGui.QFileDialog.getSaveFileName()
        fileName = str(fileName)
        PlotItem.lastFileDir = os.path.dirname(fileName)
        
        self.svg = QtSvg.QSvgGenerator()
        self.svg.setFileName(fileName)
        res = 120.
        view = self.scene().views()[0]
        bounds = view.viewport().rect()
        bounds = QtCore.QRectF(0, 0, bounds.width(), bounds.height())
        
        self.svg.setResolution(res)
        self.svg.setViewBox(bounds)
        
        self.svg.setSize(QtCore.QSize(bounds.width(), bounds.height()))
        
        painter = QtGui.QPainter(self.svg)
        view.render(painter, bounds)
        
        painter.end()
        
        ## Workaround to set pen widths correctly
        import re
        data = open(fileName).readlines()
        for i in range(len(data)):
            line = data[i]
            m = re.match(r'(<g .*)stroke-width="1"(.*transform="matrix\(([^\)]+)\)".*)', line)
            if m is not None:
                #print "Matched group:", line
                g = m.groups()
                matrix = list(map(float, g[2].split(',')))
                #print "matrix:", matrix
                scale = max(abs(matrix[0]), abs(matrix[3]))
                if scale == 0 or scale == 1.0:
                    continue
                data[i] = g[0] + ' stroke-width="%0.2g" ' % (1.0/scale) + g[1] + '\n'
                #print "old line:", line
                #print "new line:", data[i]
        open(fileName, 'w').write(''.join(data))
        
        
    def writeImage(self, fileName=None):
        if fileName is None:
            self.fileDialog = FileDialog()
            if PlotItem.lastFileDir is not None:
                self.fileDialog.setDirectory(PlotItem.lastFileDir)
            self.fileDialog.setFileMode(QtGui.QFileDialog.AnyFile)
            self.fileDialog.setAcceptMode(QtGui.QFileDialog.AcceptSave) 
            self.fileDialog.show()
            self.fileDialog.fileSelected.connect(self.writeImage)
            return
        #if fileName is None:
            #fileName = QtGui.QFileDialog.getSaveFileName()
        if isinstance(fileName, tuple):
            raise Exception("Not implemented yet..")
        fileName = str(fileName)
        PlotItem.lastFileDir = os.path.dirname(fileName)
        self.png = QtGui.QImage(int(self.size().width()), int(self.size().height()), QtGui.QImage.Format_ARGB32)
        painter = QtGui.QPainter(self.png)
        painter.setRenderHints(painter.Antialiasing | painter.TextAntialiasing)
        self.scene().render(painter, QtCore.QRectF(), self.mapRectToScene(self.boundingRect()))
        painter.end()
        self.png.save(fileName)
        
    def writeCsv(self, fileName=None):
        if fileName is None:
            self.fileDialog = FileDialog()
            if PlotItem.lastFileDir is not None:
                self.fileDialog.setDirectory(PlotItem.lastFileDir)
            self.fileDialog.setFileMode(QtGui.QFileDialog.AnyFile)
            self.fileDialog.setAcceptMode(QtGui.QFileDialog.AcceptSave) 
            self.fileDialog.show()
            self.fileDialog.fileSelected.connect(self.writeCsv)
            return
        #if fileName is None:
            #fileName = QtGui.QFileDialog.getSaveFileName()
        fileName = str(fileName)
        PlotItem.lastFileDir = os.path.dirname(fileName)
        
        fd = open(fileName, 'w')
        data = [c.getData() for c in self.curves]
        i = 0
        while True:
            done = True
            for d in data:
                if i < len(d[0]):
                    fd.write('%g,%g,'%(d[0][i], d[1][i]))
                    done = False
                else:
                    fd.write(' , ,')
            fd.write('\n')
            if done:
                break
            i += 1
        fd.close()


    def saveState(self):
        state = self.stateGroup.state()
        state['paramList'] = self.paramList.copy()
        state['view'] = self.vb.getState()
        return state
        
    def restoreState(self, state):
        if 'paramList' in state:
            self.paramList = state['paramList'].copy()
            
        self.stateGroup.setState(state)
        self.updateSpectrumMode()
        self.updateDownsampling()
        self.updateAlpha()
        self.updateDecimation()
        
        if 'powerSpectrumGroup' in state:
            state['fftCheck'] = state['powerSpectrumGroup']
        if 'gridGroup' in state:
            state['xGridCheck'] = state['gridGroup']
            state['yGridCheck'] = state['gridGroup']
            
        self.stateGroup.setState(state)
        self.updateParamList()
        
        if 'view' not in state:
            r = [[float(state['xMinText']), float(state['xMaxText'])], [float(state['yMinText']), float(state['yMaxText'])]]
            state['view'] = {
                'autoRange': [state['xAutoRadio'], state['yAutoRadio']],
                'linkedViews': [state['xLinkCombo'], state['yLinkCombo']],
                'targetRange': r,
                'viewRange': r,
            }
        self.vb.setState(state['view'])
        

    def widgetGroupInterface(self):
        return (None, PlotItem.saveState, PlotItem.restoreState)
      
    def updateSpectrumMode(self, b=None):
        if b is None:
            b = self.ctrl.fftCheck.isChecked()
        for c in self.curves:
            c.setFftMode(b)
        self.enableAutoRange()
        self.recomputeAverages()
            
    def updateLogMode(self):
        x = self.ctrl.logXCheck.isChecked()
        y = self.ctrl.logYCheck.isChecked()
        for i in self.items:
            if hasattr(i, 'setLogMode'):
                i.setLogMode(x,y)
        self.getAxis('bottom').setLogMode(x)
        self.getAxis('top').setLogMode(x)
        self.getAxis('left').setLogMode(y)
        self.getAxis('right').setLogMode(y)
        self.enableAutoRange()
        self.recomputeAverages()
        
    def setDownsampling(self, ds=None, auto=None, mode=None):
        """Change the default downsampling mode for all PlotDataItems managed by this plot.
        
        ===========  =================================================================
        Arguments
        ds           (int) Reduce visible plot samples by this factor, or
                     (bool) To enable/disable downsampling without changing the value.
        auto         (bool) If True, automatically pick *ds* based on visible range
        mode         'subsample': Downsample by taking the first of N samples. 
                         This method is fastest and least accurate.
                     'mean': Downsample by taking the mean of N samples.
                     'peak': Downsample by drawing a saw wave that follows the min 
                         and max of the original data. This method produces the best 
                         visual representation of the data but is slower.
        ===========  =================================================================
        """
        if ds is not None:
            if ds is False:
                self.ctrl.downsampleCheck.setChecked(False)
            elif ds is True:
                self.ctrl.downsampleCheck.setChecked(True)
            else:
                self.ctrl.downsampleCheck.setChecked(True)
                self.ctrl.downsampleSpin.setValue(ds)
                
        if auto is not None:
            if auto and ds is not False:
                self.ctrl.downsampleCheck.setChecked(True)
            self.ctrl.autoDownsampleCheck.setChecked(auto)
            
        if mode is not None:
            if mode == 'subsample':
                self.ctrl.subsampleRadio.setChecked(True)
            elif mode == 'mean':
                self.ctrl.meanRadio.setChecked(True)
            elif mode == 'peak':
                self.ctrl.peakRadio.setChecked(True)
            else:
                raise ValueError("mode argument must be 'subsample', 'mean', or 'peak'.")
            
    def updateDownsampling(self):
        ds, auto, method = self.downsampleMode()
        clip = self.ctrl.clipToViewCheck.isChecked()
        for c in self.curves:
            c.setDownsampling(ds, auto, method)
            c.setClipToView(clip)
        self.recomputeAverages()
        
    def downsampleMode(self):
        if self.ctrl.downsampleCheck.isChecked():
            ds = self.ctrl.downsampleSpin.value()
        else:
            ds = 1
            
        auto = self.ctrl.downsampleCheck.isChecked() and self.ctrl.autoDownsampleCheck.isChecked()
            
        if self.ctrl.subsampleRadio.isChecked():
            method = 'subsample' 
        elif self.ctrl.meanRadio.isChecked():
            method = 'mean'
        elif self.ctrl.peakRadio.isChecked():
            method = 'peak'
        
        return ds, auto, method
        
    def setClipToView(self, clip):
        """Set the default clip-to-view mode for all PlotDataItems managed by this plot.
        If *clip* is True, then PlotDataItems will attempt to draw only points within the visible
        range of the ViewBox."""
        self.ctrl.clipToViewCheck.setChecked(clip)
        
    def clipToViewMode(self):
        return self.ctrl.clipToViewCheck.isChecked()
        
        
        
    def updateDecimation(self):
        if self.ctrl.maxTracesCheck.isChecked():
            numCurves = self.ctrl.maxTracesSpin.value()
        else:
            numCurves = -1
            
        curves = self.curves[:]
        split = len(curves) - numCurves
        for i in range(len(curves)):
            if numCurves == -1 or i >= split:
                curves[i].show()
            else:
                if self.ctrl.forgetTracesCheck.isChecked():
                    curves[i].clear()
                    self.removeItem(curves[i])
                else:
                    curves[i].hide()
        
      
    def updateAlpha(self, *args):
        (alpha, auto) = self.alphaState()
        for c in self.curves:
            c.setAlpha(alpha**2, auto)
     
    def alphaState(self):
        enabled = self.ctrl.alphaGroup.isChecked()
        auto = self.ctrl.autoAlphaCheck.isChecked()
        alpha = float(self.ctrl.alphaSlider.value()) / self.ctrl.alphaSlider.maximum()
        if auto:
            alpha = 1.0  ## should be 1/number of overlapping plots
        if not enabled:
            auto = False
            alpha = 1.0
        return (alpha, auto)

    def pointMode(self):
        if self.ctrl.pointsGroup.isChecked():
            if self.ctrl.autoPointsCheck.isChecked():
                mode = None
            else:
                mode = True
        else:
            mode = False
        return mode
        

    def resizeEvent(self, ev):
        if self.autoBtn is None:  ## already closed down
            return
        btnRect = self.mapRectFromItem(self.autoBtn, self.autoBtn.boundingRect())
        y = self.size().height() - btnRect.height()
        self.autoBtn.setPos(0, y)
    
    
    def getMenu(self):
        return self.ctrlMenu
    
    def getContextMenus(self, event):
        ## called when another item is displaying its context menu; we get to add extras to the end of the menu.
        if self.menuEnabled():
            return self.ctrlMenu
        else:
            return None
    
    def setMenuEnabled(self, enableMenu=True, enableViewBoxMenu='same'):
        """
        Enable or disable the context menu for this PlotItem.
        By default, the ViewBox's context menu will also be affected.
        (use enableViewBoxMenu=None to leave the ViewBox unchanged)
        """
        self._menuEnabled = enableMenu
        if enableViewBoxMenu is None:
            return
        if enableViewBoxMenu is 'same':
            enableViewBoxMenu = enableMenu 
        self.vb.setMenuEnabled(enableViewBoxMenu)
    
    def menuEnabled(self):
        return self._menuEnabled
    
    def hoverEvent(self, ev):
        if ev.enter:
            self.mouseHovering = True
        if ev.exit:
            self.mouseHovering = False
            
        self.updateButtons()
    

    def getLabel(self, key):
        pass
        
    def _checkScaleKey(self, key):
        if key not in self.axes:
            raise Exception("Scale '%s' not found. Scales are: %s" % (key, str(list(self.axes.keys()))))
        
    def getScale(self, key):
        return self.getAxis(key)
        
    def getAxis(self, name):
        """Return the specified AxisItem. 
        *name* should be 'left', 'bottom', 'top', or 'right'."""
        self._checkScaleKey(name)
        return self.axes[name]['item']
        
    def setLabel(self, axis, text=None, units=None, unitPrefix=None, **args):
        """
        Set the label for an axis. Basic HTML formatting is allowed.
        
        ============= =================================================================
        **Arguments**
        axis          must be one of 'left', 'bottom', 'right', or 'top'
        text          text to display along the axis. HTML allowed.
        units         units to display after the title. If units are given, 
                      then an SI prefix will be automatically appended
                      and the axis values will be scaled accordingly.
                      (ie, use 'V' instead of 'mV'; 'm' will be added automatically)
        ============= =================================================================
        """
        self.getAxis(axis).setLabel(text=text, units=units, **args)
        self.showAxis(axis)
        
    def setLabels(self, **kwds):
        """
        Convenience function allowing multiple labels and/or title to be set in one call.
        Keyword arguments can be 'title', 'left', 'bottom', 'right', or 'top'.
        Values may be strings or a tuple of arguments to pass to setLabel.
        """
        for k,v in kwds.items():
            if k == 'title':
                self.setTitle(v)
            else:
                if isinstance(v, basestring):
                    v = (v,)
                self.setLabel(k, *v)
        
        
    def showLabel(self, axis, show=True):
        """
        Show or hide one of the plot's axis labels (the axis itself will be unaffected).
        axis must be one of 'left', 'bottom', 'right', or 'top'
        """
        self.getScale(axis).showLabel(show)

    def setTitle(self, title=None, **args):
        """
        Set the title of the plot. Basic HTML formatting is allowed.
        If title is None, then the title will be hidden.
        """
        if title is None:
            self.titleLabel.setVisible(False)
            self.layout.setRowFixedHeight(0, 0)
            self.titleLabel.setMaximumHeight(0)
        else:
            self.titleLabel.setMaximumHeight(30)
            self.layout.setRowFixedHeight(0, 30)
            self.titleLabel.setVisible(True)
            self.titleLabel.setText(title, **args)

    def showAxis(self, axis, show=True):
        """
        Show or hide one of the plot's axes.
        axis must be one of 'left', 'bottom', 'right', or 'top'
        """
        s = self.getScale(axis)
        p = self.axes[axis]['pos']
        if show:
            s.show()
        else:
            s.hide()
            
    def hideAxis(self, axis):
        """Hide one of the PlotItem's axes. ('left', 'bottom', 'right', or 'top')"""
        self.showAxis(axis, False)
            
    def showScale(self, *args, **kargs):
        print("Deprecated. use showAxis() instead")
        return self.showAxis(*args, **kargs)
            
    def hideButtons(self):
        """Causes auto-scale button ('A' in lower-left corner) to be hidden for this PlotItem"""
        #self.ctrlBtn.hide()
        self.buttonsHidden = True
        self.updateButtons()
        
    def showButtons(self):
        """Causes auto-scale button ('A' in lower-left corner) to be visible for this PlotItem"""
        #self.ctrlBtn.hide()
        self.buttonsHidden = False
        self.updateButtons()
        
    def updateButtons(self):
        if self._exportOpts is False and self.mouseHovering and not self.buttonsHidden and not all(self.vb.autoRangeEnabled()):
            self.autoBtn.show()
        else:
            self.autoBtn.hide()
            
    def _plotArray(self, arr, x=None, **kargs):
        if arr.ndim != 1:
            raise Exception("Array must be 1D to plot (shape is %s)" % arr.shape)
        if x is None:
            x = np.arange(arr.shape[0])
        if x.ndim != 1:
            raise Exception("X array must be 1D to plot (shape is %s)" % x.shape)
        c = PlotCurveItem(arr, x=x, **kargs)
        return c
            
        
        
    def _plotMetaArray(self, arr, x=None, autoLabel=True, **kargs):
        inf = arr.infoCopy()
        if arr.ndim != 1:
            raise Exception('can only automatically plot 1 dimensional arrays.')
        ## create curve
        try:
            xv = arr.xvals(0)
        except:
            if x is None:
                xv = np.arange(arr.shape[0])
            else:
                xv = x
        c = PlotCurveItem(**kargs)
        c.setData(x=xv, y=arr.view(np.ndarray))
        
        if autoLabel:
            name = arr._info[0].get('name', None)
            units = arr._info[0].get('units', None)
            self.setLabel('bottom', text=name, units=units)
            
            name = arr._info[1].get('name', None)
            units = arr._info[1].get('units', None)
            self.setLabel('left', text=name, units=units)
            
        return c

      
    def setExportMode(self, export, opts=None):
        GraphicsWidget.setExportMode(self, export, opts)
        self.updateButtons()
        #if export:
            #self.autoBtn.hide()
        #else:
            #self.autoBtn.show()
    
