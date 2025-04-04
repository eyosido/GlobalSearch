# ---------------
# Global Search - Substance 3D Designer plugin
# (c) 2019-2025 Eyosido Software SARL
# ---------------

import sd, sys
if sd.getContext().getSDApplication().getVersion() < "14.0.0":
    from PySide2 import QtWidgets
    from PySide2.QtGui import QGuiApplication
    from PySide2.QtCore import Qt
    from PySide2.QtWidgets import QMenu, QAction, QTreeWidgetItemIterator, QMessageBox
else:
    from PySide6 import QtWidgets
    from PySide6.QtGui import QGuiApplication, QAction
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QMenu, QTreeWidgetItemIterator, QMessageBox

from sd.api.sdnode import SDNode
from sd.api.apiexception import APIException
from sd.api.sdapiobject import SDApiError
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
        self.rootCount = 0
        self.setDisplayMode(self.__class__.DM_TREE)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.onContextMenu)
        self.resetContextMenuBuffers()

        if sd.getContext().getSDApplication().getVersion() >= "14.0.0":
            self.itemDoubleClicked.connect(self.onItemDoubleClicked)   

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

        # check if selected is still valid
        if not self.isObjectValid(pathNode.sdObj):
            QMessageBox.warning(self, self.gsuiMgr.APPNAME, "This object does not exist anymore.")
            return

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
                sdNode, sdParentGraph = self.nodeForShowing(self.bufferedPathNode)
                if sdNode and sdParentGraph:
                    self.bufferedSDNode = sdNode
                    self.bufferedParentGraph = sdParentGraph
                    action = QAction("Show in Graph View", self)
                    action.triggered.connect(self.onCMJumpToNode)
                    menu.addAction(action)

                # open graph or function
                if self.containerForOpening(self.bufferedPathNode):
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

    # given a pathNode, check if it can be shown in a graph view. If so, returns the sdNode and its parent graph
    def nodeForShowing(self, pathNode):
        sdNode = None
        sdParentGraph = None
        if pathNode.contextNode and isinstance(pathNode.contextNode, SDNode):
            sdNode = pathNode.contextNode # for comments
        elif pathNode.sdObj and isinstance(pathNode.sdObj, SDNode):
            sdNode = pathNode.sdObj
        
        if sdNode:
            self.bufferedSDNode = sdNode
            parentGraphPN = pathNode.getParentGraphPathNode()
            if parentGraphPN:
                sdParentGraph = parentGraphPN.sdObj

        return (sdNode, sdParentGraph)
    
    # given a pathNode, check if it can be opened as a graph, if so return the sd graph
    def containerForOpening(self, pathNode):
        sdContainer = None
        type = pathNode.sdObjType()
        if SDObj.isGraph(type) or SDObj.isFunction(type):
            sdContainer = pathNode.sdObj
        return sdContainer
    
    def openOrFocusOnItemIfPossible(self, item):
        if sd.getContext().getSDApplication().getVersion() >= "14.0.0":
            if item and item.childCount() == 0: # check if leaf
                pathNode = item.data(0, Qt.UserRole)
                sdNode, sdParentGraph = self.nodeForShowing(pathNode)
                if sdNode and sdParentGraph:
                    self.jumpToNode(sdNode, sdParentGraph, pathNode)
                else:
                    if self.containerForOpening(pathNode):
                        self.openContainerInEditor(pathNode)

    def onItemDoubleClicked(self, item, column):
        self.openOrFocusOnItemIfPossible(item)

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

    def isObjectValid(self, obj):
        valid = True
        try:
            if isinstance(obj, SDNode):
                if obj.getDefinition() is None:
                    raise APIException(SDApiError(SDApiError.Undefined))
            elif hasattr(obj, 'getFilePath') and callable(obj.getFilePath): # SDResource, SDPackage
                    obj.getFilePath() # raises an exception if object has been deleted
        except APIException as e:
            valid = False
        return valid
            
    def openResourceInEditor(self, resource, pathNode):
        uiMgr = sd.getContext().getSDApplication().getUIMgr()
        try:
            gslog.info("Opening resource in editor for " + str(resource))
            uiMgr.openResourceInEditor(resource)
        except APIException as e:
            gslog.error("Error opening graph " + str(resource) + ": " + str(e))
            if pathNode:
                try:
                    pathNode.logPathNodeBranch()
                except APIException as ee:
                    pass # exception may be raised if objects along the path do not exist anymore

    def openContainerInEditor(self, pathNode):
        if pathNode:
            obj = pathNode.referencedRes if pathNode.referencedRes else pathNode.sdObj
            if self.isObjectValid(obj):
                self.openResourceInEditor(obj, pathNode)
            else:
                gslog.warning("Attempt to open in editor an object does not exist anymore.")
                QMessageBox.warning(self, self.gsuiMgr.APPNAME, "This object does not exist anymore.")

    def onCMOpenContainerInEditor(self, checked):
        self.openContainerInEditor(self.bufferedPathNode)

    def jumpToNode(self, sdNode, sdParentGraph, pathNode):
        if sd.getContext().getSDApplication().getVersion() >= "14.0.0":
            if sdNode and sdParentGraph:
                if self.isObjectValid(sdParentGraph):
                    self.openResourceInEditor(sdParentGraph, pathNode)              
                else:
                    gslog.warning("Attempt to open in editor an graph does not exist anymore.")
                    QMessageBox.warning(self, self.gsuiMgr.APPNAME, "Parent graph for this object does not exist anymore.")
                    return
                try:
                    graphViewID = GSUIUtil.graphViewIDFromGraph(sdParentGraph)
                    gslog.info("Getting ViewID for graph " + str(sdParentGraph) + " graphViewID="+str(graphViewID))
                    if graphViewID:
                        uiMgr = sd.getContext().getSDApplication().getUIMgr()
                        gslog.info("Focusing on graph node " + str(sdNode) + " in graphViewID="+str(graphViewID))
                        uiMgr.focusGraphNode(graphViewID, sdNode)
                    else:
                        gslog.error("Cannot find open graph for node " + str(sdNode) + ". Parent graph: " + str(sdParentGraph))
                        pathNode.logPathNodeBranch()
                except APIException as e:
                    gslog.error("Error focusing on node " + str(sdNode) + " in graph " + str(sdParentGraph) + ": " + str(e))
                    pathNode.logPathNodeBranch()

    def onCMJumpToNode(self, checked):
        self.jumpToNode(self.bufferedSDNode, self.bufferedParentGraph, self.bufferedPathNode)

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
        self.header().setSectionHidden(2, not prefs.sp_displayNodeIds)

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
        self.rootCount = 0

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
        self.rootCount = self.countRoots()

    def countRoots(self):
        iter = QTreeWidgetItemIterator(self)
        root_count = 0
        while iter.value():
            treeItem = iter.value()
            if treeItem.parent() is None:
                root_count += 1
            iter += 1
        return root_count

    # expand or collapse all tree items
    def expandCollapseAllItems(self, expand = False, excludeRoot=True):
        iter = QTreeWidgetItemIterator(self)
        while iter.value():
            treeItem = iter.value()
            hasChildren = treeItem.childCount() > 0

            # we do not collapse the root of a tree having a single root (for reasability) excludeRoot if True
            if not (excludeRoot and (treeItem.parent() is None) and (self.rootCount == 1) and not expand):
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
    
    def hasSearchResults(self):
        return self.topLevelItemCount() > 0

    # returns the item in tree having a found match following or preceding item
    def navFoundItem(self, next, item):
        if item:
            iter = QTreeWidgetItemIterator(item)
            cur_item = iter.value()            
            while cur_item: # this loop won't go infinite as there always is at least one found match
                if next:
                    iter += 1
                    if iter.value() is None:
                        iter = QTreeWidgetItemIterator(self.navFirstTreeItem()) # cycle to top item
                else:
                    iter -= 1
                    if iter.value() is None:
                        iter = QTreeWidgetItemIterator(self.navLastTreeItem()) # cycle to last item

                cur_item = iter.value()
                if cur_item:
                    if self.navIsFoundItem(cur_item):
                        return cur_item
        return None
    
    def navIsFoundItem(self, item):
        if item:
            pathNode = item.data(0, Qt.UserRole)
            # Note: nodes found by node type filetering only (i.e. no search string) have foundMatch set to "" (=match without using string) which differenciates them from None (=no match)
            if pathNode.foundMatch is not None:
                return True
        return False
    
    def navNextFoundItem(self):
        return self.navFoundItem(next=True)
                    
    def navPrevFoundItem(self):
        return self.navFoundItem(next=False)
    
    def navFirstTreeItem(self):
        return QTreeWidgetItemIterator(self).value()
    
    def navLastTreeItem(self):
        iter = QTreeWidgetItemIterator(self)
        item = None
        while iter.value():
            item = iter.value()            
            iter += 1
        return item


    

