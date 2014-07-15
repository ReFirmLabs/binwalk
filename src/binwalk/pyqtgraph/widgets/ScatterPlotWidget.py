from pyqtgraph.Qt import QtGui, QtCore
from .PlotWidget import PlotWidget
from .DataFilterWidget import DataFilterParameter
from .ColorMapWidget import ColorMapParameter
import pyqtgraph.parametertree as ptree
import pyqtgraph.functions as fn
import numpy as np
from pyqtgraph.pgcollections import OrderedDict
import pyqtgraph as pg

__all__ = ['ScatterPlotWidget']

class ScatterPlotWidget(QtGui.QSplitter):
    """
    Given a record array, display a scatter plot of a specific set of data.
    This widget includes controls for selecting the columns to plot,
    filtering data, and determining symbol color and shape. This widget allows
    the user to explore relationships between columns in a record array.
    
    The widget consists of four components:
    
    1) A list of column names from which the user may select 1 or 2 columns
       to plot. If one column is selected, the data for that column will be
       plotted in a histogram-like manner by using :func:`pseudoScatter()
       <pyqtgraph.pseudoScatter>`. If two columns are selected, then the
       scatter plot will be generated with x determined by the first column
       that was selected and y by the second.
    2) A DataFilter that allows the user to select a subset of the data by 
       specifying multiple selection criteria.
    3) A ColorMap that allows the user to determine how points are colored by
       specifying multiple criteria.
    4) A PlotWidget for displaying the data.
    """
    def __init__(self, parent=None):
        QtGui.QSplitter.__init__(self, QtCore.Qt.Horizontal)
        self.ctrlPanel = QtGui.QSplitter(QtCore.Qt.Vertical)
        self.addWidget(self.ctrlPanel)
        self.fieldList = QtGui.QListWidget()
        self.fieldList.setSelectionMode(self.fieldList.ExtendedSelection)
        self.ptree = ptree.ParameterTree(showHeader=False)
        self.filter = DataFilterParameter()
        self.colorMap = ColorMapParameter()
        self.params = ptree.Parameter.create(name='params', type='group', children=[self.filter, self.colorMap])
        self.ptree.setParameters(self.params, showTop=False)
        
        self.plot = PlotWidget()
        self.ctrlPanel.addWidget(self.fieldList)
        self.ctrlPanel.addWidget(self.ptree)
        self.addWidget(self.plot)
        
        bg = pg.mkColor(pg.getConfigOption('background'))
        bg.setAlpha(150)
        self.filterText = pg.TextItem(border=pg.getConfigOption('foreground'), color=bg)
        self.filterText.setPos(60,20)
        self.filterText.setParentItem(self.plot.plotItem)
        
        self.data = None
        self.mouseOverField = None
        self.scatterPlot = None
        self.style = dict(pen=None, symbol='o')
        
        self.fieldList.itemSelectionChanged.connect(self.fieldSelectionChanged)
        self.filter.sigFilterChanged.connect(self.filterChanged)
        self.colorMap.sigColorMapChanged.connect(self.updatePlot)
    
    def setFields(self, fields, mouseOverField=None):
        """
        Set the list of field names/units to be processed.
        
        The format of *fields* is the same as used by 
        :func:`ColorMapWidget.setFields <pyqtgraph.widgets.ColorMapWidget.ColorMapParameter.setFields>`
        """
        self.fields = OrderedDict(fields)
        self.mouseOverField = mouseOverField
        self.fieldList.clear()
        for f,opts in fields:
            item = QtGui.QListWidgetItem(f)
            item.opts = opts
            item = self.fieldList.addItem(item)
        self.filter.setFields(fields)
        self.colorMap.setFields(fields)
        
    def setData(self, data):
        """
        Set the data to be processed and displayed. 
        Argument must be a numpy record array.
        """
        self.data = data
        self.filtered = None
        self.updatePlot()
        
    def fieldSelectionChanged(self):
        sel = self.fieldList.selectedItems()
        if len(sel) > 2:
            self.fieldList.blockSignals(True)
            try:
                for item in sel[1:-1]:
                    item.setSelected(False)
            finally:
                self.fieldList.blockSignals(False)
                
        self.updatePlot()
        
    def filterChanged(self, f):
        self.filtered = None
        self.updatePlot()
        desc = self.filter.describe()
        if len(desc) == 0:
            self.filterText.setVisible(False)
        else:
            self.filterText.setText('\n'.join(desc))
            self.filterText.setVisible(True)
            
        
    def updatePlot(self):
        self.plot.clear()
        if self.data is None:
            return
        
        if self.filtered is None:
            self.filtered = self.filter.filterData(self.data)
        data = self.filtered
        if len(data) == 0:
            return
        
        colors = np.array([fn.mkBrush(*x) for x in self.colorMap.map(data)])
        
        style = self.style.copy()
        
        ## Look up selected columns and units
        sel = list([str(item.text()) for item in self.fieldList.selectedItems()])
        units = list([item.opts.get('units', '') for item in self.fieldList.selectedItems()])
        if len(sel) == 0:
            self.plot.setTitle('')
            return
        

        if len(sel) == 1:
            self.plot.setLabels(left=('N', ''), bottom=(sel[0], units[0]), title='')
            if len(data) == 0:
                return
            #x = data[sel[0]]
            #y = None
            xy = [data[sel[0]], None]
        elif len(sel) == 2:
            self.plot.setLabels(left=(sel[1],units[1]), bottom=(sel[0],units[0]))
            if len(data) == 0:
                return
            
            xy = [data[sel[0]], data[sel[1]]]
            #xydata = []
            #for ax in [0,1]:
                #d = data[sel[ax]]
                ### scatter catecorical values just a bit so they show up better in the scatter plot.
                ##if sel[ax] in ['MorphologyBSMean', 'MorphologyTDMean', 'FIType']:
                    ##d += np.random.normal(size=len(cells), scale=0.1)
                    
                #xydata.append(d)
            #x,y = xydata

        ## convert enum-type fields to float, set axis labels
        enum = [False, False]
        for i in [0,1]:
            axis = self.plot.getAxis(['bottom', 'left'][i])
            if xy[i] is not None and (self.fields[sel[i]].get('mode', None) == 'enum' or xy[i].dtype.kind in ('S', 'O')):
                vals = self.fields[sel[i]].get('values', list(set(xy[i])))
                xy[i] = np.array([vals.index(x) if x in vals else len(vals) for x in xy[i]], dtype=float)
                axis.setTicks([list(enumerate(vals))])
                enum[i] = True
            else:
                axis.setTicks(None)  # reset to automatic ticking
        
        ## mask out any nan values
        mask = np.ones(len(xy[0]), dtype=bool)
        if xy[0].dtype.kind == 'f':
            mask &= ~np.isnan(xy[0])
        if xy[1] is not None and xy[1].dtype.kind == 'f':
            mask &= ~np.isnan(xy[1])
        
        xy[0] = xy[0][mask]
        style['symbolBrush'] = colors[mask]

        ## Scatter y-values for a histogram-like appearance
        if xy[1] is None:
            ## column scatter plot
            xy[1] = fn.pseudoScatter(xy[0])
        else:
            ## beeswarm plots
            xy[1] = xy[1][mask]
            for ax in [0,1]:
                if not enum[ax]:
                    continue
                imax = int(xy[ax].max()) if len(xy[ax]) > 0 else 0
                for i in range(imax+1):
                    keymask = xy[ax] == i
                    scatter = pg.pseudoScatter(xy[1-ax][keymask], bidir=True)
                    if len(scatter) == 0:
                        continue
                    smax = np.abs(scatter).max()
                    if smax != 0:
                        scatter *= 0.2 / smax
                    xy[ax][keymask] += scatter
        
        if self.scatterPlot is not None:
            try:
                self.scatterPlot.sigPointsClicked.disconnect(self.plotClicked)
            except:
                pass
        self.scatterPlot = self.plot.plot(xy[0], xy[1], data=data[mask], **style)
        self.scatterPlot.sigPointsClicked.connect(self.plotClicked)
        
        
    def plotClicked(self, plot, points):
        pass


