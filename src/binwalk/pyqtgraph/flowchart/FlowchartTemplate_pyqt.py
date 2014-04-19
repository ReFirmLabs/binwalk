# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './flowchart/FlowchartTemplate.ui'
#
# Created: Sun Feb 24 19:47:29 2013
#      by: PyQt4 UI code generator 4.9.3
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
        Form.resize(529, 329)
        self.selInfoWidget = QtGui.QWidget(Form)
        self.selInfoWidget.setGeometry(QtCore.QRect(260, 10, 264, 222))
        self.selInfoWidget.setObjectName(_fromUtf8("selInfoWidget"))
        self.gridLayout = QtGui.QGridLayout(self.selInfoWidget)
        self.gridLayout.setMargin(0)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.selDescLabel = QtGui.QLabel(self.selInfoWidget)
        self.selDescLabel.setText(_fromUtf8(""))
        self.selDescLabel.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.selDescLabel.setWordWrap(True)
        self.selDescLabel.setObjectName(_fromUtf8("selDescLabel"))
        self.gridLayout.addWidget(self.selDescLabel, 0, 0, 1, 1)
        self.selNameLabel = QtGui.QLabel(self.selInfoWidget)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.selNameLabel.setFont(font)
        self.selNameLabel.setText(_fromUtf8(""))
        self.selNameLabel.setObjectName(_fromUtf8("selNameLabel"))
        self.gridLayout.addWidget(self.selNameLabel, 0, 1, 1, 1)
        self.selectedTree = DataTreeWidget(self.selInfoWidget)
        self.selectedTree.setObjectName(_fromUtf8("selectedTree"))
        self.selectedTree.headerItem().setText(0, _fromUtf8("1"))
        self.gridLayout.addWidget(self.selectedTree, 1, 0, 1, 2)
        self.hoverText = QtGui.QTextEdit(Form)
        self.hoverText.setGeometry(QtCore.QRect(0, 240, 521, 81))
        self.hoverText.setObjectName(_fromUtf8("hoverText"))
        self.view = FlowchartGraphicsView(Form)
        self.view.setGeometry(QtCore.QRect(0, 0, 256, 192))
        self.view.setObjectName(_fromUtf8("view"))

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(QtGui.QApplication.translate("Form", "Form", None, QtGui.QApplication.UnicodeUTF8))

from pyqtgraph.widgets.DataTreeWidget import DataTreeWidget
from pyqtgraph.flowchart.FlowchartGraphicsView import FlowchartGraphicsView
