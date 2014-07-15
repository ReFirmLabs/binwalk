import sys, os, subprocess, time

if __name__ == "__main__" and (__package__ is None or __package__==''):
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, parent_dir)
    import examples
    __package__ = "examples"

from . import initExample
from pyqtgraph.Qt import QtCore, QtGui, USE_PYSIDE

if USE_PYSIDE:
    from .exampleLoaderTemplate_pyside import Ui_Form
else:
    from .exampleLoaderTemplate_pyqt import Ui_Form
    
import os, sys
from pyqtgraph.pgcollections import OrderedDict

examples = OrderedDict([
    ('Command-line usage', 'CLIexample.py'),
    ('Basic Plotting', 'Plotting.py'),
    ('ImageView', 'ImageView.py'),
    ('ParameterTree', 'parametertree.py'),
    ('Crosshair / Mouse interaction', 'crosshair.py'),
    ('Data Slicing', 'DataSlicing.py'),
    ('Plot Customization', 'customPlot.py'),
    ('Dock widgets', 'dockarea.py'),
    ('Console', 'ConsoleWidget.py'),
    ('Histograms', 'histogram.py'),
    ('Auto-range', 'PlotAutoRange.py'),
    ('Remote Plotting', 'RemoteSpeedTest.py'),
    ('GraphicsItems', OrderedDict([
        ('Scatter Plot', 'ScatterPlot.py'),
        #('PlotItem', 'PlotItem.py'),
        ('IsocurveItem', 'isocurve.py'),
        ('GraphItem', 'GraphItem.py'),
        ('ErrorBarItem', 'ErrorBarItem.py'),
        ('ImageItem - video', 'ImageItem.py'),
        ('ImageItem - draw', 'Draw.py'),
        ('Region-of-Interest', 'ROIExamples.py'),
        ('GraphicsLayout', 'GraphicsLayout.py'),
        ('LegendItem', 'Legend.py'),
        ('Text Item', 'text.py'),
        ('Linked Views', 'linkedViews.py'),
        ('Arrow', 'Arrow.py'),
        ('ViewBox', 'ViewBox.py'),
        ('Custom Graphics', 'customGraphicsItem.py'),
    ])),
    ('Benchmarks', OrderedDict([
        ('Video speed test', 'VideoSpeedTest.py'),
        ('Line Plot update', 'PlotSpeedTest.py'),
        ('Scatter Plot update', 'ScatterPlotSpeedTest.py'),
    ])),
    ('3D Graphics', OrderedDict([
        ('Volumetric', 'GLVolumeItem.py'),
        ('Isosurface', 'GLIsosurface.py'),
        ('Surface Plot', 'GLSurfacePlot.py'),
        ('Scatter Plot', 'GLScatterPlotItem.py'),
        ('Shaders', 'GLshaders.py'),
        ('Line Plot', 'GLLinePlotItem.py'),
        ('Mesh', 'GLMeshItem.py'),
        ('Image', 'GLImageItem.py'),
    ])),
    ('Widgets', OrderedDict([
        ('PlotWidget', 'PlotWidget.py'),
        ('SpinBox', 'SpinBox.py'),
        ('ConsoleWidget', 'ConsoleWidget.py'),
        ('Histogram / lookup table', 'HistogramLUT.py'),
        ('TreeWidget', 'TreeWidget.py'),
        ('DataTreeWidget', 'DataTreeWidget.py'),
        ('GradientWidget', 'GradientWidget.py'),
        ('TableWidget', 'TableWidget.py'),
        ('ColorButton', 'ColorButton.py'),
        #('CheckTable', '../widgets/CheckTable.py'),
        #('VerticalLabel', '../widgets/VerticalLabel.py'),
        ('JoystickButton', 'JoystickButton.py'),
    ])),
    
    #('GraphicsScene', 'GraphicsScene.py'),
    ('Flowcharts', 'Flowchart.py'),
    ('Custom Flowchart Nodes', 'FlowchartCustomNode.py'),
    #('Canvas', '../canvas'),
    #('MultiPlotWidget', 'MultiPlotWidget.py'),
])

path = os.path.abspath(os.path.dirname(__file__))

