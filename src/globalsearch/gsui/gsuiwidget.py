# ---------------
# Global Search - Substance 3D Designer plugin
# (c) 2019-2025 Eyosido Software SARL
# ---------------

import os, json
import sd
if sd.getContext().getSDApplication().getVersion() < "14.0.0":
    from PySide2 import QtWidgets, QtGui
    from PySide2.QtCore import QObject, Qt, QTimer, QStandardPaths
    from PySide2.QtWidgets import QWidget, QLineEdit, QSizePolicy, QSpacerItem, QFileDialog, QMessageBox

else:
    from PySide6 import QtCore, QtWidgets, QtGui
    from PySide6.QtCore import QObject, Qt, QTimer, QStandardPaths
    from PySide6.QtWidgets import QWidget, QLineEdit, QSizePolicy, QSpacerItem, QFileDialog, QMessageBox


from sd.api.apiexception import APIException

from globalsearch.gscore.gs import GlobalSearch
from globalsearch.gscore import gslog
from globalsearch.gscore.sdobj import SDObj
from globalsearch.gscore.searchdata import SearchResults, NoteTypeFilterData, SearchResultPathNodeJSONEncoder
from globalsearch.gscore import gssdlibrary
from globalsearch.gscore.gspresets import GSPresetTypes
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
        def __init__(self, searchStr, searchRoot, nav, preset, graphNodeFilter, functionNodeFilter):
            super().__init__()
            self.searchStr = searchStr
            self.searchRoot = searchRoot
            self.nav = nav
            self.preset = preset
            self.graphNodeFilter = graphNodeFilter
            self.functionNodeFilter = functionNodeFilter

        def isPreset(self):
            return self.preset != GSPresetTypes.SP_NONE

        def hasSearchString(self):
            return self.searchStr and len(self.searchStr) > 0        

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

        self.ignoreSearchTextChanged = False  # used for programmatic search
        self.ignoreNodeFilterTypeChanged = False  # used for programmatic search

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
        maxitems = GSUISearchHistory.DEFAULT_MAX_SEARCH_HISTORY_COUNT + 1 + GSPresetTypes.SP_LAST
        self.ui.cb_search.setMaxCount(maxitems)
        self.ui.cb_search.setMaxVisibleItems(maxitems)
        self.ui.cb_search.setLineEdit(self.LineEdit(self, self.ui.cb_search))
        self.ui.cb_search.setCompleter(None) # disable auto-completion as creates issue with Presets

        # set up icons
        buttonIconDesc = [ (self.ui.btn_prev_search, "gs_prev.png"),
                           (self.ui.btn_next_search, "gs_next.png"),
                           (self.ui.btn_refresh, "gs_refresh.png"),
                           (self.ui.btn_search, "gs_search.png"),
                           (self.ui.btn_clear, "gs_clear.png"),
                           (self.ui.btn_collapse, "gs_collapse.png"),
                           (self.ui.btn_expand, "gs_expand.png"),
                           (self.ui.btn_prefs, "gs_prefs.png"),
                           (self.ui.btn_prev_sr, "gs_prev_sr.png"),
                           (self.ui.btn_next_sr, "gs_next_sr.png"),
                           (self.ui.btn_focus_sr, "gs_focus.png"),
                           (self.ui.btn_save_sr, "gs_save.png")
                          ]
        for desc in buttonIconDesc:
            self.setupButtonIcon(desc[0], desc[1])

        self.ui.btn_focus_sr.setCheckable(True)
        self.ui.btn_focus_sr.setChecked(True)

        self.setupNodeTypeFilters()

        self.timedInitialSearchIntoPopulation()
        
    def setupDynamicUI(self):
        # add the search root combo box
        self.searchRootWidget = GSUIComboTreeWidget(self.ui)
        self.searchRootWidget.setToolTip("Where to search from")
        self.ui.hl_root.insertWidget(1, self.searchRootWidget)

        self.searchResultDisplayToogleButton = GSUIToggleToolButton(GSUIUtil.iconWithFilename("gs_list.png"), GSUIUtil.iconWithFilename("gs_tree.png"), self.ui)
        self.searchResultDisplayToogleButton.setToolTip("Toggle between list and tree search result views")
        self.ui.hl_search.insertWidget(5, self.searchResultDisplayToogleButton)
        self.curSearchPreset = GSPresetTypes.SP_NONE

        self.searchResultTreeWidget = GSUISearchResultTreeWidget(self.gsuiMgr, self.ui)
        self.ui.vl_search_main.insertWidget(2, self.searchResultTreeWidget)

        spacer = QSpacerItem(10, 24, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.ui.hl_found.insertSpacerItem(1, spacer)

        # self.focusToogleButton = GSUIToggleToolButton(GSUIUtil.iconWithFilename("gs_focus.png"), GSUIUtil.iconWithFilename("gs_focus.png"), self.ui)
        # self.focusToogleButton.setToolTip("Toggle between list and tree search result views")
        # self.ui.hl_found.insertWidget(3, self.focusToogleButton)

        self.clearStatus()
        self.onSearchTextOrNodeTypeFilterChanged()
        self.enableSearchResultControls()

    def setupNodeTypeFilters(self):
        # --- Compositing nodes
        self.ui.cb_graph_node_type.addItem("All graph nodes", None)
        italicFont = QtGui.QFont()
        italicFont.setItalic(True)
        self.ui.cb_graph_node_type.setItemData(0, italicFont, role=Qt.ItemDataRole.FontRole)

        boldFont = QtGui.QFont()
        boldFont.setBold(True)
        boldFont.setItalic(True)

        # Atomic nodes
        self.addSeparatorToNodeTypeCB("Atomic nodes", boldFont)
        self.populateSystemNodeTypeCB(SDObj.SDNODE_COMPOSITING_TYPE, self.ui.cb_graph_node_type) 

        # FX-Map nodes
        self.addSeparatorToNodeTypeCB("FX-Map nodes", boldFont)
        self.populateSystemNodeTypeCB(SDObj.SDNODE_FXMAP_TYPE, self.ui.cb_graph_node_type)

        # SD Library nodes
        self.addSeparatorToNodeTypeCB("Library nodes", boldFont)
        self.populateLibraryNodeTypeCB() 

        # --- Function nodes
        self.ui.cb_fct_node_type.addItem("All function nodes", None)
        self.ui.cb_fct_node_type.setItemData(0, italicFont, role=Qt.ItemDataRole.FontRole)
        self.ui.cb_fct_node_type.insertSeparator(1)
        self.populateSystemNodeTypeCB(SDObj.NODE_FUNCTION_TYPE, self.ui.cb_fct_node_type) 

    def addSeparatorToNodeTypeCB(self, separatorName, font):
        self.ui.cb_graph_node_type.insertSeparator(self.ui.cb_graph_node_type.count())
        self.ui.cb_graph_node_type.addItem(separatorName, None)
        self.ui.cb_graph_node_type.setItemData(self.ui.cb_graph_node_type.count()-1, font, role=Qt.ItemDataRole.FontRole)

    def populateLibraryNodeTypeCB(self):
        lib = gssdlibrary.g_gssdlibrary
        lib_nodes = lib.load()
        
        if lib_nodes and len(lib_nodes) > 0:
            sorted_items = dict(sorted(lib_nodes.items(), key=lambda item: item[gssdlibrary.GSSDLibrary.LABEL].lower()))
            for identifier, v in sorted_items.items():
                label = v[gssdlibrary.GSSDLibrary.LABEL]
                data = NoteTypeFilterData.fromLibrary(label, identifier)
                display_label = GSUIUtil.croppedText(label, maxLen=28, ellipsis='..')
                self.ui.cb_graph_node_type.addItem(display_label, data)

    def populateSystemNodeTypeCB(self, collection, cb):
        sorted_items = dict(sorted(collection.items(), key=lambda item: item[1][1].lower()))
        for definition, typeTuple in sorted_items.items():
            label = typeTuple[1]
            data = NoteTypeFilterData.fromSystem(label, definition, typeTuple[0])
            display_label = GSUIUtil.croppedText(label, maxLen=28, ellipsis='..')
            cb.addItem(display_label, data)

    # We perform a first Search Into population on timer. As long as we have no population, we retry on timer until we have one. This prevents user to have to manually hit the Refresh button the first time the plugin is being used.
    # This could be avoided if we had events notifying us of new graph/package created/loaded.
    def timedInitialSearchIntoPopulation(self):
        if not self.initialPopulationTimer.isActive():
            self.initialPopulationTimer.start()

    def doPerformInitialSearchIntoPopulation(self):
        self.initialPopulationTimer.setInterval(1000)
        # gslog.info('Automatic refreshing of "Search Into" content until first population')
        self.searchRootWidget.reload()

        # check if we have population
        itemCount = self.searchRootWidget.treeWidget.topLevelItem(0).childCount() # top level item "Everything" is always present
        if itemCount > 0:
            self.initialPopulationTimer.stop()
            gslog.info('"Search Into" has been populated, stopping automatic population on timer')

    def showNodeTypeFilters(self, show):
        # self.ui.l_graph_node_type.setVisible(show)
        self.ui.cb_graph_node_type.setVisible(show)
        self.ui.cb_fct_node_type.setVisible(show)

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
        self.ui.cb_graph_node_type.currentIndexChanged.connect(lambda:self.onSearchTextOrNodeTypeFilterChanged())
        self.ui.cb_fct_node_type.currentIndexChanged.connect(lambda:self.onSearchTextOrNodeTypeFilterChanged())
        self.ui.btn_expand.clicked.connect(lambda:self.onExpandAll())
        self.ui.btn_collapse.clicked.connect(lambda:self.onCollapseAll())
        self.ui.btn_clear.clicked.connect(lambda:self.onClear())
        self.ui.btn_prefs.clicked.connect(lambda:self.onPrefs())
        self.ui.btn_prev_sr.clicked.connect(lambda:self.onPrevFoundResult())
        self.ui.btn_next_sr.clicked.connect(lambda:self.onNextFoundResult())
        self.ui.btn_save_sr.clicked.connect(lambda:self.onSaveSearchResults())
        self.searchResultDisplayToogleButton.toggled.connect(self.onSearchResultDisplayToggle)
        
    def getCurrentSearchRoot(self):
        treeWidget = self.searchRootWidget.treeWidget
        if self.searchRootWidget.lastSelectedItem:
            treeItem = self.searchRootWidget.lastSelectedItem # more reliable than currentItem(), see definition of lastSelectedItem
        else:
            treeItem = treeWidget.currentItem()

        if not treeItem:
            treeItem = treeWidget.topLevelItem(0)

        customTreeData = None

        if treeItem:
            customTreeData = treeWidget.customDataFromTreeItem(treeItem)        
            
        return customTreeData

    def isSearchRootValid(self, customTreeData):
        # check whether root is valid (in case Search Root is not refreshed and object does not exist anymore)
        valid = True
        if customTreeData.entryType != SDObj.ROOT:
            try:
                customTreeData.sdObj.getFilePath()
            except APIException as e:
                valid = False

        return valid

    def setSearchText(self, text):
        self.ui.cb_search.lineEdit().setText(text)

    def programmaticSearch(self, text, nav=False):
        self.ignoreSearchTextChanged = True
        self.setSearchText(text)
        self.getTextAndSearch(nav)
        self.ignoreSearchTextChanged = False

    def processPrevNextItem(self, item):
        self.ignoreNodeFilterTypeChanged = True
        self.ui.cb_search.setCurrentIndex(-1)

        self.curSearchPreset = item['preset']
        self.ui.cb_graph_node_type.setCurrentIndex(item['ntfi'])
        self.ui.cb_fct_node_type.setCurrentIndex(item['fntfi'])

        self.programmaticSearch(item['text'], nav=True)

        self.enableNavButtons()
        self.enableNodeTypeFilters()
        self.ignoreNodeFilterTypeChanged = False
        self.onSearchTextOrNodeTypeFilterChanged() # important: fixes search button not re-enabling after Clear History and prev navigation.

    # --- slots
    def onPrevSearch(self):
        if self.searchHistory.nav_has_prev():
            item = self.searchHistory.nav_prev()
            self.processPrevNextItem(item)

    def onNextSearch(self):
        if self.searchHistory.nav_has_next():
            item = self.searchHistory.nav_next()
            self.processPrevNextItem(item)
    
    def onRefresh(self):
        gslog.info('Refreshing "Search Into" content')
        self.searchRootWidget.reload()

    def onSearch(self):
        self.getTextAndSearch(nav=False)

    def getTextAndSearch(self, nav=False):
        searchStr = self.ui.cb_search.currentText()
        if (searchStr and len(searchStr) > 0) or (self.ui.cb_graph_node_type.currentIndex() > 0) or (self.ui.cb_fct_node_type.currentIndex() > 0):
            customTreeData = self.getCurrentSearchRoot()
            if customTreeData:
                if self.isSearchRootValid(customTreeData):
                    self.performSearch(searchStr, customTreeData.sdObj, nav, self.curSearchPreset)
                else:
                    gslog.warning("Search Root does not exist anymore, refreshing search roots and selecting \"Everything\" as Search Root.")
                    self.onRefresh()
                    QMessageBox.warning(self, self.gsuiMgr.APPNAME, "The selected Search Root does not exist anymore. Search Roots have been refreshed, please restart your search with an appropriate Search Root.")
            else:
                gslog.info("No search root item found")

    def onSearchTextChanged(self):
        if not self.ignoreSearchTextChanged:
            self.curSearchPreset = GSPresetTypes.SP_NONE
            self.onSearchTextOrNodeTypeFilterChanged()

    def onSearchTextOrNodeTypeFilterChanged(self):
        if not self.ignoreNodeFilterTypeChanged:
            searchStr = self.ui.cb_search.currentText()
            hasText = searchStr is not None and len(searchStr) > 0

            graph_node_filter_index = self.ui.cb_graph_node_type.currentIndex()
            fct_node_filter_index = self.ui.cb_fct_node_type.currentIndex()

            nodeTypeText = self.ui.cb_graph_node_type.currentText()
            if nodeTypeText.endswith(' nodes'):
                # this is a separator, we cannot select them as filter, select the root instead
                self.ui.cb_graph_node_type.setCurrentIndex(0)
                graph_node_filter_index = 0

            enabler = hasText or ((not hasText) and ((graph_node_filter_index != 0) or (fct_node_filter_index != 0)))
            self.ui.btn_search.setEnabled(enabler)

            self.enableNodeTypeFilters()

    def onExpandAll(self):
        self.searchResultTreeWidget.expandCollapseAllItems(expand=True)

    def onCollapseAll(self):
        self.searchResultTreeWidget.expandCollapseAllItems(expand=False)

    def onClear(self):
        self.ui.cb_search.lineEdit().clear()
        self.ui.cb_search.setCurrentIndex(-1)
        self.curSearchPreset = GSPresetTypes.SP_NONE
        self.emptySearchResults()
        self.clearStatus()
        self.enableSearchResultControls()

    def onPrefs(self):
        if not self.prefsDlg:
            self.prefsDlg = GSUIPrefsDlg(self.gsuiMgr, self)
        self.prefsDlg.setupFromPrefs()
        self.prefsDlg.show()

    def navFirstOrLastFoundItem(self, first):
        foundItem = None
        # get first or last item in tree
        item = self.searchResultTreeWidget.navFirstTreeItem() if first else self.searchResultTreeWidget.navLastTreeItem()
        if item:
            # is this item a found item?
            if self.searchResultTreeWidget.navIsFoundItem(item):
                foundItem = item
            else:
                # this item is not a found item, find the first found item either forward (first is True) or backward
                foundItem = self.searchResultTreeWidget.navFoundItem(first, item)
        return foundItem

    def navFoundResult(self, next):
        if not self.hasSearchResults():
            return

        item = self.searchResultTreeWidget.currentItem()
        foundItem = None
        if not item:
            # no currently selected item, get first (next) or last (prev) found item
            foundItem = self.navFirstOrLastFoundItem(next)
        else:
            # search for the next or previous found item
            foundItem = self.searchResultTreeWidget.navFoundItem(next, item)

        if foundItem:
            self.searchResultTreeWidget.setCurrentItem(foundItem)
            if self.ui.btn_focus_sr.isChecked():
                self.searchResultTreeWidget.openOrFocusOnItemIfPossible(foundItem)

    def onPrevFoundResult(self):
        self.navFoundResult(next=False)

    def onNextFoundResult(self):
        self.navFoundResult(next=True)

    def onSaveSearchResults(self):
        initialPath = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
        initialPath = os.path.join(initialPath, "gs_search_result.json")
        filePath,_ = QFileDialog.getSaveFileName(self, "Save Search Result", initialPath, "JSON (*.json)")
        if filePath and len(filePath) > 0:
            try:
                with open(filePath, 'w') as writeFile: 
                    json.dump(self.searchResults.pathTree, writeFile, cls=SearchResultPathNodeJSONEncoder)
                gslog.info("Test result saved to: " + filePath)
            except:
                gslog.error("Error writing test result: " + filePath)

    def onSearchResultDisplayToggle(self, checked):
        self.searchResultTreeWidget.setDisplayMode(GSUISearchResultTreeWidget.DM_LIST if checked else GSUISearchResultTreeWidget.DM_TREE)
        self.enableExpandCollapseButtons()

     # --- processings
    # nav: True if search is issued by a navitation prev/next action
    def performSearch(self, searchStr, searchRoot, nav=False, preset = GSPresetTypes.SP_NONE):
        self.setStatusSearching()

        # Node type filter
        graphNodeFilter = None
        functionNodeFilter = None
        if self.gsuiMgr.prefs.sc_DisplayNodeTypeFilters:
            graphNodeFilter = self.ui.cb_graph_node_type.currentData()
            functionNodeFilter = self.ui.cb_fct_node_type.currentData()

        self.searchParams = self.SearchParams(searchStr, searchRoot, nav, preset, graphNodeFilter, functionNodeFilter)
        self.performSearchTimer.start(1)

    def doPerformSearch(self):
        self.performSearchTimer.stop()
        searchCriteria = self.gsuiMgr.prefs.toSearchCriteria()
        searchCriteria.searchString = self.searchParams.searchStr
        searchCriteria.graphNodeFilter = self.searchParams.graphNodeFilter
        searchCriteria.functionNodeFilter = self.searchParams.functionNodeFilter

        # gslog.debug(str(searchCriteria))

        # search presets
        if self.searchParams.preset == GSPresetTypes.SP_PARAM_CUSTOM_FUNC:
            searchCriteria.setupForSSParamFunc()
        elif self.searchParams.preset == GSPresetTypes.SP_TODO or self.searchParams.preset == GSPresetTypes.SP_TMP:
            searchCriteria.caseSensitive = True

        self.searchResults = SearchResults()
        globalSearch = GlobalSearch(sd.getContext(), self.gsuiMgr.prefs, self.searchParams.searchRoot, searchCriteria, self.searchResults)

        globalSearch.search()
        #searchResults.log()

        self.updateWithSearchResults(self.searchResults, searchCriteria)
        
    def updateWithSearchResults(self, searchResults, searchCriteria, handleHistoryAndNav = True):
        self.emptySearchResults()
        self.populateSearchResults(searchResults, searchCriteria)
        if searchResults.hasSearchResults():
            if handleHistoryAndNav:
                if self.searchHistory:
                    if not self.searchParams.isPreset() and self.searchParams.hasSearchString():
                        self.searchHistory.push(self.searchParams.searchStr)

                if not self.searchParams.nav:
                    # search does not come from a navigation prev/next action so append it to nav list
                    self.searchHistory.nav_append(self.searchParams.searchStr, self.curSearchPreset, self.ui.cb_graph_node_type.currentIndex(), self.ui.cb_fct_node_type.currentIndex())
                    self.enableNavButtons()

            self.setStatusResultFound(searchResults.getFoundCount())
        else:
            if self.searchParams:
                self.setNotFoundStatus(self.searchParams.searchStr)

        self.enableSearchResultControls()

    def hasSearchResults(self):
        return self.searchResultTreeWidget.hasSearchResults()
    
    def enableSearchResultControls(self):
        self.enableExpandCollapseButtons()
        hasSearchResults = self.hasSearchResults()
        self.ui.btn_save_sr.setEnabled(hasSearchResults)
        self.ui.btn_focus_sr.setEnabled(hasSearchResults)
        self.ui.btn_prev_sr.setEnabled(hasSearchResults)
        self.ui.btn_next_sr.setEnabled(hasSearchResults)

    def enableExpandCollapseButtons(self):
        treeMode = self.searchResultTreeWidget.displayMode == GSUISearchResultTreeWidget.DM_TREE
        enable = self.hasSearchResults() and treeMode
        self.ui.btn_expand.setEnabled(enable)
        self.ui.btn_collapse.setEnabled(enable)

    def emptySearchResults(self):
        self.searchResultTreeWidget.clearAll()

    def populateSearchResults(self, searchResults, searchCriteria):
        self.searchResultTreeWidget.populate(searchResults, searchCriteria)

    # search history
    def insertSearchHistory(self, index, text, data = GSPresetTypes.SP_NONE):
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
        self.insertSearchHistory(self.searchHistorySeparatorIndex + 1, "Param functions", GSPresetTypes.SP_PARAM_CUSTOM_FUNC)
        self.insertSearchHistory(self.searchHistorySeparatorIndex + 2, "TODO", GSPresetTypes.SP_TODO)
        self.insertSearchHistory(self.searchHistorySeparatorIndex + 3, "TMP", GSPresetTypes.SP_TMP)

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
            self.curSearchPreset = GSPresetTypes.SP_NONE

    def currentSelIsPreset(self):
        index = self.ui.cb_search.currentIndex()
        return index != -1 and self.ui.cb_search.itemData(index) != GSPresetTypes.SP_NONE

    def enableNodeTypeFilters(self):
        self.ui.cb_fct_node_type.setEnabled(self.curSearchPreset != GSPresetTypes.SP_PARAM_CUSTOM_FUNC) # function node type filters are not taken into account when looking for param functions

    def onCurrentIndexChangred(self):
        self.fieldClearedOnPreset = False

        index = self.ui.cb_search.currentIndex()
        if index > self.searchHistorySeparatorIndex:
            self.curSearchPreset = self.ui.cb_search.itemData(index)
        else:
            self.curSearchPreset = GSPresetTypes.SP_NONE

        self.enableNodeTypeFilters()

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
        self.ui.cb_search.insertItem(0, text, GSPresetTypes.SP_NONE)
        self.updateSearchHistorySeparatorIndex()

    def searchHistoryRemoved(self, index):
        self.ui.cb_search.removeItem(index)
        self.updateSearchHistorySeparatorIndex()

    def searchHistoryCleared(self):
        self.ignoreSearchTextChanged = True
        self.ignoreNodeFilterTypeChanged = True
        for _ in range(0, self.searchHistorySeparatorIndex):
            self.ui.cb_search.removeItem(0)
        self.searchHistorySeparatorIndex = 0
        self.ui.cb_search.setCurrentIndex(-1) # reset current index
        self.ignoreSearchTextChanged = False
        self.ignoreNodeFilterTypeChanged = False
        self.onSearchTextOrNodeTypeFilterChanged()

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
