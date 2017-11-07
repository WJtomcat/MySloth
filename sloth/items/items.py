from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from sloth.conf import config


class BaseItem(QAbstractGraphicsShapeItem):
    """
    Base class for visualization items.
    """

    cycleValuesOnKeypress = {}
    hotkeys = {}
    defaultAutoTextKeys = []

    def __init__(self, model_item=None, prefix="", parent=None):
        """
        Creates a visualization item.
        """
        QAbstractGraphicsShapeItem.__init__(self, parent)
        self.setFlags(QGraphicsItem.ItemIsSelectable |
                      QGraphicsItem.ItemIsMovable |
                      QGraphicsItem.ItemSendsGeometryChanges |
                      QGraphicsItem.ItemSendsScenePositionChanges)

        self._model_item = model_item
        if self._model_item is not None:
            self._model_item.model().dataChanged.connect(self.onDataChanged)

        # initialize members
        self._prefix = prefix
        self._auto_text_keys = self.defaultAutoTextKeys[:]
        self._text = ""
        self._text_bg_brush = None
        self._text_item = QGraphicsTextItem(self)
        self._text_item.setPos(0, 0)
        self._text_item.setAcceptHoverEvents(False)
        self._text_item.setFlags(QGraphicsItem.ItemIgnoresTransformations)
        self._text_item.setHtml(self._compile_text())
        self._valid = True

        if len(self.cycleValuesOnKeypress) > 0:
           print("cycleValueOnKeypress is deprecated and will be removed in the future. " +
                "Set BaseItem.hotkeys instead with cycleValue()")
        self.changeColor()

    def changeColor(self):
        pass

    def onDataChanged(self, indexFrom, indexTo):
        # FIXME why is this not updated, when changed graphically via attribute box ?
        #print "onDataChanged", self._model_item.index(), indexFrom, indexTo, indexFrom.parent()
        pass

    def modelItem(self):
        """
        Returns the model item of this items.
        """
        return self._model_item

    def index(self):
        """
        Returns the index of this item.
        """
        return self._model_item.index()

    def prefix(self):
        """
        Returns the key prefix of the item.
        """
        return self._prefix

    def setPen(self, pen):
        pen = QPen(pen)  # convert to pen if argument is a QColor
        QAbstractGraphicsShapeItem.setPen(self, pen)
        self._text_item.setDefaultTextColor(pen.color())

    def setText(self, text=""):
        """
        Sets a text to be displayed on this item.
        """
        self._text = text
        self._text_item.setHtml(self._compile_text())

    def text(self):
        return self._text

    def setTextBackgroundBrush(self, brush=None):
        """
        Sets the brush to be used to fill the background region
        behind the text. Set to None to not draw a background
        (leave transparent).
        """
        self._text_bg_brush = brush

    def textBackgroundBrush(self):
        """
        Returns the background brush for the text region.
        """
        return self._text_bg_brush

    def setAutoTextKeys(self, keys=None):
        """
        Sets the keys for which the values from the annotations
        are displayed automatically as text.
        """
        self._auto_text_keys = keys or []
        self._text_item.setHtml(self._compile_text())

    def autoTextKeys(self):
        """
        Returns the list of keys for which the values from
        the annotations are displayed as text automatically.
        """
        return self._auto_text_keys

    def isValid(self):
        """
        Return whether this graphics item is valid, i.e. has
        a matching, valid model item connected to it.  An item is
        by default valid, will only be set invalid on failure.
        """
        return self._valid

    def setValid(self, val):
        self._valid = val

    def _compile_text(self):
        text_lines = []
        if self._text != "" and self._text is not None:
            text_lines.append(self._text)
        for key in self._auto_text_keys:
            text_lines.append("%s: %s" % \
                    (key, self._model_item.get(key, "")))
        return '<br/>'.join(text_lines)

    def dataChanged(self):
        self.dataChange()
        self._text_item.setHtml(self._compile_text())
        self.update()

    def dataChange(self):
        pass

    def updateModel(self, ann=None):
        if ann is not None:
            self._model_item.update(ann)

    def boundingRect(self):
        return QRectF(0, 0, 0, 0)

    def setColor(self, color):
        self.setPen(color)
        self.setBrush(color)
        self.update()

    def paint(self, painter, option, widget=None):
        pass

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            self.updateModel()
        return QAbstractGraphicsShapeItem.itemChange(self, change, value)

