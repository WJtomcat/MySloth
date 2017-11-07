from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

class GraphicsView(QGraphicsView):

    def __init__(self, parent=None):
        QGraphicsView.__init__(self, parent)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setMouseTracking(True)
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform | QPainter.TextAntialiasing)
        self.setStyleSheet("QFrame { border: 3px solid black }")

        self._pan = False
        self._panStartX = -1
        self._panStartY = -1
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.ScrollHandDrag)

    def fitInView(self, *__args):
        if self.scene() is None:
            return
        si = self.scene().sceneItem()
        if si is None:
            return

        old_scale = self.getScale()
        QGraphicsView.fitInView(self, si, Qt.KeepAspectRatio)
        new_scale = self.getScale()

        if new_scale != old_scale:
            self.scaleChanged.emit(new_scale)


    def getScale(self):
        if self.isTransformed():
            return self.transform().m11()
        else:
            return 1

    def getMinScale(self):
        return 0.1

    def getMaxScale(self):
        return 20.0

    def setScaleAbsolute(self, scale):
        scale = max(scale, self.getMinScale())
        scale = min(scale, self.getMaxScale())
        self.setTransform(QTransform.fromScale(scale, scale))

    def setScaleRelative(self, factor):
        self.setScaleAbsolute(self.getScale() * factor)

    def wheelEvent(self, QWheelEvent):
        factor = 1.41 ** (QWheelEvent.angleDelta().y()/ 240.0)
        self.setScaleRelative(factor)

    def focusInEvent(self, QFocusEvent):
        print('focusInEvent')

    def mousePressEvent(self, event):
        if event.button() & Qt.MidButton != 0:
            self._pan = True
            self._panStartX = event.x()
            self._panStartY = event.y()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
        else:
            return QGraphicsView.mousePressEvent(self, event)

    def mouseReleaseEvent(self, event):
        if self._pan:
            self._pan = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
        else:
            return QGraphicsView.mouseReleaseEvent(self, event)

    def mouseMoveEvent(self, event):
        if self._pan:
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - (event.x() - self._panStartX))
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - (event.y() - self._panStartY))
            self._panStartX = event.x()
            self._panStartY = event.y()
            event.accept()
        else:
            return QGraphicsView.mouseMoveEvent(self, event)
