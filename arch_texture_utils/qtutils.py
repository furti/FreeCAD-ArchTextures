IS_QT_5 = False

if IS_QT_5:
    from PySide2 import QtGui, QtCore, QtWidgets
    IS_QT_5 = True
else:
    from PySide import QtGui, QtCore
    import PySide.QtGui as QtWidgets

import time

# common used classes
QComboBox = QtWidgets.QComboBox
QTableWidgetItem = QtWidgets.QTableWidgetItem
QDoubleSpinBox = QtWidgets.QDoubleSpinBox
QDialogButtonBox = QtWidgets.QDialogButtonBox

# File patterns
IMAGE_FILES = "Image Files (*.png *.jpg *.bmp *.tif)"
JSON_FILES = "JSON Files (*.json)"

# methods
def activeWindow():
    return QtWidgets.QApplication.activeWindow()

def showInfo(title, message):
    QtWidgets.QMessageBox.information(activeWindow(), title, message)

def userSelectedFile(title, filePattern, mustExist=True):
    if mustExist:
        fileName = QtWidgets.QFileDialog.getOpenFileName(activeWindow(), title, '', filePattern)[0]
    else:
        fileName = QtWidgets.QFileDialog.getSaveFileName(activeWindow(), caption=title, filter=filePattern)[0]

    if fileName == '':
        return None

    return fileName