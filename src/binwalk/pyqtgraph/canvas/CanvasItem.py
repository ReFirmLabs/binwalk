# -*- coding: utf-8 -*-
from pyqtgraph.Qt import QtGui, QtCore, QtSvg, USE_PYSIDE
from pyqtgraph.graphicsItems.ROI import ROI
import pyqtgraph as pg
if USE_PYSIDE:
    from . import TransformGuiTemplate_pyside as TransformGuiTemplate
else:
    from . import TransformGuiTemplate_pyqt as TransformGuiTemplate

from pyqtgraph import debug

class SelectBox(ROI):
    def __init__(self, scalable=False, rotatable=True):
        #QtGui.QGraphicsRectItem.__init__(self, 0, 0, size[0], size[1])
        ROI.__init__(self, [0,0], [1,1], invertible=True)
        center = [0.5, 0.5]
            
        if scalable:
            self.addScaleHandle([1, 1], center, lockAspect=True)
            self.addScaleHandle([0, 0], center, lockAspect=True)
        if rotatable:
            self.addRotateHandle([0, 1], center)
            self.addRotateHandle([1, 0], center)

class CanvasItem(QtCore.QObject):
    
    sigResetUserTransform = QtCore.Signal(object)
    sigTransformChangeFinished = QtCore.Signal(object)
    sigTransformChanged = QtCore.Signal(object)
    
    """CanvasItem takes care of managing an item's state--alpha, visibility, z-value, transformations, etc. and
    provides a control widget"""
    
    sigVisibilityChanged = QtCore.Signal(object)
    transformCopyBuffer = None
    
    def __init__(self, item, **opts):
        defOpts = {'name': None, 'z': None, 'movable': True, 'scalable': False, 'rotatable': True, 'visible': True, 'parent':None} #'pos': [0,0], 'scale': [1,1], 'angle':0,
        defOpts.update(opts)
        self.opts = defOpts
        self.selectedAlone = False  ## whether this item is the only one selected
        
        QtCore.QObject.__init__(self)
        self.canvas = None
        self._graphicsItem = item
        
        parent = self.opts['parent']
        if parent is not None:
            self._graphicsItem.setParentItem(parent.graphicsItem())
            self._parentItem = parent
        else:
            self._parentItem = None
        
        z = self.opts['z']
        if z is not None:
            item.setZValue(z)

        self.ctrl = QtGui.QWidget()
        self.layout = QtGui.QGridLayout()
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0,0,0,0)
        self.ctrl.setLayout(self.layout)
        
        self.alphaLabel = QtGui.QLabel("Alpha")
        self.alphaSlider = QtGui.QSlider()
        self.alphaSlider.setMaximum(1023)
        self.alphaSlider.setOrientation(QtCore.Qt.Horizontal)
        self.alphaSlider.setValue(1023)
        self.layout.addWidget(self.alphaLabel, 0, 0)
        self.layout.addWidget(self.alphaSlider, 0, 1)
        self.resetTransformBtn = QtGui.QPushButton('Reset Transform')
        self.copyBtn = QtGui.QPushButton('Copy')
        self.pasteBtn = QtGui.QPushButton('Paste')
        
        self.transformWidget = QtGui.QWidget()
        self.transformGui = TransformGuiTemplate.Ui_Form()
        self.transformGui.setupUi(self.transformWidget)
        self.layout.addWidget(self.transformWidget, 3, 0, 1, 2)
        self.transformGui.mirrorImageBtn.clicked.connect(self.mirrorY)
        self.transformGui.reflectImageBtn.clicked.connect(self.mirrorXY)
        
        self.layout.addWidget(self.resetTransformBtn, 1, 0, 1, 2)
        self.layout.addWidget(self.copyBtn, 2, 0, 1, 1)
        self.layout.addWidget(self.pasteBtn, 2, 1, 1, 1)
        self.alphaSlider.valueChanged.connect(self.alphaChanged)
        self.alphaSlider.sliderPressed.connect(self.alphaPressed)
        self.alphaSlider.sliderReleased.connect(self.alphaReleased)
        #self.canvas.sigSelectionChanged.connect(self.selectionChanged)
        self.resetTransformBtn.clicked.connect(self.resetTransformClicked)
        self.copyBtn.clicked.connect(self.copyClicked)
        self.pasteBtn.clicked.connect(self.pasteClicked)
        
        self.setMovable(self.opts['movable'])  ## update gui to reflect this option


        if 'transform' in self.opts:
            self.baseTransform = self.opts['transform']
        else:
            self.baseTransform = pg.SRTTransform()
            if 'pos' in self.opts and self.opts['pos'] is not None:
                self.baseTransform.translate(self.opts['pos'])
            if 'angle' in self.opts and self.opts['angle'] is not None:
                self.baseTransform.rotate(self.opts['angle'])
            if 'scale' in self.opts and self.opts['scale'] is not None:
                self.baseTransform.scale(self.opts['scale'])

        ## create selection box (only visible when selected)
        tr = self.baseTransform.saveState()
        if 'scalable' not in opts and tr['scale'] == (1,1):
            self.opts['scalable'] = True
            
        ## every CanvasItem implements its own individual selection box 
        ## so that subclasses are free to make their own.
        self.selectBox = SelectBox(scalable=self.opts['scalable'], rotatable=self.opts['rotatable'])
        #self.canvas.scene().addItem(self.selectBox)
        self.selectBox.hide()
        self.selectBox.setZValue(1e6)
        self.selectBox.sigRegionChanged.connect(self.selectBoxChanged)  ## calls selectBoxMoved
        self.selectBox.sigRegionChangeFinished.connect(self.selectBoxChangeFinished)

        ## set up the transformations that will be applied to the item
        ## (It is not safe to use item.setTransform, since the item might count on that not changing)
        self.itemRotation = QtGui.QGraphicsRotation()
        self.itemScale = QtGui.QGraphicsScale()
        self._graphicsItem.setTransformations([self.itemRotation, self.itemScale])
        
        self.tempTransform = pg.SRTTransform() ## holds the additional transform that happens during a move - gets added to the userTransform when move is done.
        self.userTransform = pg.SRTTransform() ## stores the total transform of the object
        self.resetUserTransform() 
        
        ## now happens inside resetUserTransform -> selectBoxToItem
        # self.selectBoxBase = self.selectBox.getState().copy()
        
                
        #print "Created canvas item", self
        #print "  base:", self.baseTransform
        #print "  user:", self.userTransform
        #print "  temp:", self.tempTransform
        #print "  bounds:", self.item.sceneBoundingRect()
        
    def setMovable(self, m):
        self.opts['movable'] = m
        
        if m:
            self.resetTransformBtn.show()
            self.copyBtn.show()
            self.pasteBtn.show()
        else:
            self.resetTransformBtn.hide()
            self.copyBtn.hide()
            self.pasteBtn.hide()

    def setCanvas(self, canvas):
        ## Called by canvas whenever the item is added.
        ## It is our responsibility to add all graphicsItems to the canvas's scene
        ## The canvas will automatically add our graphicsitem, 
        ## so we just need to take care of the selectbox.
        if canvas is self.canvas:
            return
            
        if canvas is None:
            self.canvas.removeFromScene(self._graphicsItem)
            self.canvas.removeFromScene(self.selectBox)
        else:
            canvas.addToScene(self._graphicsItem)
            canvas.addToScene(self.selectBox)
        self.canvas = canvas

    def graphicsItem(self):
        """Return the graphicsItem for this canvasItem."""
        return self._graphicsItem
        
    def parentItem(self):
        return self._parentItem

    def setParentItem(self, parent):
        self._parentItem = parent
        if parent is not None:
            if isinstance(parent, CanvasItem):
                parent = parent.graphicsItem()
        self.graphicsItem().setParentItem(parent)

    #def name(self):
        #return self.opts['name']
    
    def copyClicked(self):
        CanvasItem.transformCopyBuffer = self.saveTransform()
        
    def pasteClicked(self):
        t = CanvasItem.transformCopyBuffer
        if t is None:
            return
        else:
            self.restoreTransform(t)
            
    def mirrorY(self):
        if not self.isMovable():
            return
        
        #flip = self.transformGui.mirrorImageCheck.isChecked()
        #tr = self.userTransform.saveState()
        
        inv = pg.SRTTransform()
        inv.scale(-1, 1)
        self.userTransform = self.userTransform * inv
        self.updateTransform()
        self.selectBoxFromUser()
        self.sigTransformChangeFinished.emit(self)
        #if flip:
            #if tr['scale'][0] < 0 xor tr['scale'][1] < 0:
                #return
            #else:
                #self.userTransform.setScale([-tr['scale'][0], tr['scale'][1]])
                #self.userTransform.setTranslate([-tr['pos'][0], tr['pos'][1]])
                #self.userTransform.setRotate(-tr['angle'])
                #self.updateTransform()
                #self.selectBoxFromUser()
                #return
        #elif not flip:
            #if tr['scale'][0] > 0 and tr['scale'][1] > 0:
                #return
            #else:
                #self.userTransform.setScale([-tr['scale'][0], tr['scale'][1]])
                #self.userTransform.setTranslate([-tr['pos'][0], tr['pos'][1]])
                #self.userTransform.setRotate(-tr['angle'])
                #self.updateTransform()
                #self.selectBoxFromUser()
                #return

    def mirrorXY(self):
        if not self.isMovable():
            return
        self.rotate(180.)
        # inv = pg.SRTTransform()
        # inv.scale(-1, -1)
        # self.userTransform = self.userTransform * inv #flip lr/ud
        # s=self.updateTransform()
        # self.setTranslate(-2*s['pos'][0], -2*s['pos'][1])
        # self.selectBoxFromUser()
        
 
    def hasUserTransform(self):
        #print self.userRotate, self.userTranslate
        return not self.userTransform.isIdentity()

    def ctrlWidget(self):
        return self.ctrl
        
    def alphaChanged(self, val):
        alpha = val / 1023.
        self._graphicsItem.setOpacity(alpha)
        
    def isMovable(self):
        return self.opts['movable']
        
        
    def selectBoxMoved(self):
        """The selection box has moved; get its transformation information and pass to the graphics item"""
        self.userTransform = self.selectBox.getGlobalTransform(relativeTo=self.selectBoxBase)
        self.updateTransform()

    def scale(self, x, y):
        self.userTransform.scale(x, y)
        self.selectBoxFromUser()
        self.updateTransform()
        
    def rotate(self, ang):
        self.userTransform.rotate(ang)
        self.selectBoxFromUser()
        self.updateTransform()
        
    def translate(self, x, y):
        self.userTransform.translate(x, y)
        self.selectBoxFromUser()
        self.updateTransform()
        
    def setTranslate(self, x, y):
        self.userTransform.setTranslate(x, y)
        self.selectBoxFromUser()
        self.updateTransform()
        
    def setRotate(self, angle):
        self.userTransform.setRotate(angle)
        self.selectBoxFromUser()
        self.updateTransform()
        
    def setScale(self, x, y):
        self.userTransform.setScale(x, y)
        self.selectBoxFromUser()
        self.updateTransform()
        

    def setTemporaryTransform(self, transform):
        self.tempTransform = transform
        self.updateTransform()
    
    def applyTemporaryTransform(self):
        """Collapses tempTransform into UserTransform, resets tempTransform"""
        self.userTransform = self.userTransform * self.tempTransform ## order is important!
        self.resetTemporaryTransform()
        self.selectBoxFromUser()  ## update the selection box to match the new userTransform

        #st = self.userTransform.saveState()
        
        #self.userTransform = self.userTransform * self.tempTransform ## order is important!
        
        #### matrix multiplication affects the scale factors, need to reset
        #if st['scale'][0] < 0 or st['scale'][1] < 0:
            #nst = self.userTransform.saveState()
            #self.userTransform.setScale([-nst['scale'][0], -nst['scale'][1]])
        
        #self.resetTemporaryTransform()
        #self.selectBoxFromUser()
        #self.selectBoxChangeFinished()



    def resetTemporaryTransform(self):
        self.tempTransform = pg.SRTTransform()  ## don't use Transform.reset()--this transform might be used elsewhere.
        self.updateTransform()
        
    def transform(self): 
        return self._graphicsItem.transform()

    def updateTransform(self):
        """Regenerate the item position from the base, user, and temp transforms"""
        transform = self.baseTransform * self.userTransform * self.tempTransform ## order is important
        s = transform.saveState()
        self._graphicsItem.setPos(*s['pos'])
        
        self.itemRotation.setAngle(s['angle'])
        self.itemScale.setXScale(s['scale'][0])
        self.itemScale.setYScale(s['scale'][1])

        self.displayTransform(transform)
        return(s) # return the transform state
        
    def displayTransform(self, transform):
        """Updates transform numbers in the ctrl widget."""
        
        tr = transform.saveState()
        
        self.transformGui.translateLabel.setText("Translate: (%f, %f)" %(tr['pos'][0], tr['pos'][1]))
        self.transformGui.rotateLabel.setText("Rotate: %f degrees" %tr['angle'])
        self.transformGui.scaleLabel.setText("Scale: (%f, %f)" %(tr['scale'][0], tr['scale'][1]))
        #self.transformGui.mirrorImageCheck.setChecked(False)
        #if tr['scale'][0] < 0:
        #    self.transformGui.mirrorImageCheck.setChecked(True)


    def resetUserTransform(self):
        #self.userRotate = 0
        #self.userTranslate = pg.Point(0,0)
        self.userTransform.reset()
        self.updateTransform()
        
        self.selectBox.blockSignals(True)
        self.selectBoxToItem()
        self.selectBox.blockSignals(False)
        self.sigTransformChanged.emit(self)
        self.sigTransformChangeFinished.emit(self)
       
    def resetTransformClicked(self):
        self.resetUserTransform()
        self.sigResetUserTransform.emit(self)
        
    def restoreTransform(self, tr):
        try:
            #self.userTranslate = pg.Point(tr['trans'])
            #self.userRotate = tr['rot']
            self.userTransform = pg.SRTTransform(tr)
            self.updateTransform()
            
            self.selectBoxFromUser() ## move select box to match
            self.sigTransformChanged.emit(self)
            self.sigTransformChangeFinished.emit(self)
        except:
            #self.userTranslate = pg.Point([0,0])
            #self.userRotate = 0
            self.userTransform = pg.SRTTransform()
            debug.printExc("Failed to load transform:")
        #print "set transform", self, self.userTranslate
        
    def saveTransform(self):
        """Return a dict containing the current user transform"""
        #print "save transform", self, self.userTranslate
        #return {'trans': list(self.userTranslate), 'rot': self.userRotate}
        return self.userTransform.saveState()
        
    def selectBoxFromUser(self):
        """Move the selection box to match the current userTransform"""
        ## user transform
        #trans = QtGui.QTransform()
        #trans.translate(*self.userTranslate)
        #trans.rotate(-self.userRotate)
        
        #x2, y2 = trans.map(*self.selectBoxBase['pos'])
        
        self.selectBox.blockSignals(True)
        self.selectBox.setState(self.selectBoxBase)
        self.selectBox.applyGlobalTransform(self.userTransform)
        #self.selectBox.setAngle(self.userRotate)
        #self.selectBox.setPos([x2, y2])
        self.selectBox.blockSignals(False)
        

    def selectBoxToItem(self):
        """Move/scale the selection box so it fits the item's bounding rect. (assumes item is not rotated)"""
        self.itemRect = self._graphicsItem.boundingRect()
        rect = self._graphicsItem.mapRectToParent(self.itemRect)
        self.selectBox.blockSignals(True)
        self.selectBox.setPos([rect.x(), rect.y()])
        self.selectBox.setSize(rect.size())
        self.selectBox.setAngle(0)
        self.selectBoxBase = self.selectBox.getState().copy()
        self.selectBox.blockSignals(False)

    def zValue(self):
        return self.opts['z']
        
    def setZValue(self, z):
        self.opts['z'] = z
        if z is not None:
            self._graphicsItem.setZValue(z)
        
    #def selectionChanged(self, canvas, items):
        #self.selected = len(items) == 1 and (items[0] is self) 
        #self.showSelectBox()
           
           
    def selectionChanged(self, sel, multi):
        """
        Inform the item that its selection state has changed. 
        Arguments:
            sel: bool, whether the item is currently selected
            multi: bool, whether there are multiple items currently selected
        """
        self.selectedAlone = sel and not multi
        self.showSelectBox()
        if self.selectedAlone:
            self.ctrlWidget().show()
        else:
            self.ctrlWidget().hide()
        
    def showSelectBox(self):
        """Display the selection box around this item if it is selected and movable"""
        if self.selectedAlone and self.isMovable() and self.isVisible():  #and len(self.canvas.itemList.selectedItems())==1:
            self.selectBox.show()
        else:
            self.selectBox.hide()
        
    def hideSelectBox(self):
        self.selectBox.hide()
        
                
    def selectBoxChanged(self):
        self.selectBoxMoved()
        #self.updateTransform(self.selectBox)
        #self.emit(QtCore.SIGNAL('transformChanged'), self)
        self.sigTransformChanged.emit(self)
        
    def selectBoxChangeFinished(self):
        #self.emit(QtCore.SIGNAL('transformChangeFinished'), self)
        self.sigTransformChangeFinished.emit(self)

    def alphaPressed(self):
        """Hide selection box while slider is moving"""
        self.hideSelectBox()
        
    def alphaReleased(self):
        self.showSelectBox()
        
    def show(self):
        if self.opts['visible']:
            return
        self.opts['visible'] = True
        self._graphicsItem.show()
        self.showSelectBox()
        self.sigVisibilityChanged.emit(self)
        
    def hide(self):
        if not self.opts['visible']:
            return
        self.opts['visible'] = False
        self._graphicsItem.hide()
        self.hideSelectBox()
        self.sigVisibilityChanged.emit(self)

    def setVisible(self, vis):
        if vis:
            self.show()
        else:
            self.hide()

    def isVisible(self):
        return self.opts['visible']


class GroupCanvasItem(CanvasItem):
    """
    Canvas item used for grouping others
    """
    
    def __init__(self, **opts):
        defOpts = {'movable': False, 'scalable': False}
        defOpts.update(opts)
        item = pg.ItemGroup()
        CanvasItem.__init__(self, item, **defOpts)
    
