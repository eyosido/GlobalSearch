# ---------------
# Global Search - Substance 3D Designer plugin
# (c) 2019-2022 Eyosido Software SARL
# ---------------

from sd.api.sdgraph import SDGraph
from sd.api.sbs.sdsbsfxmapgraph import SDSBSFxMapGraph
from globalsearch.gscore.sdobj import SDObj
from globalsearch.gscore import gslog
from globalsearch.gscore.gslog import GSLogger

class SearchCriteria:
    """
    Search filters
    """
    def __init__(self, searchString = ""):
        self.searchString = searchString

        # search methods
        self.caseSensitive = False
        self.naturalSearch = True  # Natural search is a "contains" search. If False, search with wildcards is enabled
        self.enterGraphPkgFct = True # enter package functions called from graphs's function params
        self.enterCustomSubGraphs = True # enter custom sub graphs found into the currently searched graph

        # filters
        self.varGetter = True  # variable, getter
        self.varSetter = True  # variale, setter
        self.folderId = True # folder id
        self.graphName = True # graph id or label
        self.graphParamFunc = True # search inside graph parameter functions
        self.funcName = True # function id or label
        self.funcInput = True # function input param id or label
        self.comment = True # comment or frame

        # special searches
        self.ss_param_func = False # return graph parameters to which are associated functions

    def enableFilters(self, enable):
        self.varGetter = enable
        self.varSetter = enable
        self.folderId = enable
        self.graphName = enable
        self.graphParamFunc = enable
        self.funcName = enable
        self.funcInput = enable
        self.comment = enable

    def setupForSSParamFunc(self):
        self.ss_param_func = True
        self.enableFilters(False)

class SearchResultPathNode:
    """
    Node into a tree path leading to a search result
    """
    def __init__(self, sdObj, foundMatch = None, parent = None):
        self.sdObj = sdObj
        self.contextNode = None # optional, provides SDNode context in case sdObj cannot provide it (i.e param functions)
        self.contextString = None # optional, when context is defined by a specific string
        self.subType = SDObj.UNDEFINED   # to characterise some sdObj which cannot be characterized by themselves (i.e. function graph of a pixel processor) 
        self.name = "" # when node represents a named item (i.e. graph input param) whose name cannot be determined with sdObj
        self.foundMatch = foundMatch     # used only if match is found at this node level
        self.parent = parent
        self.children = []

    def hasFoundMatch(self):
        return self.foundMatch != None

    def hasName(self):
        return self.name and len(self.name) > 0

    def isLeaf(self):
        return len(self.children) == 0
    
    def getParentGraphPathNode(self):   
        p = self.parent
        while p:
            if p.sdObj and (isinstance(p.sdObj, SDSBSFxMapGraph) or isinstance(p.sdObj, SDGraph)):
                return p
            else:
                p = p.parent
        return None
    
    def sdObjType(self):
        type = self.subType
        if type == SDObj.UNDEFINED:
            if self.sdObj:
                type,_ = SDObj.type(self.sdObj)
        return type

    def consolidatedName(self):
        type,_ = self.consolidatedType()
        # if self.hasName():
        #     gslog.debug("consolidatedName() hasName " + self.name)
        #     return self.name
        # else:
        #     gslog.debug("consolidatedName() not hasName " + SDObj.name(self.sdObj, type))
        #     return SDObj.name(self.sdObj, type)
        
        return self.name if self.hasName() else SDObj.name(self.sdObj, type)

    def consolidatedType(self):
        if self.subType != SDObj.UNDEFINED:
            type = self.subType
            typeStr = SDObj.typeStrForNonObjType(self.subType)
        else:
            (type,typeStr) = SDObj.type(self.sdObj)
            # gslog.debug("consolidatedType() sdObj="+str(self.sdObj) + " typeStr="+typeStr)
        return (type, typeStr)
            
    def dumpStr(self, dump_match=True, use_indent=True):
        if self.subType == SDObj.UNDEFINED:
            _,typeStr = SDObj.type(self.sdObj)
        else:
            typeStr = SDObj.constantName(self.subType)
        indent = ""
        n = self
        if use_indent:
            while n.parent is not None:
                indent += "    "
                if n.parent is not None:
                    n = n.parent
                else:
                    break

        s = indent + "Type: " + typeStr + " - Name: " + self.consolidatedName()
        if dump_match:
            match = self.foundMatch if self.foundMatch else ""
            s += " - Match: " + match
        return s

    def __str__(self):
        return self.dumpStr()
    
    def logPathNodeBranch(self):
        gslog.info("Node branch (root is last):")
        gslog.info(self.dumpStr(dump_match=False, use_indent=False))
        p = self.parent
        while p:
            gslog.info(p.dumpStr(dump_match=False, use_indent=False))
            p = p.parent

