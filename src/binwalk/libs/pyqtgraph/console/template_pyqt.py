# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './console/template.ui'
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
        Form.resize(710, 497)
        self.gridLayout = QtGui.QGridLayout(Form)
        self.gridLayout.setMargin(0)
        self.gridLayout.setSpacing(0)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.splitter = QtGui.QSplitter(Form)
        self.splitter.setOrientation(QtCore.Qt.Vertical)
        self.splitter.setObjectName(_fromUtf8("splitter"))
        self.layoutWidget = QtGui.QWidget(self.splitter)
        self.layoutWidget.setObjectName(_fromUtf8("layoutWidget"))
        self.verticalLayout = QtGui.QVBoxLayout(self.layoutWidget)
        self.verticalLayout.setMargin(0)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.output = QtGui.QPlainTextEdit(self.layoutWidget)
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Monospace"))
        self.output.setFont(font)
        self.output.setReadOnly(True)
        self.output.setObjectName(_fromUtf8("output"))
        self.verticalLayout.addWidget(self.output)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.input = CmdInput(self.layoutWidget)
        self.input.setObjectName(_fromUtf8("input"))
        self.horizontalLayout.addWidget(self.input)
        self.historyBtn = QtGui.QPushButton(self.layoutWidget)
        self.historyBtn.setCheckable(True)
        self.historyBtn.setObjectName(_fromUtf8("historyBtn"))
        self.horizontalLayout.addWidget(self.historyBtn)
        self.exceptionBtn = QtGui.QPushButton(self.layoutWidget)
        self.exceptionBtn.setCheckable(True)
        self.exceptionBtn.setObjectName(_fromUtf8("exceptionBtn"))
        self.horizontalLayout.addWidget(self.exceptionBtn)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.historyList = QtGui.QListWidget(self.splitter)
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Monospace"))
        self.historyList.setFont(font)
        self.historyList.setObjectName(_fromUtf8("historyList"))
        self.exceptionGroup = QtGui.QGroupBox(self.splitter)
        self.exceptionGroup.setObjectName(_fromUtf8("exceptionGroup"))
        self.gridLayout_2 = QtGui.QGridLayout(self.exceptionGroup)
        self.gridLayout_2.setSpacing(0)
        self.gridLayout_2.setContentsMargins(-1, 0, -1, 0)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.catchAllExceptionsBtn = QtGui.QPushButton(self.exceptionGroup)
        self.catchAllExceptionsBtn.setCheckable(True)
        self.catchAllExceptionsBtn.setObjectName(_fromUtf8("catchAllExceptionsBtn"))
        self.gridLayout_2.addWidget(self.catchAllExceptionsBtn, 0, 1, 1, 1)
        self.catchNextExceptionBtn = QtGui.QPushButton(self.exceptionGroup)
        self.catchNextExceptionBtn.setCheckable(True)
        self.catchNextExceptionBtn.setObjectName(_fromUtf8("catchNextExceptionBtn"))
        self.gridLayout_2.addWidget(self.catchNextExceptionBtn, 0, 0, 1, 1)
        self.onlyUncaughtCheck = QtGui.QCheckBox(self.exceptionGroup)
        self.onlyUncaughtCheck.setChecked(True)
        self.onlyUncaughtCheck.setObjectName(_fromUtf8("onlyUncaughtCheck"))
        self.gridLayout_2.addWidget(self.onlyUncaughtCheck, 0, 2, 1, 1)
        self.exceptionStackList = QtGui.QListWidget(self.exceptionGroup)
        self.exceptionStackList.setAlternatingRowColors(True)
        self.exceptionStackList.setObjectName(_fromUtf8("exceptionStackList"))
        self.gridLayout_2.addWidget(self.exceptionStackList, 2, 0, 1, 5)
        self.runSelectedFrameCheck = QtGui.QCheckBox(self.exceptionGroup)
        self.runSelectedFrameCheck.setChecked(True)
        self.runSelectedFrameCheck.setObjectName(_fromUtf8("runSelectedFrameCheck"))
        self.gridLayout_2.addWidget(self.runSelectedFrameCheck, 3, 0, 1, 5)
        self.exceptionInfoLabel = QtGui.QLabel(self.exceptionGroup)
        self.exceptionInfoLabel.setObjectName(_fromUtf8("exceptionInfoLabel"))
        self.gridLayout_2.addWidget(self.exceptionInfoLabel, 1, 0, 1, 5)
        self.clearExceptionBtn = QtGui.QPushButton(self.exceptionGroup)
        self.clearExceptionBtn.setEnabled(False)
        self.clearExceptionBtn.setObjectName(_fromUtf8("clearExceptionBtn"))
        self.gridLayout_2.addWidget(self.clearExceptionBtn, 0, 4, 1, 1)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout_2.addItem(spacerItem, 0, 3, 1, 1)
        self.gridLayout.addWidget(self.splitter, 0, 0, 1, 1)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(QtGui.QApplication.translate("Form", "Console", None, QtGui.QApplication.UnicodeUTF8))
        self.historyBtn.setText(QtGui.QApplication.translate("Form", "History..", None, QtGui.QApplication.UnicodeUTF8))
        self.exceptionBtn.setText(QtGui.QApplication.translate("Form", "Exceptions..", None, QtGui.QApplication.UnicodeUTF8))
        self.exceptionGroup.setTitle(QtGui.QApplication.translate("Form", "Exception Handling", None, QtGui.QApplication.UnicodeUTF8))
        self.catchAllExceptionsBtn.setText(QtGui.QApplication.translate("Form", "Show All Exceptions", None, QtGui.QApplication.UnicodeUTF8))
        self.catchNextExceptionBtn.setText(QtGui.QApplication.translate("Form", "Show Next Exception", None, QtGui.QApplication.UnicodeUTF8))
        self.onlyUncaughtCheck.setText(QtGui.QApplication.translate("Form", "Only Uncaught Exceptions", None, QtGui.QApplication.UnicodeUTF8))
        self.runSelectedFrameCheck.setText(QtGui.QApplication.translate("Form", "Run commands in selected stack frame", None, QtGui.QApplication.UnicodeUTF8))
        self.exceptionInfoLabel.setText(QtGui.QApplication.translate("Form", "Exception Info", None, QtGui.QApplication.UnicodeUTF8))
        self.clearExceptionBtn.setText(QtGui.QApplication.translate("Form", "Clear Exception", None, QtGui.QApplication.UnicodeUTF8))

from .CmdInput import CmdInput
