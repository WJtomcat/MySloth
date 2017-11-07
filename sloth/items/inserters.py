from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from sloth.conf import config


class ItemInserter(QObject):
    """
    The base class for all item insertion handlers.
    """
    # Signals
    annotationFinished = pyqtSignal()
    inserterFinished = pyqtSignal()

    def __init__(self, labeltool, scene, default_properties=None,
                 prefix="", commit=True):
        QObject.__init__(self)
        self._labeltool = labeltool
        self._scene = scene
        self._default_properties = default_properties or {}
        self._prefix = prefix
        self._ann = {}
        self._commit = commit
        self._item = None
        self._pen = Qt.red

    def annotation(self):
        return self._ann

    def item(self):
        return self._item

    def pen(self):
        return self._pen

    def setPen(self, pen):
        self._pen = pen

    def mousePressEvent(self, event, image_item):
        event.accept()

    def mouseDoubleClickEvent(self, event, image_item):
        event.accept()

    def mouseReleaseEvent(self, event, image_item):
        event.accept()

    def mouseMoveEvent(self, event, image_item):
        event.accept()

    def keyPressEvent(self, event, image_item):
        event.ignore()

    def imageChange(self):
        """
        Slot which gets called if the current image in the labeltool changes.
        """
        pass

    def allowOutOfSceneEvents(self):
        return False

    def abort(self):
        self.inserterFinished.emit()


class PolylineItemInserter(ItemInserter):
    def __init__(self, labeltool, scene, default_properties=None, prefix="", commit=True):
        ItemInserter.__init__(self, labeltool, scene, default_properties,
                                prefix, commit)
        self._item = None
        pen = QPen()
        pen.setColor(Qt.red)
        pen.setWidth(1)
        self.setPen(pen)

    def _removeLastPointAndFinish(self, image_item):
        polygon = self._item.polygon()
        polygon.remove(polygon.size()-1)
        assert polygon.size() > 0
        self._item.setPolygon(polygon)

        self._updateAnnotation()
        if self._commit:
            image_item.addAnnotation(self._ann)
        self._scene.removeItem(self._item)
        self.annotationFinished.emit()
        self._item = None
        self._scene.clearMessage()
        self.inserterFinished.emit()

    def mousePressEvent(self, event, image_item):
        pos = event.scenePos()

        if self._item is None:
            item = PolylineItem(QPolygonF([pos]))
            self._item = item
            self._item.setPen(self.pen())
            self._scene.addItem(item)

            self._scene.setMessage("Press Enter to finish the polygon.")

        polygon = self._item.polygon()
        polygon.append(pos)
        self._item.setPolygon(polygon)

        event.accept()

    def mouseDoubleClickEvent(self, event, image_item):

        self._removeLastPointAndFinish(image_item)

        event.accept()

    def allowOutOfSceneEvents(self):
        return True


    def mouseMoveEvent(self, event, image_item):
        if self._item is not None:
            pos = event.scenePos()
            polygon = self._item.polygon()
            assert polygon.size() > 0
            polygon[-1] = pos
            self._item.setPolygon(polygon)

        event.accept()

    def keyPressEvent(self, event, image_item):
        """
        When the user presses Enter, the polygon is finished.
        """
        if event.key() == Qt.Key_Return and self._item is not None:
            # The last point of the polygon is the point the user would add
            # to the polygon when pressing the mouse button. At this point,
            # we want to throw it away.
            self._removeLastPointAndFinish(image_item)

    def abort(self):
        if self._item is not None:
            self._scene.removeItem(self._item)
            self._item = None
            self._scene.clearMessage()
        ItemInserter.abort(self)

    def _updateAnnotation(self):
        polygon = self._item.polygon()
        self._ann.update({self._prefix + 'xn':
                              ";".join([str(p.x()) for p in polygon]),
                          self._prefix + 'yn':
                              ";".join([str(p.y()) for p in polygon])})
        self._ann.update(self._default_properties)

    def onScaleChanged(self, scale):
        if self._item is not None:
            self._item.onScaleChanged(scale)

