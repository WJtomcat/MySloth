from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import hashlib
from urllib.request import urlopen
from PIL import Image
import numpy as np

gray_color_table = [qRgb(i, i, i) for i in range(256)]


class LoginDialog(QDialog):
    def __init__(self, network, mainwindow, parent=None):
        QDialog.__init__(self, parent)
        self.setWindowTitle('Login Dialog')
        self.label = QLabel('Please input your account and passwd')
        self.account = QLineEdit()
        self.passwd = QLineEdit()
        self.passwd.setEchoMode(QLineEdit.Password)
        self.validate = QLineEdit()
        self.validate.setEnabled(False)
        self.okButton = QPushButton('OK')
        self.cancelButton = QPushButton('Cancel')
        self.validatePic = ValidatePic(self)
        self.network = network
        self.mainwindow = mainwindow
        self.setupGui()

    def setupGui(self):
        self._layout = QFormLayout()
        self._layout.addRow(self.label)
        self._layout.addRow('account', self.account)
        self._layout.addRow('passwd', self.passwd)
        self._layout.addRow('validatecode', self.validate)
        self._layout.addRow(self.validatePic)
        self.hlayout = QHBoxLayout()
        self.hlayout.addWidget(self.okButton)
        self.hlayout.addWidget(self.cancelButton)
        self._layout.addRow(self.hlayout)
        self.setLayout(self._layout)

        self.okButton.clicked.connect(self.onOkPressed)
        self.cancelButton.clicked.connect(self.onCancelPressed)

    def onOkPressed(self):
        if str(self.account.text()) == '' or str(self.passwd.text()) == '':
            reply = QMessageBox.question(self, 'message', 'Please input Account and Passwd', QMessageBox.Ok)
            return
        if self.validate.isEnabled() and str(self.validate.text())=='':
            reply = QMessageBox.question(self,
                                         "Unsaved Changes",
                                         'Please input Validate Code',
                                         QMessageBox.Ok)
            return reply
        print(self.account.text())
        print(self.passwd.text())
        data = {}
        data['username'] = str(self.account.text())
        data['password'] = self.getMd5(self.passwd.text().encode())
        data['validateCode'] = str(self.validate.text())
        if self.network.loginDataProcess(data):
            self.mainwindow.onModelDirtyChanged(False)
            self.hide()
        else:
            self.wrongFresh()

    def wrongFresh(self):
        self.passwd.clear()
        self.validate.clear()
        self.validate.setEnabled(True)
        self.validatePic.freshValidate()

    def onCancelPressed(self):
        self.hide()

    def showDialog(self):
        self.account.clear()
        self.passwd.clear()
        self.validate.clear()
        if self.validate.isEnabled():
            self.validatePic.freshValidate()
        self.show()

    def getMd5(self, data):
        myhash = hashlib.md5()
        myhash.update(data)
        return myhash.hexdigest()

class ValidatePic(QLabel):
    def __init__(self, dialog, parent=None):
        QLabel.__init__(self, parent)
        self.dialog = dialog

    def mouseReleaseEvent(self, QMouseEvent):
        self.freshValidate()

    def freshValidate(self):
        if str(self.dialog.account.text()) == '':
            return
        pic = self.getValidatePic(str(self.dialog.account.text()))
        pic = QPixmap(toQImage(pic))
        self.setPixmap(pic)

    def getValidatePic(self, username):
        url = 'http://wx.wangtiansoft.com:9090/blcj/mrtApi/picVerifyCode?username=%s' % (username)
        print(url)
        pic = urlopen(url)
        print(pic)
        pic = Image.open(pic)
        return np.asarray(pic)


def toQImage(im, copy=False):
    if im is None:
        return QImage()

    if im.dtype == np.uint8:
        if len(im.shape) == 2:
            qim = QImage(im.data, im.shape[1], im.shape[0], im.strides[0], QImage.Format_Indexed8)
            qim.setColorTable(gray_color_table)
            return qim.copy() if copy else qim

        elif len(im.shape) == 3:
            if im.shape[2] == 3:
                qim = QImage(im.data, im.shape[1], im.shape[0], im.strides[0], QImage.Format_RGB888)
                return qim.copy() if copy else qim
            elif im.shape[2] == 4:
                qim = QImage(im.data, im.shape[1], im.shape[0], im.strides[0], QImage.Format_ARGB32)
                return qim.copy() if copy else qim

