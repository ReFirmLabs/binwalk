# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './GraphicsScene/exportDialogTemplate.ui'
#
# Created: Wed Jan 30 21:02:28 2013
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
        Form.resize(241, 367)
        self.gridLayout = QtGui.QGridLayout(Form)
        self.gridLayout.setSpacing(0)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.label = QtGui.QLabel(Form)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 0, 0, 1, 3)
        self.itemTree = QtGui.QTreeWidget(Form)
        self.itemTree.setObjectName(_fromUtf8("itemTree"))
        self.itemTree.headerItem().setText(0, _fromUtf8("1"))
        self.itemTree.header().setVisible(False)
        self.gridLayout.addWidget(self.itemTree, 1, 0, 1, 3)
        self.label_2 = QtGui.QLabel(Form)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.gridLayout.addWidget(self.label_2, 2, 0, 1, 3)
        self.formatList = QtGui.QListWidget(Form)
        self.formatList.setObjectName(_fromUtf8("formatList"))
        self.gridLayout.addWidget(self.formatList, 3, 0, 1, 3)
        self.exportBtn = QtGui.QPushButton(Form)
        self.exportBtn.setObjectName(_fromUtf8("exportBtn"))
        self.gridLayout.addWidget(self.exportBtn, 6, 1, 1, 1)
        self.closeBtn = QtGui.QPushButton(Form)
        self.closeBtn.setObjectName(_fromUtf8("closeBtn"))
        self.gridLayout.addWidget(self.closeBtn, 6, 2, 1, 1)
        self.paramTree = ParameterTree(Form)
        self.paramTree.setObjectName(_fromUtf8("paramTree"))
        self.paramTree.headerItem().setText(0, _fromUtf8("1"))
        self.paramTree.header().setVisible(False)
        self.gridLayout.addWidget(self.paramTree, 5, 0, 1, 3)
        self.label_3 = QtGui.QLabel(Form)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.gridLayout.addWidget(self.label_3, 4, 0, 1, 3)
        self.copyBtn = QtGui.QPushButton(Form)
        self.copyBtn.setObjectName(_fromUtf8("copyBtn"))
        self.gridLayout.addWidget(self.copyBtn, 6, 0, 1, 1)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(QtGui.QApplication.translate("Form", "Export", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("Form", "Item to export:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("Form", "Export format", None, QtGui.QApplication.UnicodeUTF8))
        self.exportBtn.setText(QtGui.QApplication.translate("Form", "Export", None, QtGui.QApplication.UnicodeUTF8))
        self.closeBtn.setText(QtGui.QApplication.translate("Form", "Close", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("Form", "Export options", None, QtGui.QApplication.UnicodeUTF8))
        self.copyBtn.setText(QtGui.QApplication.translate("Form", "Copy", None, QtGui.QApplication.UnicodeUTF8))

from pyqtgraph.parametertree import ParameterTree