class FreehandItemInserter(PolylineItemInserter):
    def __init__(self, labeltool, scene, default_properties=None,
                 prefix="", commit=True):
        PolylineItemInserter.__init__(self, labeltool, scene, default_properties,
                              prefix, commit)
        self.start = False
        self.pressflag = False
        self.num = 0
        self.pos = None
        self.initpos = None
        self.scale = None

    def setColorMap(self, label_class):
        color = config.COLORMAP[str(label_class)]
        pen = self.pen()
        pen.setColor(QColor(color[0], color[1], color[2], 255))
        self.setPen(pen)

    def setScale(self, scale):
        self.scale = scale

    def onScaleChanged(self, scale):
        self.setScale(scale)
        if self._item is not None:
            self._item.scaleChanged(scale)

    def mousePressEvent(self, event, image_item):
        if event.button() != Qt.LeftButton:
            event.accept()
            return
        pos = event.scenePos()
        self.pressflag = True
        if self._item is None:
            item = FreePolylineItem(QPolygonF([pos]))
            item.setPen(self.pen())
            self.start = True
            self.pos = pos
            self._item = item
            self._item.setendSelected(True)
            self._scene.addItem(self._item)
            event.accept()
            return

        polygon = self._item.polygon()
        if self._item.endIsSelected():
            if self._item.initregion().contains(pos):
                self._removeLastPointAndFinish(image_item)
                event.accept()
                return
            else:
                polygon.append(pos)
                self._item.setPolygon(polygon)
                self._item.update()
        elif self._item.initIsSelected():
            if self._item.endregion().contains(pos):
                self._removeLastPointAndFinish(image_item)
                event.accept()
                return
            else:
                polygon.insert(0, pos)
                self._item.setPolygon(polygon)
                self._item.update()

        else:
            if self._item.initregion().contains(pos):
                self.initpos = pos
                self._item.setinitSelected(True)
                self._item.update()
                event.accept()
                return
            elif self._item.endregion().contains(pos):
                self.initpos = pos
                self._item.setendSelected(True)
                self._item.update()
                event.accept()
                return
        event.accept()


    def mouseMoveEvent(self, event, image_item):
        if self._item is None:
            return
        if not self.pressflag:
            event.accept()
            return
        pos = event.scenePos()
        x = pos.x() - self.pos.x()
        y = pos.y() - self.pos.y()
        out = abs(x) + abs(y)
        if out < 3:
            event.accept()
            return
        self.pos = pos
        polygon = self._item.polygon()
        if self._item.endIsSelected():
            if self.pressflag:
                polygon.append(pos)
        elif self._item.initIsSelected():
            if self.pressflag:
                polygon.insert(0, pos)
        else:
            return
        self._item.setPolygon(polygon)
        self._item.update()
        event.accept()

    def mouseDoubleClickEvent(self, event, image_item):
        """Finish the polygon when the user double clicks."""
        # No need to add the position of the click, as a single mouse
        # press event added the point already.
        # Even then, the last point of the polygon is duplicate as it would be
        # shortly after a single mouse press. At this point, we want to throw it
        # away.
        self._removeLastPointAndFinish(image_item)
        event.accept()

    def keyPressEvent(self, event, image_item):
        """
        When the user presses Enter, the polygon is finished.
        """
        if event.key() == Qt.Key_Return and self._item is not None:
            # The last point of the polygon is the point the user would add
            # to the polygon when pressing the mouse button. At this point,
            # we want to throw it away.
            self._removeLastPointAndFinish(image_item)

    def mouseReleaseEvent(self, event, image_item):
        if self._item is None:
            event.accept()
            return
        pos = event.scenePos()
        if (self._item.initIsSelected() or self._item.endIsSelected()) and event.button() == Qt.LeftButton:
            if pos == self.initpos:
                event.accept()
                self.initpos = None
                self.pressflag = False
                self._item.update()
                return
        self.pressflag = False
        self._item.setinitSelected(False)
        self._item.setendSelected(False)
        self._item.update()
        event.accept()

    def abort(self):
        if self._item is not None:
            self._scene.removeItem(self._item)
            self._item = None
            self._scene.clearMessage()
        ItemInserter.abort(self)

    def _removeLastPointAndFinish(self, image_item):
        if self._item is None:
            self.inserterFinished.emit()
            return
        polygon = self._item.polygon()
        assert polygon.size() > 0
        self._updateAnnotation()
        if self._commit:
            image_item.addAnnotation(self._ann)
        self._scene.removeItem(self._item)
        self.annotationFinished.emit()
        self._item = None
        self.inserterFinished.emit()

