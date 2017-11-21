from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from types import *
from sloth.conf import config

dataSetId = config.DATASETID

class CaseListDialog(QDialog):
    def __init__(self, network, tool, parent=None):
        QDialog.__init__(self, parent)
        self.network = network
        self.tool = tool
        self.list = QTableView()
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        self.list.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.list.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list.verticalHeader().setVisible(True)
        self.list.horizontalHeader().setVisible(True)
        self.list.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderItem(0, QStandardItem('dataDetailId'))
        self.model.setHorizontalHeaderItem(1, QStandardItem('recordNo'))
        self.model.setHorizontalHeaderItem(2, QStandardItem('source'))
        self.model.setHorizontalHeaderItem(3, QStandardItem('addTime'))
        self.list.setModel(self.model)

        self.buttonBox = QDialogButtonBox()
        self.preButton = QPushButton('<')
        self.nextButton = QPushButton('>')
        self.okButton = QPushButton('OK')
        self.cancelButton = QPushButton('Cancel')
        self.setupGui()
        self.page = 1

    def setupGui(self):
        self._layout = QVBoxLayout()
        self._layout.addWidget(self.list)

        self.buttonBox.addButton(self.preButton, QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.nextButton, QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.okButton, QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.cancelButton, QDialogButtonBox.ActionRole)

        self.preButton.clicked.connect(self.onPreButton)
        self.nextButton.clicked.connect(self.onNextButton)
        self.okButton.clicked.connect(self.onOkButton)
        self.cancelButton.clicked.connect(self.onCancelButton)

        self._layout.addWidget(self.buttonBox)
        self.setLayout(self._layout)

    def loadData(self, data):
        key = ['dataDetailId', 'recordNo', 'source', 'addTime']
        list = []
        for i in key:
            item = data[i]
            if type(item) is int:
                item = str(item)
            item = QStandardItem(item)
            list.append(item)
        self.model.appendRow(list)

    def onPreButton(self):
        if self.page > 1:
            self.page = self.page - 1
            self.getData(currentPage=self.page)

    def onNextButton(self):
        self.page = self.page + 1
        self.getData(currentPage=self.page)

    def onOkButton(self):
        indexlist = self.list.selectedIndexes()
        data = self.model.data(indexlist[0])
        print(data)
        data = {'dataDetailId': int(data)}
        model = self.network.caseDetailDataProcess(data)
        self.tool.loadAnnotations(model)
        self.hide()

    def onCancelButton(self):
        self.hide()

    def getData(self, currentPage=1, pageSize=20):
        data = {}
        data['pageSize'] = pageSize
        data['currentPage'] = currentPage
        data['dataSetId'] = dataSetId
        out = self.network.sendRequest('caseList', data)
        out = self.network.processData(out)
        self.model.clear()
        if out is None:
            return
        else:
            items = out['items']
            for i in items:
                self.loadData(i)