class PolygonItem(BaseItem):

    def __init__(self, model_item=None, prefix="", parent=None):
        BaseItem.__init__(self, model_item, prefix, parent)

        # Make it non-movable for now
        self.setFlags(QGraphicsItem.ItemIsSelectable |
                      QGraphicsItem.ItemSendsGeometryChanges |
                      QGraphicsItem.ItemSendsScenePositionChanges)
        self._polygon = None
        self.setOpacity(0.6)

        self._updatePolygon(self._dataToPolygon(self._model_item))
        print("Constructed polygon %s for model item %s" %
                  (self._polygon, model_item))
        self.pos = None
        color = config.COLORMAP[model_item['class']]
        brush = QBrush(QColor(color[0], color[1], color[2], 255), Qt.SolidPattern)
        self.setBrush(brush)
        pen = QPen()
        pen.setStyle(Qt.NoPen)
        self.setPen(pen)
        self._opacity = 0.6

        # self.createMenu()

    def __call__(self, model_item=None, parent=None):
        item = PolygonItem(model_item, parent)
        item.setPen(self.pen())
        return item

    def _dataToPolygon(self, model_item):
        if model_item is None:
            return QPolygonF()

        try:
            polygon = QPolygonF()
            xn = [float(x) for x in model_item["xn"].split(";")]
            yn = [float(y) for y in model_item["yn"].split(";")]
            for x, y in zip(xn, yn):
                polygon.append(QPointF(x, y))
            return polygon

        except KeyError as e:
            print("PolygonItem: Could not find expected key in item: "
                      + str(e) + ". Check your config!")
            self.setValid(False)
            return QPolygonF()

    def dataTo(self, name):
        if self._model_item is None:
            return ''
        try:
            note = self._model_item[name]
            return note
        except KeyError as e:
            print("PolygonItem: Could not find expected key in item: "
                      + str(e) + ". Check your config!")
            return ''

    def dataToIndex(self):
        if self._model_item is None:
            return 0
        try:
            index = self._model_item['combo']
            return index
        except KeyError as e:
            print("PolygonItem: Could not find expected key in item: "
                      + str(e) + ". Check your config!")
            return 0

    def _updatePolygon(self, polygon):
        if polygon == self._polygon:
            return

        self.prepareGeometryChange()
        self._polygon = polygon
        self.setPos(QPointF(0, 0))

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemMatrixChange:
            self.updateModel()
        return QAbstractGraphicsShapeItem.itemChange(self, change, value)

    def updateModel(self):
        xn = [str(p.x()) for p in self._polygon]
        yn = [str(p.y()) for p in self._polygon]
        strx = ';'.join(xn)
        stry = ';'.join(yn)
        self._model_item.update({
            self.prefix() + 'xn': strx,
            self.prefix() + 'yn': stry
        })

    def updateTo(self, key, data):
        self._model_item.update({
            self.prefix() + key: data
        })

    def boundingRect(self):
        xn = [p.x() for p in self._polygon]
        yn = [p.y() for p in self._polygon]
        xmin = min(xn)
        xmax = max(xn)
        ymin = min(yn)
        ymax = max(yn)
        return QRectF(xmin, ymin, xmax - xmin, ymax - ymin)

    def paint(self, painter, option, widget=None):
        pen = self.pen()
        if self.isSelected():
            if self._opacity >= 0.8 :
                self.setOpacity(1)
            else:
                self.setOpacity(self._opacity + 0.2)
        else:
            self.setOpacity(self._opacity)
        pen.setStyle(Qt.NoPen)
        painter.setPen(pen)
        painter.setBrush(self.brush())
        painter.drawPolygon(self._polygon)


    def dataChange(self):
        polygon = self._dataToPolygon(self._model_item)
        self._updatePolygon(polygon)

    def subtract(self, other):
        newpolygon = self._polygon.subtracted(other)
        if newpolygon == self._polygon:
            return
        self._updatePolygon(newpolygon)
        self.updateModel()

    def opaqueChanged(self, value):
        self._opacity = value
        self.update()

    # def contextMenuEvent(self, event):
    #     self.menu.exec_(QCursor.pos())
    #
    # def createMenu(self):
    #     self.menu = QMenu();
    #     self.actionGroup = QActionGroup(self.menu)
    #     for i in config.LABELS:
    #         itemclass = i['attributes']['class']
    #         if itemclass != 'Eraser':
    #             action = self.menu.addAction(itemclass)
    #         self.actionGroup.addAction(action)
    #     self.actionGroup.triggered.connect(self.onMenuAction)

    # @pyqtSlot()
    # def onMenuAction(self, action):
    #     self._model_item.update({
    #         self.prefix() + 'class': str(action.text()),
    #     })
    #     color = config.COLORMAP[self._model_item['class']]
    #     brush = QBrush(QColor(color[0], color[1], color[2], 255), Qt.SolidPattern)
    #     self.setBrush(brush)