class SearchResults:
    """
    Search results
    """    
    def __init__(self):
        self.pathTree = None
        self.currentPathNode = self.pathTree
        self.foundCount = 0
        self.searchLogs = False
    
    def logSearch(self, s):
        if self.searchLogs:
            gslog.info('[SEARCH] ' + s)

    def hasSearchResults(self):
        return self.pathTree != None

    def getFoundCount(self):
        return self.foundCount

    def incrementFoundCount(self):
        self.foundCount += 1

    # --- Path tree operations
    def appendPathNode(self, sdObj, foundMatchStr = None, isFoundMatch = False, assignToCurrent = True):
        # we are using both foundMatchStr and isFoundMatch as for presets foundMatchStr can be empty
        logSearchStr = "appendPathNode: " + SDObj.dumpStr(sdObj)

        newPathNode = SearchResultPathNode(sdObj, foundMatchStr, self.pathTree)
        if not self.pathTree:
            self.pathTree = newPathNode
        else:
            if self.currentPathNode == None:    # happens when we just left a package which has no parent
                self.currentPathNode = newPathNode
            else:
                newPathNode.parent = self.currentPathNode # don't do this in the above case else we'll create a cycle with parent pointing to self
                self.currentPathNode.children.append(newPathNode)

        if assignToCurrent:
            self.currentPathNode = newPathNode

        if isFoundMatch:
            logSearchStr += ' - match found for "' + foundMatchStr + '" assignToCurrent=' + str(assignToCurrent)
            self.incrementFoundCount()

        self.logSearch(logSearchStr)

        return newPathNode

    def dropCurrentPathBranch(self):
        # gslog.debug("dropCurrentPathBranch, tree before drop:")
        # gslog.debug("self.currentPathNode="+str(self.currentPathNode))
        # gslog.debug("self.currentPathNode.parent="+str(self.currentPathNode.parent))
        # self.log()

        if not self.currentPathNode.parent:
            self.currentPathNode = None
            self.pathTree = None
        else:
            self.currentPathNode.parent.children.remove(self.currentPathNode)
            self.currentPathNode = self.currentPathNode.parent

        # gslog.debug("dropCurrentPathBranch, tree after drop, self.currentPathNode="+str(self.currentPathNode))
        # self.log()

    def setFoundMatchForCurrentPathNode(self, foundMatch):
        if self.currentPathNode: 
            self.currentPathNode.foundMatch = foundMatch
            self.incrementFoundCount()

    # --- debug
    def logTreeStr(self, pathNode):
        gslog.info(pathNode.__str__())
        for child in pathNode.children:
            self.logTreeStr(child)

    def log(self):
        if self.pathTree:
            self.logTreeStr(self.pathTree)

    def leafCount(self, count = 0, pathNode = None):
        curNode = pathNode if pathNode else self.pathTree
        c = count
        if curNode:
            if not curNode.children:
                c += 1
            else:
                for child in curNode.children:
                    c += self.leafCount(count, child)
        return c
