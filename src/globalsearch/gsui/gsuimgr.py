# ---------------
# Global Search - Substance 3D Designer plugin
# (c) 2019-2025 Eyosido Software SARL
# ---------------

from functools import partial

import sd
if sd.getContext().getSDApplication().getVersion() < "14.0.0":
    from PySide2.QtCore import QTimer
    from PySide2.QtWidgets import QVBoxLayout, QAction
else:
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QVBoxLayout
    from PySide6.QtGui import QAction

from globalsearch.gscore import gslog
from globalsearch.gsui.prefs import GSUIPref
from globalsearch.gsui.gsuiwidget import GSUIWidget
from globalsearch.gstests.gsunittests import GSUnitTests

class GSUIManager:
    """
    Main UI handler
    """
    APPNAME = "Global Search"

    @classmethod
    def classInit(cls):
        global g_gsuimgr
        g_gsuimgr = GSUIManager()

    @classmethod
    def classDeinit(cls):
        globals()["g_gsuimgr"] = None

    def __init__(self):
        app = sd.getContext().getSDApplication()
        self.uiMgr = app.getQtForPythonUIMgr()
        self.prefs = GSUIPref()
        self.uiWidget = None
        self.menu = None

    def setupUI(self):
        self.dockWidget =  self.uiMgr.newDockWidget('global_search', self.__class__.APPNAME)
        self.uiWidget = GSUIWidget(self)

        boxLayout = QVBoxLayout()
        self.dockWidget.setLayout(boxLayout)
        boxLayout.addWidget(self.uiWidget.ui)

        self.updateFromPrefs()

        if self.prefs.dev_unitTests:
            QTimer.singleShot(0, lambda:self.setupUnitTests())

    # create an application menu from where unit tests can be run
    def setupUnitTests(self):
        self.menu = self.uiMgr.newMenu(self.APPNAME, self.APPNAME)

        action = QAction("Run Unit Tests", self.menu)
        action.triggered.connect(lambda:self.onRunUnitTests())
        self.menu.addAction(action)

        action = QAction("Run Unit Tests (Record)", self.menu)
        action.triggered.connect(lambda:self.onRunUnitTests(record=True))
        self.menu.addAction(action)

        individualTestsMenu = self.menu.addMenu("Tests")

        action = QAction("Display Test Result In Tree View", individualTestsMenu)
        action.setCheckable(True)
        self.displayTestResultInTreeView = True
        action.setChecked(self.displayTestResultInTreeView)
        action.triggered.connect(self.onDisplayTestResultInTreeView)
        individualTestsMenu.addAction(action)

        for testId, test in GSUnitTests.TESTS.items():
            actionName = testId + " - " + test['name']
            action = QAction(actionName, individualTestsMenu)
            action.triggered.connect(partial(self.onRunTest, testId))
            individualTestsMenu.addAction(action)

    def onDisplayTestResultInTreeView(self, checked):
        self.displayTestResultInTreeView = checked

    def onRunUnitTests(self, record=False):
        unitTests = GSUnitTests(self.prefs)
        unitTests.runAllTests(record)

    def onRunTest(self, testId):
        unitTests = GSUnitTests(self.prefs)
        unitTests.runTestId(testId)
        if self.displayTestResultInTreeView:
            self.uiWidget.setSearchText(unitTests.searchCriteria.searchString)
            self.uiWidget.updateWithSearchResults(unitTests.searchResults, unitTests.searchCriteria, handleHistoryAndNav=False)

    def updateFromPrefs(self):
        self.uiWidget.showNodeTypeFilters(self.prefs.sc_DisplayNodeTypeFilters)

    def removeUI(self):
        gslog.info("Remove UI")
        if self.menu:
            self.uiMgr.deleteMenu(self.menu.objectName())
            self.menu = None      

        if self.dockWidget:
            if self.uiWidget.ui:
                self.uiWidget.ui.deleteLater()
                self.uiWidget.ui = None

            self.dockWidget.close()
            self.dockWidget.parent().close()

            # self.uiMgr.getMainWindow().removeDockWidget(self.dockWidget.parent())
            self.dockWidget = None
        else:
            gslog.error("dockWidget not found, cannot delete it.")

