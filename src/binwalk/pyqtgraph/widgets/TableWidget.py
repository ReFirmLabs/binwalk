# -*- coding: utf-8 -*-
from pyqtgraph.Qt import QtGui, QtCore
from pyqtgraph.python2_3 import asUnicode

import numpy as np
try:
    import metaarray
    HAVE_METAARRAY = True
except ImportError:
    HAVE_METAARRAY = False

__all__ = ['TableWidget']
class TableWidget(QtGui.QTableWidget):
    """Extends QTableWidget with some useful functions for automatic data handling
    and copy / export context menu. Can automatically format and display a variety
    of data types (see :func:`setData() <pyqtgraph.TableWidget.setData>` for more
    information.
    """
    
    def __init__(self, *args, **kwds):
        QtGui.QTableWidget.__init__(self, *args)
        self.setVerticalScrollMode(self.ScrollPerPixel)
        self.setSelectionMode(QtGui.QAbstractItemView.ContiguousSelection)
        self.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        self.setSortingEnabled(True)
        self.clear()
        editable = kwds.get('editable', False)
        self.setEditable(editable)
        self.contextMenu = QtGui.QMenu()
        self.contextMenu.addAction('Copy Selection').triggered.connect(self.copySel)
        self.contextMenu.addAction('Copy All').triggered.connect(self.copyAll)
        self.contextMenu.addAction('Save Selection').triggered.connect(self.saveSel)
        self.contextMenu.addAction('Save All').triggered.connect(self.saveAll)
        
    def clear(self):
        """Clear all contents from the table."""
        QtGui.QTableWidget.clear(self)
        self.verticalHeadersSet = False
        self.horizontalHeadersSet = False
        self.items = []
        self.setRowCount(0)
        self.setColumnCount(0)
        
    def setData(self, data):
        """Set the data displayed in the table.
        Allowed formats are:
        
        * numpy arrays
        * numpy record arrays 
        * metaarrays
        * list-of-lists  [[1,2,3], [4,5,6]]
        * dict-of-lists  {'x': [1,2,3], 'y': [4,5,6]}
        * list-of-dicts  [{'x': 1, 'y': 4}, {'x': 2, 'y': 5}, ...]
        """
        self.clear()
        self.appendData(data)
        self.resizeColumnsToContents()
        
    def appendData(self, data):
        """Types allowed:
        1 or 2D numpy array or metaArray
        1D numpy record array
        list-of-lists, list-of-dicts or dict-of-lists
        """
        fn0, header0 = self.iteratorFn(data)
        if fn0 is None:
            self.clear()
            return
        it0 = fn0(data)
        try:
            first = next(it0)
        except StopIteration:
            return
        fn1, header1 = self.iteratorFn(first)
        if fn1 is None:
            self.clear()
            return
        
        firstVals = [x for x in fn1(first)]
        self.setColumnCount(len(firstVals))
        
        if not self.verticalHeadersSet and header0 is not None:
            self.setRowCount(len(header0))
            self.setVerticalHeaderLabels(header0)
            self.verticalHeadersSet = True
        if not self.horizontalHeadersSet and header1 is not None:
            self.setHorizontalHeaderLabels(header1)
            self.horizontalHeadersSet = True
        
        self.setRow(0, firstVals)
        i = 1
        for row in it0:
            self.setRow(i, [x for x in fn1(row)])
            i += 1
    
    def setEditable(self, editable=True):
        self.editable = editable
        for item in self.items:
            item.setEditable(editable)
            
    def iteratorFn(self, data):
        ## Return 1) a function that will provide an iterator for data and 2) a list of header strings
        if isinstance(data, list) or isinstance(data, tuple):
            return lambda d: d.__iter__(), None
        elif isinstance(data, dict):
            return lambda d: iter(d.values()), list(map(str, data.keys()))
        elif HAVE_METAARRAY and (hasattr(data, 'implements') and data.implements('MetaArray')):
            if data.axisHasColumns(0):
                header = [str(data.columnName(0, i)) for i in range(data.shape[0])]
            elif data.axisHasValues(0):
                header = list(map(str, data.xvals(0)))
            else:
                header = None
            return self.iterFirstAxis, header
        elif isinstance(data, np.ndarray):
            return self.iterFirstAxis, None
        elif isinstance(data, np.void):
            return self.iterate, list(map(str, data.dtype.names))
        elif data is None:
            return (None,None)
        else:
            msg = "Don't know how to iterate over data type: {!s}".format(type(data))
            raise TypeError(msg)
        
    def iterFirstAxis(self, data):
        for i in range(data.shape[0]):
            yield data[i]
            
    def iterate(self, data):
        # for numpy.void, which can be iterated but mysteriously 
        # has no __iter__ (??)
        for x in data:
            yield x
        
    def appendRow(self, data):
        self.appendData([data])
        
    def addRow(self, vals):
        row = self.rowCount()
        self.setRowCount(row + 1)
        self.setRow(row, vals)
        
    def setRow(self, row, vals):
        if row > self.rowCount() - 1:
            self.setRowCount(row + 1)
        for col in range(len(vals)):
            val = vals[col]
            item = TableWidgetItem(val)
            item.setEditable(self.editable)
            self.items.append(item)
            self.setItem(row, col, item)

    def sizeHint(self):
        # based on http://stackoverflow.com/a/7195443/54056
        width = sum(self.columnWidth(i) for i in range(self.columnCount()))
        width += self.verticalHeader().sizeHint().width()
        width += self.verticalScrollBar().sizeHint().width()
        width += self.frameWidth() * 2
        height = sum(self.rowHeight(i) for i in range(self.rowCount()))
        height += self.verticalHeader().sizeHint().height()
        height += self.horizontalScrollBar().sizeHint().height()
        return QtCore.QSize(width, height)
         
    def serialize(self, useSelection=False):
        """Convert entire table (or just selected area) into tab-separated text values"""
        if useSelection:
            selection = self.selectedRanges()[0]
            rows = list(range(selection.topRow(),
                              selection.bottomRow() + 1))
            columns = list(range(selection.leftColumn(),
                                 selection.rightColumn() + 1))        
        else:
            rows = list(range(self.rowCount()))
            columns = list(range(self.columnCount()))


        data = []
        if self.horizontalHeadersSet:
            row = []
            if self.verticalHeadersSet:
                row.append(asUnicode(''))
            
            for c in columns:
                row.append(asUnicode(self.horizontalHeaderItem(c).text()))
            data.append(row)
        
        for r in rows:
            row = []
            if self.verticalHeadersSet:
                row.append(asUnicode(self.verticalHeaderItem(r).text()))
            for c in columns:
                item = self.item(r, c)
                if item is not None:
                    row.append(asUnicode(item.value))
                else:
                    row.append(asUnicode(''))
            data.append(row)
            
        s = ''
        for row in data:
            s += ('\t'.join(row) + '\n')
        return s

    def copySel(self):
        """Copy selected data to clipboard."""
        QtGui.QApplication.clipboard().setText(self.serialize(useSelection=True))

    def copyAll(self):
        """Copy all data to clipboard."""
        QtGui.QApplication.clipboard().setText(self.serialize(useSelection=False))

    def saveSel(self):
        """Save selected data to file."""
        self.save(self.serialize(useSelection=True))

    def saveAll(self):
        """Save all data to file."""
        self.save(self.serialize(useSelection=False))

    def save(self, data):
        fileName = QtGui.QFileDialog.getSaveFileName(self, "Save As..", "", "Tab-separated values (*.tsv)")
        if fileName == '':
            return
        open(fileName, 'w').write(data)
        

    def contextMenuEvent(self, ev):
        self.contextMenu.popup(ev.globalPos())
        
    def keyPressEvent(self, ev):
        if ev.text() == 'c' and ev.modifiers() == QtCore.Qt.ControlModifier:
            ev.accept()
            self.copy()
        else:
            ev.ignore()

