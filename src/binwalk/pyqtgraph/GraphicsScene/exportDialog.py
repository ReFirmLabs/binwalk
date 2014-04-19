from pyqtgraph.Qt import QtCore, QtGui, USE_PYSIDE
import pyqtgraph as pg
import pyqtgraph.exporters as exporters

if USE_PYSIDE:
    from . import exportDialogTemplate_pyside as exportDialogTemplate
else:
    from . import exportDialogTemplate_pyqt as exportDialogTemplate


class ExportDialog(QtGui.QWidget):
    def __init__(self, scene):
        QtGui.QWidget.__init__(self)
        self.setVisible(False)
        self.setWindowTitle("Export")
        self.shown = False
        self.currentExporter = None
        self.scene = scene
            
        self.selectBox = QtGui.QGraphicsRectItem()
        self.selectBox.setPen(pg.mkPen('y', width=3, style=QtCore.Qt.DashLine))
        self.selectBox.hide()
        self.scene.addItem(self.selectBox)
        
        self.ui = exportDialogTemplate.Ui_Form()
        self.ui.setupUi(self)
        
        self.ui.closeBtn.clicked.connect(self.close)
        self.ui.exportBtn.clicked.connect(self.exportClicked)
        self.ui.copyBtn.clicked.connect(self.copyClicked)
        self.ui.itemTree.currentItemChanged.connect(self.exportItemChanged)
        self.ui.formatList.currentItemChanged.connect(self.exportFormatChanged)
        

    def show(self, item=None):
        if item is not None:
            ## Select next exportable parent of the item originally clicked on
            while not isinstance(item, pg.ViewBox) and not isinstance(item, pg.PlotItem) and item is not None:
                item = item.parentItem()
            ## if this is a ViewBox inside a PlotItem, select the parent instead.
            if isinstance(item, pg.ViewBox) and isinstance(item.parentItem(), pg.PlotItem):
                item = item.parentItem()
            self.updateItemList(select=item)
        self.setVisible(True)
        self.activateWindow()
        self.raise_()
        self.selectBox.setVisible(True)
        
        if not self.shown:
            self.shown = True
            vcenter = self.scene.getViewWidget().geometry().center()
            self.setGeometry(vcenter.x()-self.width()/2, vcenter.y()-self.height()/2, self.width(), self.height())
        
    def updateItemList(self, select=None):
        self.ui.itemTree.clear()
        si = QtGui.QTreeWidgetItem(["Entire Scene"])
        si.gitem = self.scene
        self.ui.itemTree.addTopLevelItem(si)
        self.ui.itemTree.setCurrentItem(si)
        si.setExpanded(True)
        for child in self.scene.items():
            if child.parentItem() is None:
                self.updateItemTree(child, si, select=select)
                
    def updateItemTree(self, item, treeItem, select=None):
        si = None
        if isinstance(item, pg.ViewBox):
            si = QtGui.QTreeWidgetItem(['ViewBox'])
        elif isinstance(item, pg.PlotItem):
            si = QtGui.QTreeWidgetItem(['Plot'])
            
        if si is not None:
            si.gitem = item
            treeItem.addChild(si)
            treeItem = si
            if si.gitem is select:
                self.ui.itemTree.setCurrentItem(si)
            
        for ch in item.childItems():
            self.updateItemTree(ch, treeItem, select=select)
        
            
    def exportItemChanged(self, item, prev):
        if item is None:
            return
        if item.gitem is self.scene:
            newBounds = self.scene.views()[0].viewRect()
        else:
            newBounds = item.gitem.sceneBoundingRect()
        self.selectBox.setRect(newBounds)
        self.selectBox.show()
        self.updateFormatList()
        
    def updateFormatList(self):
        current = self.ui.formatList.currentItem()
        if current is not None:
            current = str(current.text())
        self.ui.formatList.clear()
        self.exporterClasses = {}
        gotCurrent = False
        for exp in exporters.listExporters():
            self.ui.formatList.addItem(exp.Name)
            self.exporterClasses[exp.Name] = exp
            if exp.Name == current:
                self.ui.formatList.setCurrentRow(self.ui.formatList.count()-1)
                gotCurrent = True
                
        if not gotCurrent:
            self.ui.formatList.setCurrentRow(0)
        
    def exportFormatChanged(self, item, prev):
        if item is None:
            self.currentExporter = None
            self.ui.paramTree.clear()
            return
        expClass = self.exporterClasses[str(item.text())]
        exp = expClass(item=self.ui.itemTree.currentItem().gitem)
        params = exp.parameters()
        if params is None:
            self.ui.paramTree.clear()
        else:
            self.ui.paramTree.setParameters(params)
        self.currentExporter = exp
        self.ui.copyBtn.setEnabled(exp.allowCopy)
        
    def exportClicked(self):
        self.selectBox.hide()
        self.currentExporter.export()
        
    def copyClicked(self):
        self.selectBox.hide()
        self.currentExporter.export(copy=True)
        
    def close(self):
        self.selectBox.setVisible(False)
        self.setVisible(False)


    