class FreehandEraser(FreehandItemInserter):
    def _removeLastPointAndFinish(self, image_item):
            polygon = self._item.polygon()
            assert polygon.size() > 0
            self._scene.removeItem(self._item)
            self._item = None

            itemlist = self._scene.items()
            for item in itemlist:
                if hasattr(item, 'subtract'):
                    item.subtract(polygon)
            self.inserterFinished.emit()

class PolylineItem(QAbstractGraphicsShapeItem):

    def __init__(self, polygon):
        QAbstractGraphicsShapeItem.__init__(self)
        self._polygon = polygon

    def paint(self, painter, option, widget = None):
        pen = self.pen()
        painter.setPen(pen)
        painter.drawPolyline(self._polygon)

    def polygon(self):
        return self._polygon

    def setPolygon(self, polygon):
        self._polygon = polygon

    def boundingRect(self):
        xn = [p.x() for p in self._polygon]
        yn = [p.y() for p in self._polygon]
        xmin = min(xn)
        xmax = max(xn)
        ymin = min(yn)
        ymax = max(yn)
        return QRectF(xmin, ymin, xmax - xmin, ymax - ymin)

    def scaleChanged(self, scale):
        pass

class FreePolylineItem(QAbstractGraphicsShapeItem):

    def __init__(self, polygon):
        QAbstractGraphicsShapeItem.__init__(self)
        self._polygon = polygon
        self._initpoint = polygon[0]
        self._endpoint = polygon[-1]
        self._dynamic = False
        self._endSelected = False
        self._initSelected = False
        self.setFlags(QGraphicsItem.ItemIsSelectable |
                      QGraphicsItem.ItemSendsScenePositionChanges)
        # pen = QPen()
        # pen.setColor(Qt.yellow)
        # pen.setStyle(Qt.DashLine)
        # self.setPen(pen)
        self.circleR = 4.0

        # self.setCacheMode(2)

    def paint(self, painter, option, widget = None):
        pen = self.pen()
        painter.setPen(pen)
        painter.drawPolyline(self._polygon)

        if self._initSelected:
            pen.setColor(Qt.green)
        else:
            pen.setColor(Qt.yellow)
        painter.setPen(pen)
        painter.drawEllipse(self._initpoint, self.circleR, self.circleR)
        if self._endSelected:
            pen.setColor(Qt.green)
        else:
            pen.setColor(Qt.yellow)
        painter.setPen(pen)
        painter.drawEllipse(self._endpoint, self.circleR, self.circleR)

    def endregion(self):
        return QRectF(self._endpoint.x()-2*self.circleR, self._endpoint.y()-2*self.circleR, 4*self.circleR, 4*self.circleR)

    def initregion(self):
        return QRectF(self._initpoint.x()-2*self.circleR, self._initpoint.y()-2*self.circleR, 4*self.circleR, 4*self.circleR)

    def setinitSelected(self, state):
        if state:
            self._initSelected = True
            self._endSelected = False
        else:
            self._initSelected = False

    def setendSelected(self, state):
        if state:
            self._endSelected = True
            self._initSelected = False
        else:
            self._endSelected = False

    def initIsSelected(self):
        return self._initSelected

    def endIsSelected(self):
        return self._endSelected

    def polygon(self):
        return self._polygon

    def setPolygon(self, polygon):
        self._polygon = polygon
        self._initpoint = polygon[0]
        self._endpoint = polygon[-1]

    def boundingRect(self):
        xn = [p.x() for p in self._polygon]
        yn = [p.y() for p in self._polygon]
        xmin = min(xn)
        xmax = max(xn)
        ymin = min(yn)
        ymax = max(yn)
        return QRectF(xmin-3, ymin-3, xmax - xmin + 6, ymax - ymin + 6)

