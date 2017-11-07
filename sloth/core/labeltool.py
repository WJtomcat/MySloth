from PyQt5.QtGui import *
from PyQt5.QtCore import *
from sloth.gui.labeltool import MainWindow

class LabelTool(QObject):
    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        self._mainwindow = MainWindow(self)
        self._mainwindow.show()
