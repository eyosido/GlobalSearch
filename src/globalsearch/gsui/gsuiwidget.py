# ---------------
# Global Search - Substance 3D Designer plugin
# (c) 2019-2022 Eyosido Software SARL
# ---------------

from enum import Enum
import os

import sd
if sd.getContext().getSDApplication().getVersion() < "14.0.0":
    from PySide2 import QtCore, QtWidgets, QtGui
    from PySide2.QtCore import QObject, Signal, Slot, QModelIndex, Qt, QEvent, QTimer
    from PySide2.QtUiTools import QUiLoader
    from PySide2.QtWidgets import QVBoxLayout, QWidget, QSlider, QLabel, QTreeWidget, QComboBox, QLineEdit, QTreeWidgetItemIterator, QSizePolicy
else:
    from PySide6 import QtCore, QtWidgets, QtGui
    from PySide6.QtCore import QObject, Signal, Slot, QModelIndex, Qt, QEvent, QTimer
    from PySide6.QtUiTools import QUiLoader
    from PySide6.QtWidgets import QVBoxLayout, QWidget, QSlider, QLabel, QTreeWidget, QComboBox, QLineEdit, QTreeWidgetItemIterator, QSizePolicy

from globalsearch.gscore.gs import GlobalSearch
from globalsearch.gscore import gslog
from globalsearch.gscore.searchdata import SearchResults
from globalsearch.gsui.uiutil import GSUIUtil
from globalsearch.gsui.searchroottree import GSUIComboTreeWidget
from globalsearch.gsui.resulttree import GSUISearchResultTreeWidget
from globalsearch.gsui.prefsdlg import GSUIPrefsDlg
from globalsearch.gsui.searchhistory import GSUISearchHistory

class GSUIToggleToolButton(QtWidgets.QToolButton):
    """
    A QToolButton that can be toggled between two states/two icons
    Listen to QAbstractButton. Toggled signal to receive information about state change
    """
    def __init__(self, uncheckedIcon, checkedIcon, parent=None):
        super().__init__(parent)
        self.uncheckedIcon = uncheckedIcon
        self.checkedIcon = checkedIcon
        self.setCheckable(True)
        self.setChecked(False)
        self.toggled.connect(self.onToggled)
        self.updateIcon()

    def onToggled(self, checked):
        self.updateIcon()

    def updateIcon(self):
        self.setIcon(self.checkedIcon if self.isChecked() else self.uncheckedIcon)

