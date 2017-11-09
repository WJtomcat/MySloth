import os
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QWidget, QVBoxLayout
from PyQt5.QtCore import QSettings, QVariant, QSize, QPoint, QObject
from sloth import APP_NAME, ORGANIZATION_DOMAIN
import PyQt5.uic as uic
from sloth.gui.frameviewer import GraphicsView
from sloth.gui.annotationscene import AnnotationScene
from sloth.gui.controlbuttons import ControlButtonWidget
from sloth.gui.logindl import LoginDialog
from sloth.annotations.model import *
from sloth.network.network import Network
from sloth.gui.caselist import CaseListDialog
from sloth.gui.annotationtool import AnnotationTool
from sloth.gui.propertyeditor import PropertyEditor
from sloth.conf import config
from sloth.gui.inftable import CaseInformationWidget
from sloth.core.utils import import_callable
from sloth.utils.bind import *

GUIDIR=os.path.join(os.path.dirname(__file__))


class MainWindow(QMainWindow):
    def __init__(self, labeltool, parent=None):
        QMainWindow.__init__(self, parent)
        self.network = Network()
        self.tool = AnnotationTool(self, self.network)

        self.logindl = LoginDialog(self.network, self)
        self.caseList = CaseListDialog(self.network, self.tool)

        self.setupGui()
        self.connectActions()
        self.onAnnotationsLoaded()
        self.loadApplicationSettings()

        self.network.caseChanged.connect(self.inftable.onCaseChanged)


    def setupGui(self):
        inserters = dict([(label['attributes']['class'], label['inserter'])
                          for label in config.LABELS
                          if 'class' in label.get('attributes', {}) and 'inserter' in label])
        items = dict([(label['attributes']['class'], label['item'])
                      for label in config.LABELS
                      if 'class' in label.get('attributes', {}) and 'item' in label])

        self.ui = uic.loadUi(os.path.join(GUIDIR, "labeltool.ui"), self)

        self.view = GraphicsView()
        self.scene = AnnotationScene(self.tool, inserters=inserters, items=items)
        self.view.setScene(self.scene)

        self.central_widget = QWidget()
        self.central_layout = QVBoxLayout()
        self.controls = ControlButtonWidget()
        self.controls.back_button.clicked.connect(self.tool.gotoPrevious)
        self.controls.forward_button.clicked.connect(self.tool.gotoNext)

        self.central_layout.addWidget(self.controls)
        self.central_layout.addWidget(self.view)
        self.central_widget.setLayout(self.central_layout)
        self.setCentralWidget(self.central_widget)

        self.initShortcuts(config.HOTKEYS)

        self.treeview =AnnotationTreeView()
        self.treeview.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        self.ui.dockAnnotations.setWidget(self.treeview)

        self.propertyEditor = PropertyEditor(config, self.tool)
        self.ui.dockProperties.setWidget(self.propertyEditor)
        self.propertyEditor.insertionModeStarted.connect(self.scene.onInsertionModeStarted)
        self.propertyEditor.insertionModeEnded.connect(self.scene.onInsertionModeEnded)

        self.inftable = CaseInformationWidget(self.tool)
        self.ui.dockInformation.setWidget(self.inftable)

        self.statusBar = QStatusBar()
        self.posinfo = QLabel("-1, -1")
        self.posinfo.setFrameStyle(QFrame.StyledPanel)
        self.statusBar.addPermanentWidget(self.posinfo)

        self.image_resolution = QLabel('[No Image]')
        self.image_resolution.setFrameStyle(QFrame.StyledPanel)
        self.statusBar.addPermanentWidget(self.image_resolution)

        self.image_download = QLabel('[Image Download]')
        self.image_download.setFrameStyle(QFrame.StyledPanel)
        self.statusBar.addPermanentWidget(self.image_download)

        self.zoominfo = QLabel()
        self.zoominfo.setFrameStyle(QFrame.StyledPanel)
        self.statusBar.addPermanentWidget(self.zoominfo)

        self.setStatusBar(self.statusBar)

    def connectActions(self):
        self.ui.open.triggered.connect(self.onOpen)
        self.ui.save.triggered.connect(self.onSave)
        self.ui.submit.triggered.connect(self.onSubmit)
        self.ui.actionExit.triggered.connect(self.close)

        self.ui.actionNext.triggered.connect(self.tool.gotoNext)
        self.ui.actionPrevious.triggered.connect(self.tool.gotoPrevious)
        # self.ui.actionZoom_In.triggered.connect()
        # self.ui.actionZoom_Out.triggered.connect()
        self.ui.actionLogin.triggered.connect(self.login)
        self.ui.actionLogoff.triggered.connect(self.logoff)
        self.tool.annotationsLoaded.connect(self.onAnnotationsLoaded)
        self.tool.currentImageChanged.connect(self.onCurrentImageChanged)

    def initShortcuts(self, HOTKEYS):
        self.shortcuts = []

        for hotkey in HOTKEYS:
            assert len(hotkey) >= 2
            key = hotkey[0]
            fun = hotkey[1]
            desc = ""
            if len(hotkey) > 2:
                desc = hotkey[2]
            if type(fun) == str:
                fun = import_callable(fun)

            hk = QAction(desc, self)
            hk.setShortcut(QKeySequence(key))
            hk.setEnabled(True)
            if hasattr(fun, '__call__'):
                hk.triggered.connect(bind(fun, self.tool))
            else:
                hk.triggered.connect(compose_noargs([bind(f, self.tool) for f in fun]))
            self.ui.menuShortcuts.addAction(hk)
            self.shortcuts.append(hk)

    def onAnnotationsLoaded(self):
        self.tool.model().dirtyChanged.connect(self.onModelDirtyChanged)
        self.onModelDirtyChanged(self.tool.model().dirty())
        self.treeview.setModel(self.tool.model())
        self.scene.setModel(self.tool.model())
        self.selectionmodel = QItemSelectionModel(self.tool.model())
        self.treeview.setSelectionModel(self.selectionmodel)
        self.treeview.selectionModel().currentChanged.connect(self.tool.setCurrentImage)

    def login(self):
        if self.network.isLogin():
            if not self.okToContinue():
                return
            else:
                reply = QMessageBox.question(self,
                        "Unsaved Changes",
                        'WJ',
                        QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.No:
                    return
        self.logindl.showDialog()

    def logoff(self):
        if not self.network.isLogin():
            return
        if not self.okToContinue():
            return
        self.network.logOff()
        self.onModelDirtyChanged(False)

    def onSave(self):
        print(self.tool.annotations())
        out = self.network.labelUpload(self.tool.annotations(), isSubmit=False)
        if out:
            self.tool.model().setDirty(False)
        return out

    def onSubmit(self):
        print(self.tool.annotations())
        out = self.network.labelUpload(self.tool.annotations(), isSubmit=True)
        if out:
            self.tool.clearAnnotations()

    def onOpen(self):
        if not self.network.isLogin():
            QMessageBox.question(self, 'message', 'Please login first.', QMessageBox.Ok)
            return
        if self.okToContinue():
            self.tool.clearAnnotations()
            self.inftable.onCaseChanged(None)
            self.inftable.onImageChanged(None)
            self.caseList.show()
            self.caseList.getData()

    def onCurrentImageChanged(self):
        new_image = self.tool.currentImage()
        self.scene.setCurrentImage(new_image)
        self.treeview.scrollTo(new_image.index())
        self.inftable.onImageChanged(new_image)

    def okToContinue(self):
        if self.tool.model().dirty():
            reply = QMessageBox.question(self,
                    "message",
                    'Save Unsaved changes?',
                    QMessageBox.Yes|QMessageBox.No|QMessageBox.Cancel)
            if reply == QMessageBox.Cancel:
                return False
            elif reply == QMessageBox.Yes:
                return self.onSave()
        return True

    def onModelDirtyChanged(self, dirty):
        postfix = '[+]' if dirty else ''
        name = self.network.name
        self.setWindowTitle('%s%s - username:%s' % (APP_NAME, postfix, name))

    def loadApplicationSettings(self):
        settings = QSettings()
        size = settings.value("MainWindow/Size", QSize(1000, 800))
        pos = settings.value("MainWindow/Position", QPoint(10, 10))
        state = settings.value("MainWindow/State")
        locked = settings.value("MainWindow/ViewsLocked", False)
        if isinstance(size, QVariant): size = size.toSize()
        if isinstance(pos, QVariant): pos = pos.toPoint()
        if isinstance(state, QVariant): state = state.toByteArray()
        if isinstance(locked, QVariant): locked = locked.toBool()
        self.resize(size)
        self.move(pos)
        if state is not None:
            self.restoreState(state)
        self.ui.actionLocked.setChecked(bool(locked))

    def saveApplicationSettings(self):
        settings = QSettings()
        settings.setValue("MainWindow/Size", self.size())
        settings.setValue("MainWindow/Position", self.pos())
        settings.setValue("MainWindow/State", self.saveState())
        settings.setValue("MainWindow/ViewsLocked", self.ui.actionLocked.isChecked())

    def closeEvent(self, event):
        if self.okToContinue():
            self.saveApplicationSettings()
        else:
            event.ignore()

    def about(self):
        QMessageBox.about(self, "About %s" % APP_NAME,
             """<b>%s</b> version %s
             <p>This labeling application for computer vision research
             was developed at the CVHCI research group at KIT.
             <p>For more details, visit our homepage: <a href="%s">%s</a>"""
              % (APP_NAME, __version__, ORGANIZATION_DOMAIN, ORGANIZATION_DOMAIN))
