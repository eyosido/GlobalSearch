# ---------------
# Global Search - Substance 3D Designer plugin
# (c) 2019-2022 Eyosido Software SARL
# ---------------

from PySide2 import QtWidgets
from PySide2.QtGui import QGuiApplication
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QMenu, QAction

from sd.api.sdnode import SDNode

from globalsearch.gsui.uiutil import GSUIUtil
from globalsearch.gscore.sdobj import SDObj
from globalsearch.gscore.searchdata import SearchResultPathNode
from globalsearch.gsui.prefs import GSUIPref

from sd.api.sdnode import SDNode

class GSUISearchResultTreeWidget(QtWidgets.QTreeWidget):
    """
    Tree view widget displaying search results
    """
    ICON_HEIGHT = 18

    # Display modes
    DM_TREE = 0
    DM_LIST = 1

    def __init__(self, parent=None):
        super().__init__(parent)
        self.searchResults = None
        self.setDisplayMode(self.__class__.DM_TREE)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.onContextMenu)
        self.resetContextMenuBuffers()

    def idForPathNode(self, pathNode):
        sdNode = None
        id = None
        if pathNode.contextNode:
            sdNode = pathNode.contextNode
        elif isinstance(pathNode.sdObj, SDNode):
            sdNode = pathNode.sdObj
        if sdNode:
            id = sdNode.getIdentifier()
        return id

    def resetContextMenuBuffers(self):
        self.bufferedLocation = None
        self.bufferedFound = None
        self.bufferedId = None

    def onContextMenu(self, pos):
        treeItem = self.itemAt(pos)
        menu = QMenu(self)
        self.resetContextMenuBuffers()
        pathNode = treeItem.data(0, Qt.UserRole)

        # --- gather text items

        # Location column
        if self.displayMode == self.__class__.DM_TREE:
            useLocation = True

            if pathNode.subType == SDObj.FUNC_CALL:
                useLocation = False
            elif isinstance(pathNode.sdObj, SDNode):
                defId = pathNode.sdObj.getDefinition().getId()
                # we ignore Get/Set Location text for getters and setters
                if defId.startswith("sbs::function::get") or defId.startswith("sbs::function::set"):
                    useLocation = False

            if useLocation:
                self.bufferedLocation = pathNode.consolidatedName()

        # Found column
        self.bufferedFound = pathNode.foundMatch

        # node Id
        self.bufferedId = self.idForPathNode(pathNode)

        # --- Copy menu items
        menu.addSection("Copy")
        actionStr = "Copy"

        # Copy Location
        action = self.createContextMenuItemForTextAtColumn(menu, actionStr, self.bufferedLocation)
        if action:
            action.triggered.connect(self.onCMCopyLocation)

        # Copy Found
        if self.bufferedFound != self.bufferedLocation:
            action = self.createContextMenuItemForTextAtColumn(menu, actionStr, self.bufferedFound)
            if action:
                action.triggered.connect(self.onCMCopyFound)

        # Copy Node Id
        if self.bufferedId:
            action = self.createContextMenuItemForTextAtColumn(menu, actionStr, self.bufferedId)
            if action:
                action.triggered.connect(self.onCMCopyId)

        # --- Search actions
        menu.addSection("Search")
        actionStr = "Search"

        # Search Location
        action = self.createContextMenuItemForTextAtColumn(menu, actionStr, self.bufferedLocation)
        if action:
            action.triggered.connect(self.onCMSearchLocation)

        # Search Found
        if self.bufferedFound != self.bufferedLocation:
            action = self.createContextMenuItemForTextAtColumn(menu, actionStr, self.bufferedFound)
            if action:
                action.triggered.connect(self.onCMSearchFound)

        menu.exec_(self.mapToGlobal(pos))

    def createContextMenuItemForTextAtColumn(self, menu, actionStr, text):
        action = None
        if text and len(text) > 0:
            menuText = GSUIUtil.croppedText(text)
            self.textToCopyIntoClipboard = text
            action = QAction(actionStr + " " + menuText, self)  
            menu.addAction(action)
        return action
    
    def onCMCopyLocation(self, checked):
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(self.bufferedLocation)

    def onCMCopyFound(self, checked):
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(self.bufferedFound)

    def onCMCopyId(self, checked):
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(self.bufferedId)

    def onCMSearchLocation(self, checked):
        from globalsearch.gsui.gsuimgr import GSUIManager
        GSUIManager.uiWidget.programmaticSearch(self.bufferedLocation)

    def onCMSearchFound(self, checked):
        from globalsearch.gsui.gsuimgr import GSUIManager
        GSUIManager.uiWidget.programmaticSearch(self.bufferedFound)

    def setDisplayMode(self, displayMode):
        if displayMode == self.__class__.DM_TREE:
            headers = ("Location", "Found", "Node Id")
            enableFlag = False
        else:
            headers = ("Found", "Context", "Node Id", "Path")
            enableFlag = True

        self.setupDisplayMode(displayMode, headers, enableFlag)

    def updateFromPrefs(self):
        from globalsearch.gsui.gsuimgr import GSUIManager
        prefs = GSUIManager.prefs
        self.header().setSectionHidden(2, not prefs.sp_display_node_ids)

    def setupDisplayMode(self, displayMode, headers, enableFlag):
        header = self.header()
        header.reset()
        self.setHeaderLabels(headers)
        self.displayMode = displayMode
        self.setHeaderResizeMode(QtWidgets.QHeaderView.ResizeToContents)

        self.setSortingEnabled(enableFlag)
        header.setSortIndicatorShown(enableFlag)
        header.setSectionsClickable(enableFlag)
        header.setSectionHidden(3, not enableFlag) # show/hide last column (Path)

        if self.searchResults:
            self.clear()
            self.doPopulate()

    def clearAll(self):
        self.clear()
        self.searchResults = None

    def setHeaderResizeMode(self, resizeMode):
        header = self.header()
        for s in range (0, header.count()):
            header.setSectionResizeMode(s, resizeMode)

    def populate(self, searchResults, searchCriteria):
        self.searchResults = searchResults
        self.searchCriteria = searchCriteria
        self.doPopulate()

    def doPopulate(self):
        self.setHeaderResizeMode(QtWidgets.QHeaderView.Interactive) # doing this at init time does not create even columns
        pathNode = self.searchResults.pathTree
        if pathNode:
            if self.displayMode == self.__class__.DM_TREE:
                self.populateFromPathNodeTreeDM(pathNode)
                self.expandAll()
            else:
                nodeList = []
                self.populateFromPathNodeListDM(pathNode, nodeList)
                
        self.header().resizeSections(QtWidgets.QHeaderView.ResizeToContents) # adapts headers to new context

    # --- Tree display mode

    def populateFromPathNodeTreeDM(self, pathNode, parentItem = None):
        uiTreeItem = self.createUITreeItemTreeDM(pathNode, parentItem)
        for child in pathNode.children:
            self.populateFromPathNodeTreeDM(child, uiTreeItem)

    def createUITreeItemTreeDM(self, pathNode, parentItem = None):
        if parentItem:
            treeItem = QtWidgets.QTreeWidgetItem(parentItem)
        else:
            treeItem = QtWidgets.QTreeWidgetItem(self)

        treeItem.setData(0, Qt.UserRole, pathNode)

        type,_ = pathNode.consolidatedType()

        # Location: name + icon
        if type == SDObj.FUNC_PARAM and self.searchCriteria.ss_param_func:
            locationText = "Parameter function"
            icon = GSUIUtil.iconForSDObj(SDObj.FUNC_PARAM, self.__class__.ICON_HEIGHT)
        elif pathNode.subType == SDObj.FUNC_CALL:
            locationText = "Function call"
            icon = GSUIUtil.iconForSDObj(SDObj.FUNC_CALL, self.__class__.ICON_HEIGHT)
        else:
            locationText = GSUIUtil.croppedText(pathNode.consolidatedName())   
            icon = GSUIUtil.iconForSDObj(type, self.__class__.ICON_HEIGHT)

        treeItem.setText(0, locationText)
        if icon:
            treeItem.setIcon(0, icon)

        # Found
        foundText = None
        if type == SDObj.FUNC_PARAM and self.searchCriteria.ss_param_func:
            # special search, search all param functions, there is no string match
            # in this case so we set the location name in the Found column 
            foundText = GSUIUtil.croppedText(pathNode.consolidatedName())
            icon = GSUIUtil.iconForSDObj(SDObj.FUNC_PARAM, self.__class__.ICON_HEIGHT)
            if icon:
                treeItem.setIcon(1, icon)
        elif pathNode.hasFoundMatch():
            foundText = GSUIUtil.croppedTextCenteredAroundSubstring(self.searchCriteria.searchString, pathNode.foundMatch)
            if pathNode.subType == SDObj.FUNC_CALL:
                icon = GSUIUtil.iconForSDObj(SDObj.FUNC_CALL, self.__class__.ICON_HEIGHT)
                if icon:
                    treeItem.setIcon(1, icon)
        
        if foundText:
            treeItem.setText(1, foundText)

        # ID
        if pathNode.subType != SDObj.FUNC_PARAM:
            id = self.idForPathNode(pathNode)
            if id:
                treeItem.setText(2, id)

        return treeItem

    # --- List display mode
    def strFromNodeList(self, nodeList):
        s = ""
        size = len(nodeList)
        for n in range(0, size):
            node = nodeList[n]
            _,typeStr = SDObj.type(node.sdObj)
            s += typeStr.upper() + ": " +  node.consolidatedName()
            if n < size-1:
                s += " > "
        return s

    def populateFromPathNodeListDM(self, pathNode, nodeList):
        if pathNode.hasFoundMatch():
            self.createUITreeItemListDM(pathNode, nodeList)

        nodeList.append(pathNode)
        for child in pathNode.children:
            self.populateFromPathNodeListDM(child, nodeList)
        nodeList.pop()

    def createUITreeItemListDM(self, pathNode, nodeList):
        treeItem = QtWidgets.QTreeWidgetItem(self)
        treeItem.setData(0, Qt.UserRole, pathNode)

        # Found
        if self.searchCriteria.ss_param_func:
            # special search, search all param functions, there is no string match
            # in this case so we set the location name in the Found column 
            foundText = GSUIUtil.croppedText(pathNode.consolidatedName())
        else:
            foundText = GSUIUtil.croppedTextCenteredAroundSubstring(self.searchCriteria.searchString, pathNode.foundMatch)

        treeItem.setText(0, foundText)

        typeStr = ""
        if pathNode.subType == SDObj.FUNC_CALL:
            type = SDObj.FUNC_CALL
        else:
            type, typeStr = pathNode.consolidatedType()

        icon = GSUIUtil.iconForSDObj(type, self.__class__.ICON_HEIGHT)
        if icon:
            treeItem.setIcon(0, icon)

        # Context
        context = ""
        if self.searchCriteria.ss_param_func:
            if pathNode.contextNode:
                if pathNode.contextString:
                    context = pathNode.contextString
                else:
                    tempPathNode = SearchResultPathNode(pathNode.contextNode)
                    context = tempPathNode.consolidatedName()
                icon = GSUIUtil.iconForSDObj(SDObj.GRAPH_NODE, self.__class__.ICON_HEIGHT)
                if icon:
                    treeItem.setIcon(1, icon)
        elif pathNode.contextString:
            context = pathNode.contextString
        else:
            context = typeStr.capitalize()
            
        treeItem.setText(1, context)

        # ID
        id = self.idForPathNode(pathNode)
        if id:
            treeItem.setText(2, id)
            
        # Path
        treeItem.setText(3, self.strFromNodeList(nodeList))
        return treeItem
