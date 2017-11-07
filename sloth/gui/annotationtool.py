from PyQt5.QtCore import *
from sloth.annotations.model import *
from threading import Thread
import hashlib


class AnnotationTool(QObject):

    annotationsLoaded = pyqtSignal()
    currentImageChanged = pyqtSignal()
    def __init__(self, mainwindow, network):
        QObject.__init__(self)
        self._model = AnnotationModel([])
        self._mainwindow = mainwindow
        self._currentImage = None
        self.network = self._mainwindow.network
        self.images = []

    def model(self):
        return self._model

    def propertyEditor(self):
        return self._mainwindow.propertyEditor

    def exitInsertMode(self):
        if self._mainwindow is not None:
            return self._mainwindow.propertyEditor.endInsertionMode()

    def selectAllAnnotations(self):
        if self._mainwindow is not None:
            return self._mainwindow.scene.selectAllItems()

    def deleteSelectedAnnotations(self):
        if self._mainwindow is not None:
            self._mainwindow.scene.deleteSelectedItems()


    def loadAnnotations(self, ann, handleErrors=True):
        try:
            self._model = AnnotationModel(ann)
        except Exception as e:
            if handleErrors:
                print("Error: Loading failed (%s)" % str(e))
            else:
                raise
        self.annotationsLoaded.emit()
        self.loadImage()

    def loadImage(self):
        for item in self._model.iterator(ImageFileModelItem):
            image = ImageThread(item, self.network)
            image.start()
            image.imageLoaded.connect(self.onImageLoaded)
            self.images.append(image)

    def onImageLoaded(self):
        self._mainwindow.treeview.update()
        for image in self.images:
            if not image.isLoaded():
                return
        self.network.downloadSuccess()

    def currentImage(self):
        return self._currentImage

    def setCurrentImage(self, image):
        print('setcurrentimage')
        print(type(image))
        if isinstance(image, QModelIndex):
            image = self._model.itemFromIndex(image)
        if isinstance(image, RootModelItem):
            return
        while (image is not None) and (not isinstance(image, ImageFileModelItem)):
            image = image.parent()
        if image is None:
            raise RuntimeError("Tried to set current image to item that has no Image or Frame as parent!")
        if image != self._currentImage:
            self._currentImage = image
            print('setcurrentimage emit')
            self.currentImageChanged.emit()
        else:
            print('budui a')

    def getImage(self, item):
        for image in self.images:
            if image.picId == item['picId']:
                return image

    def annotations(self):
        if self._model is None:
            return None
        return self._model.root().getAnnotations()

    def clearAnnotations(self):
        self._model = AnnotationModel([])
        self.annotationsLoaded.emit()

    def gotoNext(self):
        print('gotonext')
        step = 1
        if self._model is not None:
            if self._currentImage is not None:
                next_image = self._currentImage.getNextSibling(step)
            else:
                next_image = next(self._model.iterator(ImageFileModelItem))
            if next_image is not None:
                self.setCurrentImage(next_image)

    def gotoPrevious(self):
        print('gotoprevious')
        step = 1
        if self._model is not None and self._currentImage is not None:
            prev_image = self._currentImage.getPreviousSibling(step)
            if prev_image is not None:
                self.setCurrentImage(prev_image)

    def gotoIndex(self, index):
        if self._model is None:
            return

        current = self._currentImage
        if current is None:
            current = next(self._model.iterator(ImageFileModelItem))

        next_image = current.getSibling(index)
        if next_image is not None:
            self.setCurrentImage(next_image)

class ImageThread(Thread, QObject):
    imageLoaded = pyqtSignal()
    def __init__(self, image, network):
        Thread.__init__(self)
        QObject.__init__(self)
        self.image = image
        self.picId = image['picId']
        self.network = network
        self._isLoaded = False
        self.pic = None
        self.wrongFlag = 0

    def getImage(self):
        return self.pic

    # def md5Validate(self, pic):
    #     myhash = hashlib.md5
    #     while True:
    #         b = pic.read(8096)
    #         if not b:
    #             break
    #         myhash.update(b)
    #     hex = myhash.hexdigest()
    #     return hex == self.image['md5']

    def run(self):
        print('start download', self.picId)
        (pic, hex) = self.network.downloadPic(self.picId)
        while True:
            if hex == 0:
                self.pic = pic
                self._isLoaded = True
                self.imageLoaded.emit()
                self.image.setSeen()
                print('download done', self.picId)
                return
            else:
                print('pic wrong')
                self.wrongFlag += 1
                if self.wrongFlag >= 3:
                    return

    def run(self):
        self.wrongFlag = 0
        while True:
            (pic, hex) = self.network.downloadPic(self.picId)
            if True:
                print(hex)
                print(self.image['md5'])
                self.pic = pic
                self._isLoaded = True
                self.imageLoaded.emit()
                self.image.setSeen()
                return
            else:
                self.wrongFlag += 1
                if self.wrongFlag >= 3:
                    return


    def isLoaded(self):
        return self._isLoaded

