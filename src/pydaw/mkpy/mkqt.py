if True:
    from PyQt5 import QtGui, QtWidgets, QtCore
    from PyQt5.QtCore import pyqtSignal as Signal, pyqtSlot as Slot
    from PyQt5.QtGui import *
    from PyQt5.QtWidgets import *
else:
    from PySide2 import QtGui, QtWidgets, QtCore
    from PySide2.QtCore import Signal, Slot
    from PySide2.QtGui import *
    from PySide2.QtWidgets import *
