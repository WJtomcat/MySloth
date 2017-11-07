from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from sloth.gui.logindl import toQImage
from sloth.annotations.model import *
from sloth.items import *

class AnnotationScene(QGraphicsScene):

    def __init__(self, tool, inserters=inserters, items=items, parent=None):
        super(AnnotationScene, self).__init__(parent)
        self._model = None
        self._image_item = None
        self.tool = tool
        self._itemFactory = Factory(items)
        self._inserterFactory = Factory(inserters)
        self._inserter =None
        self.reset()

    def setModel(self, model):
        if model == self._model:
            # same model as the current one
            # reset caches anyway, invalidate root
            self.reset()
            return
        # disconnect old signals
        if self._model is not None:
            self._model.dataChanged.disconnect(self.dataChanged)
            self._model.rowsInserted.disconnect(self.rowsInserted)
            self._model.rowsAboutToBeRemoved.disconnect(self.rowsAboutToBeRemoved)
            self._model.modelReset.disconnect(self.reset)
        self._model = model
        # connect new signals
        if self._model is not None:
            self._model.dataChanged.connect(self.dataChanged)
            self._model.rowsInserted.connect(self.rowsInserted)
            self._model.rowsAboutToBeRemoved.connect(self.rowsAboutToBeRemoved)
            self._model.modelReset.connect(self.reset)
        # reset caches, invalidate root
        self.reset()

    def sceneItem(self):
        return self._scene_item

    def setCurrentImage(self, current_image=None):
        if current_image == self._image_item:
            return
        if current_image is None:
            self.clear()
            self._image_item = None
            self._image = None
            self._pixmap = None
        else:
            self.clear()
            self._image_item = current_image
            image = self.tool.getImage(current_image)
            if image.isLoaded():
                self._image = image.getImage()
                self._opaque = 0.6
                self._image_item._sceen = True
                self._pixmap = QPixmap(toQImage(self._image))
                self._scene_item = QGraphicsPixmapItem(self._pixmap)
                self._scene_item.setZValue(-1)
                self.setSceneRect(0, 0, self._pixmap.width(), self._pixmap.height())
                self.addItem(self._scene_item)
                self.insertItems(0, len(self._image_item.children()) - 1)
                self.update()
            else:
                image.imageLoaded.connect(self.waitForImage)

    def waitForImage(self):
        image = self.tool.getImage(self._image_item)
        image.imageLoaded.disconnect(self.waitForImage)
        self._image = image.getImage()
        self._opaque = 0.6
        self._image_item._sceen = True
        self._pixmap = QPixmap(toQImage(self._image))
        self._scene_item = QGraphicsPixmapItem(self._pixmap)
        self._scene_item.setZValue(-1)
        self.setSceneRect(0, 0, self._pixmap.width(), self._pixmap.height())
        self.addItem(self._scene_item)
        self.insertItems(0, len(self._image_item.children()) - 1)
        self.update()

    def insertItems(self, first, last):
        if self._image_item is None:
            return

        assert self._model is not None

        # create a graphics item for each model index
        for row in range(first, last + 1):
            child = self._image_item.childAt(row)
            if not isinstance(child, AnnotationModelItem):
                continue
            try:
                label_class = child['class']
            except KeyError:
                print('keyerror there is no class key item')
                continue
            item = self._itemFactory.create(label_class, child)
            if item is not None:
                self.addItem(item)
            else:
                continue

    def deleteSelectedItems(self):
        modelitems_to_delete = dict((id(item.modelItem()), item.modelItem()) for item in self.selectedItems())
        for item in modelitems_to_delete.values():
            item.delete()

    def reset(self):
        self.clear()
        self.setCurrentImage()

    def clear(self):
        for item in self.items():
            if item.parentItem() is None:
                self.removeItem(item)
        self._scene_item = None

    def onInsertionModeStarted(self, label_class):
        if self._inserter is not None:
            self._inserter.abort()

        self.deselectAllItems()

        # Add new inserter
        default_properties = self.tool.propertyEditor().currentEditorProperties()
        inserter = self._inserterFactory.create(label_class, self.tool, self, default_properties)
        if inserter is None:
            raise Exception
        inserter.inserterFinished.connect(self.onInserterFinished)
        self.tool.currentImageChanged.connect(inserter.imageChange)
        self._inserter = inserter
        # Change cursor to cross
        self.views()[0].viewport().setCursor(Qt.CrossCursor)

    def onInsertionModeEnded(self):
        if self._inserter is not None:
            self._inserter.abort()
        self.views()[0].viewport().setCursor(Qt.ArrowCursor)

    def onInserterFinished(self):
        self.sender().inserterFinished.disconnect(self.onInserterFinished)
        self.tool.currentImageChanged.disconnect(self.sender().imageChange)
        self.tool.exitInsertMode()
        self._inserter = None

    def mousePressEvent(self, event):
        if self._inserter is not None:
            if not self.sceneRect().contains(event.scenePos()) and \
                    not self._inserter.allowOutOfSceneEvents():
                # ignore events outside the scene rect
                return
            # insert mode
            self._inserter.mousePressEvent(event, self._image_item)
        else:
            # selection mode
            QGraphicsScene.mousePressEvent(self, event)

    def mouseDoubleClickEvent(self, event):
        if self._inserter is not None:
            if not self.sceneRect().contains(event.scenePos()) and \
                    not self._inserter.allowOutOfSceneEvents():
                # ignore events outside the scene rect
                return
            # insert mode
            self._inserter.mouseDoubleClickEvent(event, self._image_item)
        else:
            # selection mode
            QGraphicsScene.mouseDoubleClickEvent(self, event)

    def mouseReleaseEvent(self, event):
        if self._inserter is not None:
            # insert mode
            self._inserter.mouseReleaseEvent(event, self._image_item)
        else:
            # selection mode
            QGraphicsScene.mouseReleaseEvent(self, event)

    def mouseMoveEvent(self, event):
        sp = event.scenePos()
        # self.mousePositionChanged.emit(sp.x(), sp.y())
        # LOG.debug("mouseMoveEvent %s %s" % (self.sceneRect().contains(event.scenePos()), event.scenePos()))
        if self._inserter is not None:
            # insert mode
            self._inserter.mouseMoveEvent(event, self._image_item)
        else:
            # selection mode
            QGraphicsScene.mouseMoveEvent(self, event)

    def deselectAllItems(self):
        for item in self.items():
            item.setSelected(False)

    def onSelectionChanged(self):
        model_items = [item.modelItem() for item in self.selectedItems()]
        self.tool.treeview().setSelectedItems(model_items)
        self.editSelectedItems()

    def onSelectionChangedInTreeView(self, model_items):
        block = self.blockSignals(True)
        selected_items = set()
        for model_item in model_items:
            for item in self.itemsFromIndex(model_item.index()):
                selected_items.add(item)
        for item in self.items():
            item.setSelected(False)
        for item in selected_items:
            if item is not None:
                item.setSelected(True)
        self.blockSignals(block)
        self.editSelectedItems()


    def keyPressEvent(self, event):
        if self._model is None or self._image_item is None:
            event.ignore()
            return

        if self._inserter is not None:
            # insert mode
            self._inserter.keyPressEvent(event, self._image_item)
        else:
            # selection mode
            if event.key() == Qt.Key_Delete:
                self.deleteSelectedItems()
                event.accept()

            elif event.key() == Qt.Key_Escape:
                # deselect all selected items
                for item in self.selectedItems():
                    item.setSelected(False)
                event.accept()

            elif len(self.selectedItems()) > 0:
                for item in self.selectedItems():
                    item.keyPressEvent(event)

        QGraphicsScene.keyPressEvent(self, event)

    def dataChanged(self, indexFrom, indexTo):
        if self._image_item is None or self._image_item.index() != indexFrom.parent().parent():
            return

        item = self.itemFromIndex(indexFrom.parent())
        if item is not None:
            item.dataChanged()

    def rowsInserted(self, index, first, last):
        print('rowsinserted')
        if self._image_item is None or self._image_item.index() != index:
            return
        self.insertItems(first, last)

    def rowsAboutToBeRemoved(self, index, first, last):
        if self._image_item is None or self._image_item.index() != index:
            return

        for row in range(first, last + 1):
            items = self.itemsFromIndex(index.child(row, 0))
            for item in items:
                # if the item has a parent item, do not delete it
                # we assume, that the parent shares the same model index
                # and thus removing the parent will also remove the child
                if item.parentItem() is not None:
                    continue
                self.removeItem(item)

    def itemFromIndex(self, index):
        for item in self.items():
            # some graphics items will not have an index method,
            # we just skip these
            if hasattr(item, 'index') and item.index() == index:
                return item
        return None

    def itemsFromIndex(self, index):
        items = []
        for item in self.items():
            # some graphics items will not have an index method,
            # we just skip these
            if hasattr(item, 'index') and item.index() == index:
                items.append(item)
        return items

    def selectAllItems(self):
        for item in self.items():
            item.setSelected(True)


