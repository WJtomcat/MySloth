from urllib import request
from urllib.parse import quote
import json
from PIL import Image
import numpy as np
import hashlib
from PyQt5.QtCore import *

URL = 'http://wx.wangtiansoft.com:9090/blcj/mrtApi/'

class Network(QObject):
    caseChanged = pyqtSignal(object)
    def __init__(self):
        QObject.__init__(self)
        self.name = ''
        self.token = ''
        self._loginFlag = False
        self.caseId = ''

    def isLogin(self):
        return self._loginFlag

    def sendRequest(self, port, data):
        requestData = {}
        requestData['token'] = self.token
        requestData['data'] = data
        requestData = json.dumps(requestData)
        print(requestData)
        finalurl = '%s%s?args=%s' % (URL, port, requestData)
        print(finalurl)
        finalurl = quote(finalurl, safe='=/:?&')
        print(finalurl)
        out = request.urlopen(finalurl)
        out = out.read().decode('utf-8')
        print(out)
        return out

    def processData(self, data):
        data = json.loads(data)
        if data['status'] == 1:
            if data['message'] != '':
                print(data['message'])
            return data['data']
        else:
            print(data['status'])
            return None

    def loginDataProcess(self, data):
        out = self.sendRequest('login', data)
        out = self.processData(out)
        if out is None:
            return 0
        self.name = out['name']
        self.token = out['token']
        self._loginFlag = True
        return 1

    def downloadSuccess(self):
        data = {'dataDetailId': self.caseId}
        self.sendRequest('downloaded', data)

    def labelUpload(self, data, isSubmit=False):
        data = self.modelDeTrans(data, isSubmit)
        out = self.sendRequest('labelUpload', data)
        out = json.loads(out)
        if out['status'] == 1:
            return True
        else:
            return False

    def logOff(self):
        self.name = ''
        self.token = ''
        self._loginFlag = False

    def caseDetailDataProcess(self, data):
        out = self.sendRequest('caseDetail', data)
        out = self.processData(out)
        if out is None:
            return
        else:
            out = self.modelTrans(out)
            self.caseId = data['dataDetailId']
            return out

    def modelTrans(self, data):
        caseInfo = {}
        for key, item in data.items():
            if key != 'images':
                caseInfo[key] = item
        self.caseChanged.emit(caseInfo)
        outs = []
        print(data)
        for image in data['images']:
            out = {}
            out['class'] = 'image'
            for key, item in image.items():
                if key != 'tag':
                    out[key] = item
            out['tagId'] = image['tag']['tagId']
            list = []
            if image['tag']['tagData'] is not None:
                for tag in image['tag']['tagData']:
                    list.append(tag)
            out['annotations'] = list
            outs.append(out)
        print(outs)
        return outs

    def modelDeTrans(self, data, isSubmit):
        outs = {}
        outs['dataDetailId'] = self.caseId
        if isSubmit:
            outs['isSubmit'] = 'true'
        list = []
        for image in data:
            out = {}
            out['tagId'] = image['tagId']
            out['note'] = ''
            tmplist = []
            for i in image['annotations']:
                tmplist.append(i)
            out['tagData'] = tmplist
            list.append(out)
        outs['labels'] = list
        return outs

    def downloadPic(self, picId):
        req = {}
        req['token'] = self.token
        req['data'] = {'picId': picId}
        req = json.dumps(req)
        finalurl = '%s%s?args=%s' % (URL, 'download', req)
        finalurl = quote(finalurl, safe='=/:?&')
        print(finalurl)
        out = request.urlopen(finalurl)
        print(type(out))
        im = Image.open(out)
        md5hex = self.getmd5(out)
        print('image download success')
        return (np.asarray(im), md5hex)

    def getmd5(self, pic):
        myhash = hashlib.md5()
        while True:
            b = pic.read(8096)
            if not b:
                break
            myhash.update(b)
        hex = myhash.hexdigest()
        return hex





