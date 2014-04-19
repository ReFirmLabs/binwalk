"""
ViewBox test cases:

* call setRange then resize; requested range must be fully visible
* lockAspect works correctly for arbitrary aspect ratio
* autoRange works correctly with aspect locked
* call setRange with aspect locked, then resize
* AutoRange with all the bells and whistles
    * item moves / changes transformation / changes bounds
    * pan only
    * fractional range


"""

import pyqtgraph as pg
app = pg.mkQApp()

imgData = pg.np.zeros((10, 10))
imgData[0] = 3
imgData[-1] = 3
imgData[:,0] = 3
imgData[:,-1] = 3

def testLinkWithAspectLock():
    global win, vb
    win = pg.GraphicsWindow()
    vb = win.addViewBox(name="image view")
    vb.setAspectLocked()
    vb.enableAutoRange(x=False, y=False)
    p1 = win.addPlot(name="plot 1")
    p2 = win.addPlot(name="plot 2", row=1, col=0)
    win.ci.layout.setRowFixedHeight(1, 150)
    win.ci.layout.setColumnFixedWidth(1, 150)

    def viewsMatch():
        r0 = pg.np.array(vb.viewRange())
        r1 = pg.np.array(p1.vb.viewRange()[1])
        r2 = pg.np.array(p2.vb.viewRange()[1])
        match = (abs(r0[1]-r1) <= (abs(r1) * 0.001)).all() and (abs(r0[0]-r2) <= (abs(r2) * 0.001)).all()
        return match

    p1.setYLink(vb)
    p2.setXLink(vb)
    print "link views match:", viewsMatch()
    win.show()
    print "show views match:", viewsMatch()
    img = pg.ImageItem(imgData)
    vb.addItem(img)
    vb.autoRange()
    p1.plot(x=imgData.sum(axis=0), y=range(10))
    p2.plot(x=range(10), y=imgData.sum(axis=1))
    print "add items views match:", viewsMatch()
    #p1.setAspectLocked()
    #grid = pg.GridItem()
    #vb.addItem(grid)
    pg.QtGui.QApplication.processEvents()
    pg.QtGui.QApplication.processEvents()
    #win.resize(801, 600)

def testAspectLock():
    global win, vb
    win = pg.GraphicsWindow()
    vb = win.addViewBox(name="image view")
    vb.setAspectLocked()
    img = pg.ImageItem(imgData)
    vb.addItem(img)
    
    
#app.processEvents()
#print "init views match:", viewsMatch()
#p2.setYRange(-300, 300)
#print "setRange views match:", viewsMatch()
#app.processEvents()
#print "setRange views match (after update):", viewsMatch()

#print "--lock aspect--"
#p1.setAspectLocked(True)
#print "lockAspect views match:", viewsMatch()
#p2.setYRange(-200, 200)
#print "setRange views match:", viewsMatch()
#app.processEvents()
#print "setRange views match (after update):", viewsMatch()

#win.resize(100, 600)
#app.processEvents()
#vb.setRange(xRange=[-10, 10], padding=0)
#app.processEvents()
#win.resize(600, 100)
#app.processEvents()
#print vb.viewRange()


if __name__ == '__main__':
    testLinkWithAspectLock()
