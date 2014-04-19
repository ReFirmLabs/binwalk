# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './GraphicsScene/exportDialogTemplate.ui'
#
# Created: Wed Jan 30 21:02:28 2013
#      by: pyside-uic 0.2.13 running on PySide 1.1.1
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(241, 367)
        self.gridLayout = QtGui.QGridLayout(Form)
        self.gridLayout.setSpacing(0)
        self.gridLayout.setObjectName("gridLayout")
        self.label = QtGui.QLabel(Form)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 3)
        self.itemTree = QtGui.QTreeWidget(Form)
        self.itemTree.setObjectName("itemTree")
        self.itemTree.headerItem().setText(0, "1")
        self.itemTree.header().setVisible(False)
        self.gridLayout.addWidget(self.itemTree, 1, 0, 1, 3)
        self.label_2 = QtGui.QLabel(Form)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 2, 0, 1, 3)
        self.formatList = QtGui.QListWidget(Form)
        self.formatList.setObjectName("formatList")
        self.gridLayout.addWidget(self.formatList, 3, 0, 1, 3)
        self.exportBtn = QtGui.QPushButton(Form)
        self.exportBtn.setObjectName("exportBtn")
        self.gridLayout.addWidget(self.exportBtn, 6, 1, 1, 1)
        self.closeBtn = QtGui.QPushButton(Form)
        self.closeBtn.setObjectName("closeBtn")
        self.gridLayout.addWidget(self.closeBtn, 6, 2, 1, 1)
        self.paramTree = ParameterTree(Form)
        self.paramTree.setObjectName("paramTree")
        self.paramTree.headerItem().setText(0, "1")
        self.paramTree.header().setVisible(False)
        self.gridLayout.addWidget(self.paramTree, 5, 0, 1, 3)
        self.label_3 = QtGui.QLabel(Form)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 4, 0, 1, 3)
        self.copyBtn = QtGui.QPushButton(Form)
        self.copyBtn.setObjectName("copyBtn")
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