class GSUIWidget(QWidget):
    """
    Main UI widget
    """
    # --- Search combo item data
    SP_NONE = 0
    SP_PARAM_CUSTOM_FUNC = 1 # graph parameters with custom functions
    SP_TODO = 2
    SP_TMP = 3
    SP_LAST = 4

    class LineEdit(QLineEdit):
        """
        Used to intercept kepress to properly handle regular text vs. presets
        (for some reason event filtering did not work...)
        """
        def __init__(self, callback, parent=None):
            super().__init__(parent)
            self.callback = callback

        def keyPressEvent(self, event):
            self.callback.onSearchLineKeyPressEvent()
            return super().keyPressEvent(event)

    class SearchParams(QObject):
        def __init__(self, searchStr, searchRoot, nav, preset):
            super().__init__()
            self.searchStr = searchStr
            self.searchRoot = searchRoot
            self.nav = nav
            self.preset = preset

    def __init__(self, gsuiMgr):
        super().__init__()
        self.gsuiMgr = gsuiMgr
        self.uiMgr = gsuiMgr.uiMgr
        self.ui = None

        self.initialPopulationTimer = QTimer(self)
        self.initialPopulationTimer.timeout.connect(self.doPerformInitialSearchIntoPopulation)
        self.initialPopulationTimer.setInterval(100) # first timer attempt is fast, others will be spaced more

        self.performSearchTimer = QTimer(self)
        self.performSearchTimer.timeout.connect(self.doPerformSearch)
        self.searchParams = None

        self.loadStaticUI()
        self.setupDynamicUI()
        self.setupSearchHistory()
        self.connectSlots()
        self.prefsDlg = None

    def setupButtonIcon(self, button, iconFilename):
        button.setIcon(QtGui.QIcon(QtGui.QPixmap(GSUIUtil.filePathForIcon(iconFilename))))
        button.setText("")

    def loadStaticUI(self):
        self.ui = GSUIUtil.loadUI("gs_main.ui")
        self.ui.cb_search.lineEdit().setPlaceholderText("Search text")
        maxitems = GSUISearchHistory.DEFAULT_MAX_SEARCH_HISTORY_COUNT + 1 + self.__class__.SP_LAST
        self.ui.cb_search.setMaxCount(maxitems)
        self.ui.cb_search.setMaxVisibleItems(maxitems)
        self.ui.cb_search.setLineEdit(self.LineEdit(self, self.ui.cb_search))
        self.ui.cb_search.setCompleter(None) # disable auto-completion as creates issue with Presets

        # set up icons
        self.setupButtonIcon(self.ui.btn_prev_search, "gs_prev.png")
        self.setupButtonIcon(self.ui.btn_next_search, "gs_next.png")
        self.setupButtonIcon(self.ui.btn_refresh, "gs_refresh.png")
        self.setupButtonIcon(self.ui.btn_search, "gs_search.png")
        self.setupButtonIcon(self.ui.btn_clear, "gs_clear.png")
        self.setupButtonIcon(self.ui.btn_collapse, "gs_collapse.png")
        self.setupButtonIcon(self.ui.btn_expand, "gs_expand.png")
        self.setupButtonIcon(self.ui.btn_prefs, "gs_prefs.png")

        self.timedInitialSearchIntoPopulation()

    def setupDynamicUI(self):
        # add the search root combo box
        self.searchRootWidget = GSUIComboTreeWidget(self.ui)
        self.searchRootWidget.setToolTip("Where to search from")
        self.ui.hl_root.insertWidget(1, self.searchRootWidget)

        self.searchResultDisplayToogleButton = GSUIToggleToolButton(GSUIUtil.iconWithFilename("gs_list.png"), GSUIUtil.iconWithFilename("gs_tree.png"), self.ui)
        self.searchResultDisplayToogleButton.setToolTip("Toggle between list and tree search result views")
        self.ui.hl_search.insertWidget(5, self.searchResultDisplayToogleButton)
        self.curSearchPreset = self.__class__.SP_NONE

        self.searchResultTreeWidget = GSUISearchResultTreeWidget(self.gsuiMgr, self.ui)
        self.ui.vl_search_main.insertWidget(1, self.searchResultTreeWidget)
        
        self.clearStatus()
        self.onSearchTextChanged()
        self.enableExpandCollapseButtons()

    # We perform a first Search Into population on timer. As long as we have no population, we retry on timer until we have one. This prevents user to have to manually hit the Refresh button the first time the plugin is being used.
    # This could be avoided if we had events notifying us of new graph/package created/loaded.
    def timedInitialSearchIntoPopulation(self):
        if not self.initialPopulationTimer.isActive():
            self.initialPopulationTimer.start()

    def doPerformInitialSearchIntoPopulation(self):
        # gslog.info('Automatic refreshing of "Search Into" content until first population')
        self.searchRootWidget.reload()

        # check if we have population
        itemCount = self.searchRootWidget.treeWidget.topLevelItem(0).childCount() # top level item "Everything" is always present
        if itemCount > 0:
            self.initialPopulationTimer.stop()
            gslog.info('"Search Into" has been populated, stopping automatic population on timer')
        else:
            self.initialPopulationTimer.setInterval(1000)

    def enableNavButtons(self):
        self.ui.btn_prev_search.setEnabled(self.searchHistory.nav_has_prev())
        self.ui.btn_next_search.setEnabled(self.searchHistory.nav_has_next())

    def connectSlots(self):
        # we use lambda functions as the slot is not is the same class as the signal
        self.ui.btn_prev_search.clicked.connect(lambda:self.onPrevSearch())
        self.ui.btn_next_search.clicked.connect(lambda:self.onNextSearch())
        self.ui.btn_refresh.clicked.connect(lambda:self.onRefresh())
        self.ui.btn_search.clicked.connect(lambda:self.onSearch())
        le = self.ui.cb_search.lineEdit()
        le.returnPressed.connect(lambda:self.onSearch())
        le.textChanged.connect(lambda:self.onSearchTextChanged())
        self.ui.cb_search.currentIndexChanged.connect(lambda:self.onCurrentIndexChangred())
        self.ui.btn_expand.clicked.connect(lambda:self.onExpandAll())
        self.ui.btn_collapse.clicked.connect(lambda:self.onCollapseAll())
        self.ui.btn_clear.clicked.connect(lambda:self.onClear())
        self.ui.btn_prefs.clicked.connect(lambda:self.onPrefs())
        self.searchResultDisplayToogleButton.toggled.connect(self.onSearchResultDisplayToggle)
        
    def getCurrentSearchRoot(self):
        treeWidget = self.searchRootWidget.treeWidget
        treeItem = treeWidget.currentItem()

        if not treeItem:
            treeItem = treeWidget.topLevelItem(0)

        customTreeData = None

        if treeItem:
            customTreeData = treeWidget.customDataFromTreeItem(treeItem)
            
        return customTreeData

    def programmaticSearch(self, text, nav=False):
        self.ui.cb_search.lineEdit().setText(text)
        self.getTextAndSearch(nav)

    # --- slots
    def onPrevSearch(self):
        if self.searchHistory.nav_has_prev():
            self.programmaticSearch(self.searchHistory.nav_prev(), nav=True)
            self.enableNavButtons()

    def onNextSearch(self):
        if self.searchHistory.nav_has_next():
            self.programmaticSearch(self.searchHistory.nav_next(), nav=True)
            self.enableNavButtons()
    
    def onRefresh(self):
        gslog.info('Refreshing "Search Into" content')
        self.searchRootWidget.reload()

    def onSearch(self):
        self.getTextAndSearch(nav=False)

    def getTextAndSearch(self, nav=False):
        searchStr = self.ui.cb_search.currentText()
        if searchStr and len(searchStr) > 0:
            customTreeData = self.getCurrentSearchRoot()
            if customTreeData:
                self.performSearch(searchStr, customTreeData.sdObj, nav, self.curSearchPreset)
            else:
                gslog.info("No search root item found")

    def onSearchTextChanged(self):
        searchStr = self.ui.cb_search.currentText()
        hasText = searchStr is not None and len(searchStr) > 0
        self.ui.btn_search.setEnabled(hasText)
        self.ui.btn_clear.setEnabled(hasText)

    def onExpandAll(self):
        self.searchResultTreeWidget.expandCollapseAllItems(expand=True)

    def onCollapseAll(self):
        self.searchResultTreeWidget.expandCollapseAllItems(expand=False)

    def onClear(self):
        self.ui.cb_search.lineEdit().clear()
        self.emptySearchResults()
        self.clearStatus()

    def onPrefs(self):
        if not self.prefsDlg:
            self.prefsDlg = GSUIPrefsDlg(self.gsuiMgr, self)
        self.prefsDlg.setupFromPrefs()
        self.prefsDlg.show()

    def onSearchResultDisplayToggle(self, checked):
        self.searchResultTreeWidget.setDisplayMode(GSUISearchResultTreeWidget.DM_LIST if checked else GSUISearchResultTreeWidget.DM_TREE)
        self.enableExpandCollapseButtons()

     # --- processings
    # nav: True if search is issued by a navitation prev/next action
    def performSearch(self, searchStr, searchRoot, nav=False, preset = SP_NONE):
        self.setStatusSearching()
        self.searchParams = self.SearchParams(searchStr, searchRoot, nav, preset)
        self.performSearchTimer.start(1)

    def doPerformSearch(self):
        self.performSearchTimer.stop()
        searchCriteria = self.gsuiMgr.prefs.toSearchCriteria()
        searchCriteria.searchString = self.searchParams.searchStr

        # search presets
        if self.searchParams.preset == self.__class__.SP_PARAM_CUSTOM_FUNC:
            searchCriteria.setupForSSParamFunc()
        elif self.searchParams.preset == self.__class__.SP_TODO or self.searchParams.preset == self.__class__.SP_TODO:
            searchCriteria.caseSensitive = True

        searchResults = SearchResults()
        globalSearch = GlobalSearch(sd.getContext(), self.searchParams.searchRoot, searchCriteria, searchResults)

        globalSearch.search()
        #searchResults.log()

        self.emptySearchResults()
        self.populateSearchResults(searchResults, searchCriteria)
        
        if searchResults.hasSearchResults():
            if self.searchHistory:
                if self.searchParams.preset == self.__class__.SP_NONE:
                    self.searchHistory.push(self.searchParams.searchStr)

            if not self.searchParams.nav:
                # search does not come from a navigation prev/next action so append it to nav list
                self.searchHistory.nav_append(self.searchParams.searchStr)
                self.enableNavButtons()

            self.setStatusResultFound(searchResults.getFoundCount())
        else:
            self.setNotFoundStatus(self.searchParams.searchStr)

        self.enableExpandCollapseButtons()

    def enableExpandCollapseButtons(self):
        hasSearchResults = self.searchResultTreeWidget.topLevelItemCount() > 0
        treeMode = self.searchResultTreeWidget.displayMode == GSUISearchResultTreeWidget.DM_TREE
        enable = hasSearchResults and treeMode
        self.ui.btn_expand.setEnabled(enable)
        self.ui.btn_collapse.setEnabled(enable)

    def emptySearchResults(self):
        self.searchResultTreeWidget.clearAll()

    def populateSearchResults(self, searchResults, searchCriteria):
        self.searchResultTreeWidget.populate(searchResults, searchCriteria)

    # search history
    def insertSearchHistory(self, index, text, data = SP_NONE):
        self.ui.cb_search.insertItem(index, text, data)

    def setupSearchHistory(self):
        self.searchHistory = GSUISearchHistory(self)
        self.searchHistory.load()

        # populate search history
        self.ui.cb_search.clear()
        i = 0
        for text in self.searchHistory.history:
            self.insertSearchHistory(i, text)
            i += 1
        self.ui.cb_search.setCurrentIndex(-1) # not initial selection

        self.fieldClearedOnPreset = False

        # append search presets
        self.searchHistorySeparatorIndex = i
        self.ui.cb_search.insertSeparator(self.searchHistorySeparatorIndex)
        self.insertSearchHistory(self.searchHistorySeparatorIndex + 1, "Param functions", self.__class__.SP_PARAM_CUSTOM_FUNC)
        self.insertSearchHistory(self.searchHistorySeparatorIndex + 2, "TODO", self.__class__.SP_TODO)
        self.insertSearchHistory(self.searchHistorySeparatorIndex + 3, "TMP", self.__class__.SP_TMP)

        self.enableNavButtons()

    def disableSearchHistory(self):
        if self.searchHistory:
            self.searchHistory.delete()
            self.searchHistory = None

    def onSearchLineKeyPressEvent(self):
        if not self.fieldClearedOnPreset and self.currentSelIsPreset():
            self.ui.cb_search.lineEdit().clear()
            self.fieldClearedOnPreset = True
            self.ui.cb_search.setCurrentIndex(-1)
            self.curSearchPreset = self.__class__.SP_NONE

    def currentSelIsPreset(self):
        index = self.ui.cb_search.currentIndex()
        return index != -1 and self.ui.cb_search.itemData(index) != self.__class__.SP_NONE

    def onCurrentIndexChangred(self):
        self.fieldClearedOnPreset = False

        index = self.ui.cb_search.currentIndex()
        if index > self.searchHistorySeparatorIndex:
            self.curSearchPreset = self.ui.cb_search.itemData(index)
        else:
            self.curSearchPreset = self.__class__.SP_NONE

    def updateSearchHistorySeparatorIndex(self):
        self.searchHistorySeparatorIndex = len(self.searchHistory.history)

    # --- GSUISearchHistory callbacks
    def searchHistoryUpdateStarting(self):
        self.searchHistoryCurIndexModified = False
    
    def searchHistoryUpdateEnded(self):
        if self.searchHistory.count() > 0:
            # after a history update, most recent item is always on top, select it
            # to make sure we are not pointing on old data
            self.ui.cb_search.setCurrentIndex(0)

    def searchHistoryPushed(self, text):
        self.ui.cb_search.insertItem(0, text, self.__class__.SP_NONE)
        self.updateSearchHistorySeparatorIndex()

    def searchHistoryRemoved(self, index):
        self.ui.cb_search.removeItem(index)
        self.updateSearchHistorySeparatorIndex()

    def searchHistoryCleared(self):
        for _ in range(0, self.searchHistorySeparatorIndex):
            self.ui.cb_search.removeItem(0)
        self.searchHistorySeparatorIndex = 0
        self.ui.cb_search.setCurrentIndex(-1) # reset current index

    # --- status operations
    def setStatus(self, status):
        self.ui.l_status.setText(status)

    def clearStatus(self):
        self.setStatus("")

    def setNotFoundStatus(self, searchStr = None):
        if searchStr:
            self.setStatus("No result found for \"" + searchStr + "\".")
        else:
            self.setStatus("No result found.")

    def setStatusSearching(self):
        self.setStatus("Searching...")

    def setStatusResultFound(self, resultCount):
        resultStr = "results" if resultCount > 1 else "result"
        self.setStatus("Found " + str(resultCount) + " " + resultStr + ".")
