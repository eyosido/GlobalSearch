# ---------------
# Global Search - Substance 3D Designer plugin
# (c) 2019-2022 Eyosido Software SARL
# ---------------

from pathlib import Path

import sd
if sd.getContext().getSDApplication().getVersion() < "14.0.0":
    from PySide2 import QtWidgets
    from PySide2.QtCore import Signal
    from PySide2.QtWidgets import QTreeWidgetItemIterator, QSizePolicy
else:
    from PySide6 import QtWidgets
    from PySide6.QtCore import Signal
    from PySide6.QtWidgets import QTreeWidgetItemIterator, QSizePolicy

from sd.api.sdpackage import SDPackage
from sd.api.sdgraph import SDGraph
from sd.api.sdresourcefolder import SDResourceFolder

from globalsearch.gscore import gslog
from globalsearch.gscore.sdobj import SDObj
from globalsearch.gsui.uiutil import GSUIUtil

class GSUISearchRootTreeWidget(QtWidgets.QTreeWidget):
    """
    Tree view widget displaying potential search roots
    """
    searchRootChanged = Signal(int)
    
    MAX_VISIBLE_ITEM_COUNT = 20
    ICON_HEIGHT = 18

    def __init__(self, parent=None):
        super().__init__(parent)
        self.treeItemRoot = None
        self.treeMapping = {} # dictionnary mapping tree QTreeWidgetItem and CustomTreeData. Key:id(treeItem), value:CustomTreeData 
        self.isExpandCollapse = False
        self.setHeaderHidden(True)
        self.itemCollapsed.connect(self.onItemCollapsed)
        self.itemExpanded.connect(self.onItemExpanded)
        self.itemClicked.connect(self.onItemClicked)

    # --- Public
    def populate(self):
        self.clear()
        self.setupTreeItemRoot()
        ctx = sd.getContext()
        pkgMgr = ctx.getSDApplication().getPackageMgr()
        packages = pkgMgr.getUserPackages()
        for p in range(0, packages.getSize()):
            pkg = packages.getItem(p)
            self.populateFromPackage(pkg, self.treeItemRoot)

    # --- slots    
    def onItemCollapsed(self, item):
        self.expandedOrCollapsed(item)

    def onItemExpanded(self, item):
        self.expandedOrCollapsed(item)

    def onItemClicked(self, item):
        self.searchRootChanged.emit(item)

    # --- Private
    class CustomTreeData():
        def __init__(self, sdObj = None):
            if sdObj:
                self.entryType,_ = SDObj.type(sdObj)
                self.name = SDObj.name(sdObj, self.entryType)
                # gslog.debug("CustomTreeData() sdObj="+str(sdObj) + " entryType="+str(self.entryType) + " name="+self.name)
            else:
                self.entryType = SDObj.ROOT
                self.name = "Everything (hit Refresh button to update)"
               
            self.sdObj = sdObj

        def __str__(self):
            return "entryType: " + str(self.entryType) + " name: " + self.name

    def setupTreeItemRoot(self):
        self.treeItemRoot = self.createUITreeItem(self.CustomTreeData())

    def expandedOrCollapsed(self, item):
        self.isExpandCollapse = True
        self.resizeTreeHeightBasedOnItemCount(int(self.__class__.ICON_HEIGHT*1.4))    # constant row height whether icons are present or not

    def resizeTreeHeightBasedOnItemCount(self, rowHeight):
        # size tree view to the number of non-collapsed items
        count = self.visibleItemCount()
        if count > self.__class__.MAX_VISIBLE_ITEM_COUNT:
            count = self.__class__.MAX_VISIBLE_ITEM_COUNT
        newHeight = rowHeight * count
        self.setMinimumHeight(newHeight)

    def name(self, sdObj):
        name = ""
        if isinstance(sdObj, SDPackage):
            name = Path(sdObj.getFilePath()).stem
        else:
            name = sdObj.getIdentifier()
        return name

    def customDataFromTreeItem(self, treeItem):
        return self.treeMapping[id(treeItem)]

    def populateFromPackage(self, package, parentUITreeItem):
        customTreeData = self.CustomTreeData(package)
        uiTreeItem = self.createUITreeItem(customTreeData, parentUITreeItem)

        resources = package.getChildrenResources(False)
        if resources:
            for r in range(0, resources.getSize()):
                resource = resources.getItem(r)
                self.populateFrom(resource, uiTreeItem)

    def populateFrom(self, sdObj, parentUITreeItem):
        if isinstance(sdObj, SDGraph):
            customTreeData = self.CustomTreeData(sdObj)
            self.createUITreeItem(customTreeData, parentUITreeItem)
        elif isinstance(sdObj, SDResourceFolder):
            self.populateFromFolder(sdObj, parentUITreeItem)

    def populateFromFolder(self, folder, parentUITreeItem):
        customTreeData = self.CustomTreeData(folder)
        uiTreeItem = self.createUITreeItem(customTreeData, parentUITreeItem)

        resources = folder.getChildren(False)
        if resources:
            for r in range(0, resources.getSize()):
                resource = resources.getItem(r)
                self.populateFrom(resource, uiTreeItem)

    def createUITreeItem(self, customTreeData, parentItem=None):
        if parentItem:
            treeItem = QtWidgets.QTreeWidgetItem(parentItem)
        else:
            treeItem = QtWidgets.QTreeWidgetItem(self)

        text = customTreeData.name
        if len(text) == 0:
            text = "(no name)"
            
        treeItem.setText(0, text)
        icon = GSUIUtil.iconForSDObj(customTreeData.entryType, self.__class__.ICON_HEIGHT)
        if icon:
            treeItem.setIcon(0, icon)

        self.treeMapping[id(treeItem)] = customTreeData
        return treeItem

    def visibleItemCount(self):
        count = 0
        iter = QTreeWidgetItemIterator(self)
        while iter.value():
            parentItem = iter.value().parent()
            if not (parentItem and not parentItem.isExpanded()):
                count += 1
            iter += 1
        return count

class GSUIComboTreeWidget(QtWidgets.QComboBox):
    """
    A combo box displaying a tree view as dropdown popup
    """
    doActivate = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.treeWidget = GSUISearchRootTreeWidget(self)
        self.treeWidget.populate()
        self.setModel(self.treeWidget.model())
        self.setView(self.treeWidget)
        self.activated.connect(self.onActivated) #custom signal to be able to send the system's activate signal
        self.setCurrentIndex(0)
        self.setMaxVisibleItems(GSUISearchRootTreeWidget.MAX_VISIBLE_ITEM_COUNT)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed))
    
    def onActivated(self, index):
        pass

    def reload(self):
        self.clear()
        self.treeWidget.populate()
    
    def hidePopup(self):
        if not self.treeWidget.isExpandCollapse:
            super().hidePopup()
        else:
            # prevent popup from closing by not calling base class implementation
            self.doActivate.emit(0)
        self.treeWidget.isExpandCollapse = False
