# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './canvas/CanvasTemplate.ui'
#
# Created: Sun Sep  9 14:41:30 2012
#      by: PyQt4 UI code generator 4.9.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName(_fromUtf8("Form"))
        Form.resize(490, 414)
        self.gridLayout = QtGui.QGridLayout(Form)
        self.gridLayout.setMargin(0)
        self.gridLayout.setSpacing(0)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.splitter = QtGui.QSplitter(Form)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName(_fromUtf8("splitter"))
        self.view = GraphicsView(self.splitter)
        self.view.setObjectName(_fromUtf8("view"))
        self.layoutWidget = QtGui.QWidget(self.splitter)
        self.layoutWidget.setObjectName(_fromUtf8("layoutWidget"))
        self.gridLayout_2 = QtGui.QGridLayout(self.layoutWidget)
        self.gridLayout_2.setMargin(0)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.storeSvgBtn = QtGui.QPushButton(self.layoutWidget)
        self.storeSvgBtn.setObjectName(_fromUtf8("storeSvgBtn"))
        self.gridLayout_2.addWidget(self.storeSvgBtn, 1, 0, 1, 1)
        self.storePngBtn = QtGui.QPushButton(self.layoutWidget)
        self.storePngBtn.setObjectName(_fromUtf8("storePngBtn"))
        self.gridLayout_2.addWidget(self.storePngBtn, 1, 1, 1, 1)
        self.autoRangeBtn = QtGui.QPushButton(self.layoutWidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.autoRangeBtn.sizePolicy().hasHeightForWidth())
        self.autoRangeBtn.setSizePolicy(sizePolicy)
        self.autoRangeBtn.setObjectName(_fromUtf8("autoRangeBtn"))
        self.gridLayout_2.addWidget(self.autoRangeBtn, 3, 0, 1, 2)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.redirectCheck = QtGui.QCheckBox(self.layoutWidget)
        self.redirectCheck.setObjectName(_fromUtf8("redirectCheck"))
        self.horizontalLayout.addWidget(self.redirectCheck)
        self.redirectCombo = CanvasCombo(self.layoutWidget)
        self.redirectCombo.setObjectName(_fromUtf8("redirectCombo"))
        self.horizontalLayout.addWidget(self.redirectCombo)
        self.gridLayout_2.addLayout(self.horizontalLayout, 6, 0, 1, 2)
        self.itemList = TreeWidget(self.layoutWidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(100)
        sizePolicy.setHeightForWidth(self.itemList.sizePolicy().hasHeightForWidth())
        self.itemList.setSizePolicy(sizePolicy)
        self.itemList.setHeaderHidden(True)
        self.itemList.setObjectName(_fromUtf8("itemList"))
        self.itemList.headerItem().setText(0, _fromUtf8("1"))
        self.gridLayout_2.addWidget(self.itemList, 7, 0, 1, 2)
        self.ctrlLayout = QtGui.QGridLayout()
        self.ctrlLayout.setSpacing(0)
        self.ctrlLayout.setObjectName(_fromUtf8("ctrlLayout"))
        self.gridLayout_2.addLayout(self.ctrlLayout, 11, 0, 1, 2)
        self.resetTransformsBtn = QtGui.QPushButton(self.layoutWidget)
        self.resetTransformsBtn.setObjectName(_fromUtf8("resetTransformsBtn"))
        self.gridLayout_2.addWidget(self.resetTransformsBtn, 8, 0, 1, 1)
        self.mirrorSelectionBtn = QtGui.QPushButton(self.layoutWidget)
        self.mirrorSelectionBtn.setObjectName(_fromUtf8("mirrorSelectionBtn"))
        self.gridLayout_2.addWidget(self.mirrorSelectionBtn, 4, 0, 1, 1)
        self.reflectSelectionBtn = QtGui.QPushButton(self.layoutWidget)
        self.reflectSelectionBtn.setObjectName(_fromUtf8("reflectSelectionBtn"))
        self.gridLayout_2.addWidget(self.reflectSelectionBtn, 4, 1, 1, 1)
        self.gridLayout.addWidget(self.splitter, 0, 0, 1, 1)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(QtGui.QApplication.translate("Form", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.storeSvgBtn.setText(QtGui.QApplication.translate("Form", "Store SVG", None, QtGui.QApplication.UnicodeUTF8))
        self.storePngBtn.setText(QtGui.QApplication.translate("Form", "Store PNG", None, QtGui.QApplication.UnicodeUTF8))
        self.autoRangeBtn.setText(QtGui.QApplication.translate("Form", "Auto Range", None, QtGui.QApplication.UnicodeUTF8))
        self.redirectCheck.setToolTip(QtGui.QApplication.translate("Form", "Check to display all local items in a remote canvas.", None, QtGui.QApplication.UnicodeUTF8))
        self.redirectCheck.setText(QtGui.QApplication.translate("Form", "Redirect", None, QtGui.QApplication.UnicodeUTF8))
        self.resetTransformsBtn.setText(QtGui.QApplication.translate("Form", "Reset Transforms", None, QtGui.QApplication.UnicodeUTF8))
        self.mirrorSelectionBtn.setText(QtGui.QApplication.translate("Form", "Mirror Selection", None, QtGui.QApplication.UnicodeUTF8))
        self.reflectSelectionBtn.setText(QtGui.QApplication.translate("Form", "MirrorXY", None, QtGui.QApplication.UnicodeUTF8))

from pyqtgraph.widgets.GraphicsView import GraphicsView
from CanvasManager import CanvasCombo
from pyqtgraph.widgets.TreeWidget import TreeWidget
