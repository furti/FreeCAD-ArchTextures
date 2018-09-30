IS_QT_5 = False

if IS_QT_5:
    from PySide2 import QtGui, QtCore, QtWidgets
    IS_QT_5 = True
else:
    from PySide import QtGui, QtCore
    import PySide.QtGui as QtWidgets

import time

def showInfo(title, message):
    QtWidgets.QMessageBox.information(activeWindow(), title, message)
