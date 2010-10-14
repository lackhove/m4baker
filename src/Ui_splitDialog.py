# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/kilian/Dokumente/coding/M4Baker/m4baker-0.2d/m4baker/splitDialog.ui'
#
# Created: Sun Sep  5 01:36:24 2010
#      by: PyQt4 UI code generator 4.7.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_splitDialog(object):
    def setupUi(self, splitDialog):
        splitDialog.setObjectName("splitDialog")
        splitDialog.resize(366, 86)
        self.verticalLayout = QtGui.QVBoxLayout(splitDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtGui.QLabel(splitDialog)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.splitTimeEdit = QtGui.QTimeEdit(splitDialog)
        self.splitTimeEdit.setEnabled(True)
        self.splitTimeEdit.setMaximumTime(QtCore.QTime(13, 0, 0))
        self.splitTimeEdit.setTime(QtCore.QTime(1, 2, 3))
        self.splitTimeEdit.setObjectName("splitTimeEdit")
        self.verticalLayout.addWidget(self.splitTimeEdit)
        self.buttonBox = QtGui.QDialogButtonBox(splitDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(splitDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), splitDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), splitDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(splitDialog)

    def retranslateUi(self, splitDialog):
        splitDialog.setWindowTitle(QtGui.QApplication.translate("splitDialog", "split audiobook", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("splitDialog", "Split audiobook into pieces of max hh:mm:ss", None, QtGui.QApplication.UnicodeUTF8))
        self.splitTimeEdit.setDisplayFormat(QtGui.QApplication.translate("splitDialog", "HH:mm:ss", None, QtGui.QApplication.UnicodeUTF8))


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    splitDialog = QtGui.QDialog()
    ui = Ui_splitDialog()
    ui.setupUi(splitDialog)
    splitDialog.show()
    sys.exit(app.exec_())