class TableWidgetItem(QtGui.QTableWidgetItem):
    def __init__(self, val):
        if isinstance(val, float) or isinstance(val, np.floating):
            s = "%0.3g" % val
        else:
            s = str(val)
        QtGui.QTableWidgetItem.__init__(self, s)
        self.value = val
        flags = QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled
        self.setFlags(flags)
        
    def setEditable(self, editable):
        if editable:
            self.setFlags(self.flags() | QtCore.Qt.ItemIsEditable)
        else:
            self.setFlags(self.flags() & ~QtCore.Qt.ItemIsEditable)

    def __lt__(self, other):
        if hasattr(other, 'value'):
            return self.value < other.value
        else:
            return self.text() < other.text()


if __name__ == '__main__':
    app = QtGui.QApplication([])
    win = QtGui.QMainWindow()
    t = TableWidget()
    win.setCentralWidget(t)
    win.resize(800,600)
    win.show()
    
    ll = [[1,2,3,4,5]] * 20
    ld = [{'x': 1, 'y': 2, 'z': 3}] * 20
    dl = {'x': list(range(20)), 'y': list(range(20)), 'z': list(range(20))}
    
    a = np.ones((20, 5))
    ra = np.ones((20,), dtype=[('x', int), ('y', int), ('z', int)])
    
    t.setData(ll)
    
    if HAVE_METAARRAY:
        ma = metaarray.MetaArray(np.ones((20, 3)), info=[
            {'values': np.linspace(1, 5, 20)}, 
            {'cols': [
                {'name': 'x'},
                {'name': 'y'},
                {'name': 'z'},
            ]}
        ])
        t.setData(ma)
    
