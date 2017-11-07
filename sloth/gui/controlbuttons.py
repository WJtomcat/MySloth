from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

class ControlButtonWidget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        layout = QHBoxLayout()
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignTop)
        self.back_button = QPushButton("<")
        self.forward_button = QPushButton(">")
        self.label = QLabel("<center><b></b></center>")

        layout.addWidget(self.back_button)
        layout.addWidget(self.label)
        layout.addWidget(self.forward_button)
        self.setLayout(layout)

    def setFilename(self, filename):
        self._label.setText("<center><b>%s</b></center>" % (filename,))
