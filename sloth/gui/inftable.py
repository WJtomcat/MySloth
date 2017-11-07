from PyQt5.QtWidgets import *
import json

class CaseInformationWidget(QWidget):
    def __init__(self, tool, parent=None):
        QWidget.__init__(self, parent)
        self.caseInf = QTextEdit()
        self.caseInf.setEnabled(False)
        self.imageInf = QTextEdit()
        self.imageInf.setEnabled(False)
        self.tool = tool
        self.setupGui()

    def setupGui(self):
        self.casebox = QGroupBox('Case')
        self.case_layout = QVBoxLayout()
        self.case_layout.addWidget(self.caseInf)
        self.casebox.setLayout(self.case_layout)

        self.imagebox = QGroupBox('Image')
        self.image_layout = QVBoxLayout()
        self.image_layout.addWidget(self.imageInf)
        self.imagebox.setLayout(self.image_layout)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.casebox)
        self.layout.addWidget(self.imagebox)
        self.setLayout(self.layout)

    def onCaseChanged(self, caseinf):
        if caseinf is None:
            self.caseInf.clear()
            return
        ann = ''
        for key, item in caseinf.items():
            tmp = str(key) + ':' + str(item) + '\n'
            ann = ann+tmp
        self.caseInf.setText(ann)


    def onImageChanged(self, image):
        if image is None:
            self.imageInf.clear()
            return
        ann = ''
        items = image.getAnnotations()
        keys = ['picName', 'picId', 'picTypeName', 'picExplain']
        for i in keys:
            tmp = i + ':' + str(items[i]) + '\n'
            ann = ann+tmp
        self.imageInf.setText(ann)