class ExampleLoader(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.ui = Ui_Form()
        self.cw = QtGui.QWidget()
        self.setCentralWidget(self.cw)
        self.ui.setupUi(self.cw)
        
        self.codeBtn = QtGui.QPushButton('Run Edited Code')
        self.codeLayout = QtGui.QGridLayout()
        self.ui.codeView.setLayout(self.codeLayout)
        self.codeLayout.addItem(QtGui.QSpacerItem(100,100,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Expanding), 0, 0)
        self.codeLayout.addWidget(self.codeBtn, 1, 1)
        self.codeBtn.hide()
        
        global examples
        self.itemCache = []
        self.populateTree(self.ui.exampleTree.invisibleRootItem(), examples)
        self.ui.exampleTree.expandAll()
        
        self.resize(1000,500)
        self.show()
        self.ui.splitter.setSizes([250,750])
        self.ui.loadBtn.clicked.connect(self.loadFile)
        self.ui.exampleTree.currentItemChanged.connect(self.showFile)
        self.ui.exampleTree.itemDoubleClicked.connect(self.loadFile)
        self.ui.pyqtCheck.toggled.connect(self.pyqtToggled)
        self.ui.pysideCheck.toggled.connect(self.pysideToggled)
        self.ui.codeView.textChanged.connect(self.codeEdited)
        self.codeBtn.clicked.connect(self.runEditedCode)

    def pyqtToggled(self, b):
        if b:
            self.ui.pysideCheck.setChecked(False)
        
    def pysideToggled(self, b):
        if b:
            self.ui.pyqtCheck.setChecked(False)
        

    def populateTree(self, root, examples):
        for key, val in examples.items():
            item = QtGui.QTreeWidgetItem([key])
            self.itemCache.append(item) # PyQt 4.9.6 no longer keeps references to these wrappers,
                                        # so we need to make an explicit reference or else the .file
                                        # attribute will disappear.
            if isinstance(val, basestring):
                item.file = val
            else:
                self.populateTree(item, val)
            root.addChild(item)
            
    
    def currentFile(self):
        item = self.ui.exampleTree.currentItem()
        if hasattr(item, 'file'):
            global path
            return os.path.join(path, item.file)
        return None
    
    def loadFile(self, edited=False):
        
        extra = []
        if self.ui.pyqtCheck.isChecked():
            extra.append('pyqt')
        elif self.ui.pysideCheck.isChecked():
            extra.append('pyside')
        
        if self.ui.forceGraphicsCheck.isChecked():
            extra.append(str(self.ui.forceGraphicsCombo.currentText()))

        
        #if sys.platform.startswith('win'):
            #os.spawnl(os.P_NOWAIT, sys.executable, '"'+sys.executable+'"', '"' + fn + '"', *extra)
        #else:
            #os.spawnl(os.P_NOWAIT, sys.executable, sys.executable, fn, *extra)
        
        if edited:
            path = os.path.abspath(os.path.dirname(__file__))
            proc = subprocess.Popen([sys.executable, '-'] + extra, stdin=subprocess.PIPE, cwd=path)
            code = str(self.ui.codeView.toPlainText()).encode('UTF-8')
            proc.stdin.write(code)
            proc.stdin.close()
        else:
            fn = self.currentFile()
            if fn is None:
                return
            if sys.platform.startswith('win'):
                os.spawnl(os.P_NOWAIT, sys.executable, '"'+sys.executable+'"', '"' + fn + '"', *extra)
            else:
                os.spawnl(os.P_NOWAIT, sys.executable, sys.executable, fn, *extra)
            
    def showFile(self):
        fn = self.currentFile()
        if fn is None:
            self.ui.codeView.clear()
            return
        if os.path.isdir(fn):
            fn = os.path.join(fn, '__main__.py')
        text = open(fn).read()
        self.ui.codeView.setPlainText(text)
        self.ui.loadedFileLabel.setText(fn)
        self.codeBtn.hide()
        
    def codeEdited(self):
        self.codeBtn.show()
        
    def runEditedCode(self):
        self.loadFile(edited=True)

def run():
    app = QtGui.QApplication([])
    loader = ExampleLoader()
    
    app.exec_()

def buildFileList(examples, files=None):
    if files == None:
        files = []
    for key, val in examples.items():
        #item = QtGui.QTreeWidgetItem([key])
        if isinstance(val, basestring):
            #item.file = val
            files.append((key,val))
        else:
            buildFileList(val, files)
    return files
            
def testFile(name, f, exe, lib, graphicsSystem=None):
    global path
    fn =  os.path.join(path,f)
    #print "starting process: ", fn
    os.chdir(path)
    sys.stdout.write(name)
    sys.stdout.flush()
    
    import1 = "import %s" % lib if lib != '' else ''
    import2 = os.path.splitext(os.path.split(fn)[1])[0]
    graphicsSystem = '' if graphicsSystem is None else "pg.QtGui.QApplication.setGraphicsSystem('%s')" % graphicsSystem
    code = """
try:
    %s
    import initExample
    import pyqtgraph as pg
    %s
    import %s
    import sys
    print("test complete")
    sys.stdout.flush()
    import time
    while True:  ## run a little event loop
        pg.QtGui.QApplication.processEvents()
        time.sleep(0.01)
except:
    print("test failed")
    raise

"""  % (import1, graphicsSystem, import2)

    if sys.platform.startswith('win'):
        process = subprocess.Popen([exe], stdin=subprocess.PIPE, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        process.stdin.write(code.encode('UTF-8'))
        process.stdin.close()
    else:
        process = subprocess.Popen(['exec %s -i' % (exe)], shell=True, stdin=subprocess.PIPE, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        process.stdin.write(code.encode('UTF-8'))
        process.stdin.close() ##?
    output = ''
    fail = False
    while True:
        c = process.stdout.read(1).decode()
        output += c
        #sys.stdout.write(c)
        #sys.stdout.flush()
        if output.endswith('test complete'):
            break
        if output.endswith('test failed'):
            fail = True
            break
    time.sleep(1)
    process.kill()
    #res = process.communicate()
    res = (process.stdout.read(), process.stderr.read())
    
    if fail or 'exception' in res[1].decode().lower() or 'error' in res[1].decode().lower():
        print('.' * (50-len(name)) + 'FAILED')
        print(res[0].decode())
        print(res[1].decode())
    else:
        print('.' * (50-len(name)) + 'passed')
    


if __name__ == '__main__':
    if '--test' in sys.argv[1:]:
        files = buildFileList(examples)
        if '--pyside' in sys.argv[1:]:
            lib = 'PySide'
        elif '--pyqt' in sys.argv[1:]:
            lib = 'PyQt4'
        else:
            lib = ''
            
        exe = sys.executable
        print("Running tests:", lib, sys.executable)
        for f in files:
            testFile(f[0], f[1], exe, lib)
    else: 
        run()
