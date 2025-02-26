# ---------------
# Global Search - Substance 3D Designer plugin
# (c) 2019-2022 Eyosido Software SARL
# ---------------

import sd, sys
if sd.getContext().getSDApplication().getVersion() < "14.0.0":
    from PySide2 import QtWidgets
    from PySide2.QtGui import QGuiApplication
    from PySide2.QtCore import Qt
    from PySide2.QtWidgets import QMenu, QAction, QTreeWidgetItemIterator
else:
    from PySide6 import QtWidgets
    from PySide6.QtGui import QGuiApplication, QAction
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QMenu, QTreeWidgetItemIterator

from sd.api.sdnode import SDNode
from sd.api.apiexception import APIException
from globalsearch.gsui.uiutil import GSUIUtil
from globalsearch.gscore.sdobj import SDObj
from globalsearch.gscore.searchdata import SearchResultPathNode
from globalsearch.gscore import gslog

class GSUISearchResultTreeWidget(QtWidgets.QTreeWidget):
    """
    Tree view widget displaying search results
    """
    ICON_HEIGHT = 18

    # Display modes
    DM_TREE = 0
    DM_LIST = 1

    def __init__(self, gsuiMgr, parent=None):
        super().__init__(parent)
        self.gsuiMgr = gsuiMgr
        self.searchResults = None
        self.setDisplayMode(self.__class__.DM_TREE)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.onContextMenu)
        self.resetContextMenuBuffers()

    def idForPathNode(self, pathNode):
        sdNode = None
        ident = None
        if pathNode.contextNode:
            sdNode = pathNode.contextNode
        elif isinstance(pathNode.sdObj, SDNode):
            sdNode = pathNode.sdObj
        if sdNode:
            ident = sdNode.getIdentifier()
        return ident

    def resetContextMenuBuffers(self):
        self.bufferedLocation = None
        self.bufferedFound = None
        self.bufferedId = None
        self.bufferedPathNode = None
        self.bufferedSDNode = None
        self.bufferedGraphViewID = None
        self.bufferedParentGraph = None

    def onContextMenu(self, pos):
        treeItem = self.itemAt(pos)
        menu = QMenu(self)
        self.resetContextMenuBuffers()
        pathNode = treeItem.data(0, Qt.UserRole)
        self.bufferedPathNode = pathNode

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

        # Copy /Jump To Node Id
        if self.bufferedId:
            action = self.createContextMenuItemForTextAtColumn(menu, actionStr, self.bufferedId)
            if action:
                action.triggered.connect(self.onCMCopyId)

        menu.addSection("Navigation")
        if sd.getContext().getSDApplication().getVersion() >= "14.0.0":
            # --- Jump to node
            if self.bufferedPathNode:
                sd_node = None
                if self.bufferedPathNode.contextNode and isinstance(self.bufferedPathNode.contextNode, SDNode):
                    sd_node = self.bufferedPathNode.contextNode # for comments
                elif self.bufferedPathNode.sdObj and isinstance(self.bufferedPathNode.sdObj, SDNode):
                    sd_node = self.bufferedPathNode.sdObj
                
                if sd_node:
                    self.bufferedSDNode = sd_node
                    parentGraphPN = self.bufferedPathNode.getParentGraphPathNode()
                    if parentGraphPN:
                        self.bufferedParentGraph = parentGraphPN.sdObj

                        action = QAction("Show in Graph View", self)
                        action.triggered.connect(self.onCMJumpToNode)
                        menu.addAction(action)

                # open graph or function
                type = self.bufferedPathNode.sdObjType()
                if SDObj.isGraph(type) or SDObj.isFunction(type):
                    action = QAction("Open In Editor", self)
                    action.triggered.connect(self.onCMOpenContainerInEditor)
                    menu.addAction(action)

                # --- Show in Explorer
                if SDObj.isExplorerNode(self.bufferedPathNode.subType):
                    self.bufferedSDNode = self.bufferedPathNode.sdObj
                    action = QAction("Show In Explorer", self)
                    action.triggered.connect(self.onCMShowInExplorer)
                    menu.addAction(action)

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
            action = QAction(actionStr + ' "' + menuText + '"', self)  
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

    def openResourceInEditor(self, resource):
        uiMgr = sd.getContext().getSDApplication().getUIMgr()
        try:
            gslog.info("Opening resource in editor for " + str(resource))
            uiMgr.openResourceInEditor(resource)
        except APIException as e:
            gslog.error("Error opening graph " + str(resource) + ": " + str(e))
            if self.bufferedPathNode:
                self.bufferedPathNode.logPathNodeBranch()

    def onCMJumpToNode(self, checked):
        if sd.getContext().getSDApplication().getVersion() >= "14.0.0":
            if self.bufferedSDNode and self.bufferedParentGraph:
                self.openResourceInEditor(self.bufferedParentGraph)                
                try:
                    graphViewID = GSUIUtil.graphViewIDFromGraph(self.bufferedParentGraph)
                    gslog.info("Getting ViewID for graph " + str(self.bufferedParentGraph) + " graphViewID="+str(graphViewID))
                    if graphViewID:
                        uiMgr = sd.getContext().getSDApplication().getUIMgr()
                        uiMgr.focusGraphNode(graphViewID, self.bufferedSDNode)
                    else:
                        gslog.error("Cannot find open graph for node " + str(self.bufferedSDNode) + ". Parent graph: " + str(self.bufferedParentGraph))
                        self.bufferedPathNode.logPathNodeBranch()
                except APIException as e:
                    gslog.error("Error focusing on node " + str(self.bufferedSDNode) + " in graph " + str(self.bufferedParentGraph) + ": " + str(e))
                    self.bufferedPathNode.logPathNodeBranch()

    def onCMOpenContainerInEditor(self, checked):
        if sd.getContext().getSDApplication().getVersion() >= "14.0.0":
            if self.bufferedPathNode:
                self.openResourceInEditor(self.bufferedPathNode.sdObj)

    def onCMShowInExplorer(self, checked):
        if sd.getContext().getSDApplication().getVersion() >= "14.0.0":
            if self.bufferedSDNode:
                try:
                    uiMgr = sd.getContext().getSDApplication().getUIMgr()
                    uiMgr.setExplorerSelection(self.bufferedSDNode)
                except APIException as e:
                    gslog.error("Error selecting node in Explorer " + str(self.bufferedSDNode) + ": " + str(e))

    def onCMSearchLocation(self, checked):
        self.gsuiMgr.uiWidget.programmaticSearch(self.bufferedLocation)

    def onCMSearchFound(self, checked):
        self.gsuiMgr.uiWidget.programmaticSearch(self.bufferedFound)

    def setDisplayMode(self, displayMode):
        if displayMode == self.__class__.DM_TREE:
            headers = ("Location", "Found", "Node Id")
            enableFlag = False
        else:
            headers = ("Found", "Context", "Node Id", "Path")
            enableFlag = True

        self.setupDisplayMode(displayMode, headers, enableFlag)

    def updateFromPrefs(self):
        prefs = self.gsuiMgr.prefs
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

    # expand or collapse all tree items
    def expandCollapseAllItems(self, expand = False, excludeRoot=True):
        iter = QTreeWidgetItemIterator(self)
        while iter.value():
            treeItem = iter.value()
            hasChildren = treeItem.childCount() > 0

            if not (excludeRoot and treeItem.parent() is None):
                if hasChildren:
                    if expand:
                        self.expandItem(treeItem)
                    else:
                        self.collapseItem(treeItem)

            iter += 1

    # --- Tree display mode

    def populateFromPathNodeTreeDM(self, pathNode, parentItem = None):
        if pathNode.subType == SDObj.ROOT:
            uiTreeItem = None
        else:
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
        
        if len(locationText) == 0:
            locationText = "(no name)"

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
            ident = self.idForPathNode(pathNode)
            if ident:
                treeItem.setText(2, ident)

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
        if pathNode.subType != SDObj.ROOT:
            if pathNode.hasFoundMatch():
                self.createUITreeItemListDM(pathNode, nodeList)

            nodeList.append(pathNode)

        for child in pathNode.children:
            self.populateFromPathNodeListDM(child, nodeList)

        if pathNode.subType != SDObj.ROOT:
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
        ident = self.idForPathNode(pathNode)
        if ident:
            treeItem.setText(2, ident)
            
        # Path
        treeItem.setText(3, self.strFromNodeList(nodeList))
        return treeItem
