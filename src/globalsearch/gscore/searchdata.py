# ---------------
# Global Search - Substance 3D Designer plugin
# (c) 2019-2025 Eyosido Software SARL
# ---------------

import json
from json import JSONEncoder

from sd.api.sdgraph import SDGraph
from sd.api.sbs.sdsbsfxmapgraph import SDSBSFxMapGraph
from globalsearch.gscore.sdobj import SDObj
from globalsearch.gscore import gslog
from globalsearch.gscore.gslog import GSLogger

# Used to tailor a search to a specific node type
class NoteTypeFilterData:
    # This represents either a system node (atomic, function) or library node.
    # Fields definition and type are being used only for system nodes, and 
    # identifier is used only for library nodes.
    # label is being used by both types
    def __init__(self, label, definition, type, identifier):
        self.label = label
        self.definition = definition
        self.type = type
        self.identifier = identifier

    @classmethod
    def fromSystem(cls, label, definition, type):
        return NoteTypeFilterData(label, definition, type, None)
    
    @classmethod
    def fromLibrary(cls, label, identifier):
        return NoteTypeFilterData(label, None, None, identifier)

    def isLibrary(self):
        return self.identifier is not None
    
    def isSystem(self):
        return self.definition is not None
    
    def __str__(self):
        s = "  NoteTypeFilterData:\n"
        s += "   label: " + self.label + "\n"    
        s += "   definition: " + self.definition + "\n"    
        s += "   type: " + str(self.type) + "\n"    
        s += "   identifier: " + self.identifier
        return s

class SearchCriteria:
    """
    Search filters
    """
    def __init__(self, searchString = ""):
        self.searchString = searchString

        # search methods
        self.caseSensitive = False
        self.wholeWord = False
        self.enterGraphPkgFct = False # enter package functions called from graphs's function params
        self.enterCustomSubGraphs = False # enter custom sub graphs found into the currently searched graph

        # filters
        self.varGetter = True  # variable, getter
        self.varSetter = True  # variale, setter
        self.folderId = True # folder id
        self.graphName = True # graph id or label
        self.graphParamFunc = True # search inside graph parameter functions
        self.funcName = True # function id or label
        self.funcInput = True # function input param id or label
        self.comment = True # comment or frame

        # Node type filter
        self.graphNodeFilter = None # NoteTypeFilterData
        self.functionNodeFilter = None # NoteTypeFilterData

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

    def hasSearchString(self):
        return self.searchString and len(self.searchString) > 0
    
    def hasNodeFilter(self):
        return self.graphNodeFilter or self.functionNodeFilter    

    def isGraphNodeFilterMatchingWithTypeAndRefRes(self, nodeType, refRes):
        matching = False
        isSystem = False
        partialMatch = False # set to true when the node is not an actual match but its sub-nodes may be (i.e. looking for a Quadrant and we have an FX-Map, this is not an exact match but we need to dig into the FX-Map to find the Quadrant)
        if self.graphNodeFilter:
            if self.graphNodeFilter.isSystem():
                isSystem = True
                matching = nodeType == self.graphNodeFilter.type
                if not matching:
                    # check for partial match
                    if self.graphNodeFilter.type == SDObj.FX_MAP:
                        # Special case: if graph node filter is FX-Map are we're on an FX-Map node (Quadrant, Switch etc.), then it's a match as we don't need to descend into the FX-Map node (so not partial match)
                        matching = SDObj.isFXMapNode(nodeType)
                    elif SDObj.isFXMapNode(self.graphNodeFilter.type):
                        # Special case: if graph node filter is an FX-Map node (Quadrant etc.) and we're on an FX-Map, this is a partial match so we can enter the FX-Map
                        partialMatch = nodeType == SDObj.FX_MAP
            elif refRes and isinstance(refRes, SDGraph):
                graph_id = refRes.getIdentifier()
                matching = graph_id == self.graphNodeFilter.identifier
        return matching, partialMatch, isSystem

    def isGraphNodeFilterMatching(self, sdNode):
        nodeType, _ = SDObj.type(sdNode)   
        refRes = sdNode.getReferencedResource()
        matching, _, _ = self.isGraphNodeFilterMatchingWithTypeAndRefRes(nodeType, refRes)  
        return matching

    def isFunctionNodeFilterMatchingForDef(self, definitionId):
        matching = False
        if self.functionNodeFilter:
            matching = definitionId == self.functionNodeFilter.definition
        return matching

    def isFunctionNodeFilterMatching(self, sdNode):
        return self.isFunctionNodeFilterMatchingForDef(sdNode.getDefinition().getId())

    def setupForSSParamFunc(self):
        self.ss_param_func = True
        self.enableFilters(False)

    def __str__(self):
        s = "SearchCriteria:\n"
        s += "searchString: " + self.searchString + "\n"

        s += "caseSensitive: " + str(self.caseSensitive) + "\n"
        s += "wholeWord: " + str(self.wholeWord) + "\n"
        s += "enterGraphPkgFct: " + str(self.enterGraphPkgFct) + "\n"
        s += "enterCustomSubGraphs: " + str(self.enterCustomSubGraphs) + "\n"

        s += "varGetter: " + str(self.varGetter) + "\n"
        s += "varSetter: " + str(self.varSetter) + "\n"
        s += "folderId: " + str(self.folderId) + "\n"
        s += "graphName: " + str(self.graphName) + "\n"
        s += "graphParamFunc: " + str(self.graphParamFunc) + "\n"
        s += "funcName: " + str(self.funcName) + "\n"
        s += "funcInput: " + str(self.funcInput) + "\n"
        s += "comment: " + str(self.comment) + "\n"

        if self.graphNodeFilter:
            s += "Graph node filter:\n" + str(self.graphNodeFilter) + "\n"
        else:
            s += "No graph node filter\n"

        if self.functionNodeFilter:
            s += "Function node filter:\n" + str(self.functionNodeFilter) + "\n"
        else:
            s += "No function node filter\n"

        s += "ss_param_func: " + str(self.ss_param_func)
        return s

class SearchResultPathNode:
    """
    Node into a tree path leading to a search result
    """
    def __init__(self, sdObj, foundMatch = None, parent = None):
        self.sdObj = sdObj
        self.contextNode = None # optional, provides SDNode context in case sdObj cannot provide it (i.e param functions)
        self.contextString = None # optional, when context is defined by a specific string
        self.referencedRes = None # optional, referenced resource (graph or function) in case a node references a sub-graph or a package function
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
        type, typeStr = self.consolidatedType()
        # if self.hasName():
        #     gslog.debug("consolidatedName() hasName " + self.name)
        #     return self.name
        # else:
        #     gslog.debug("consolidatedName() not hasName " + SDObj.name(self.sdObj, type))
        #     return SDObj.name(self.sdObj, type)
        
        name = self.name if self.hasName() else SDObj.name(self.sdObj, type)
        if not name or len(name)==0:
            name = typeStr
        return name

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

# this is used for unit tests in order to make test results serializable
class SearchResultPathNodeJSONEncoder(JSONEncoder):
    def default(self, pathNode):
        type, typeStr = SDObj.type(pathNode.sdObj)
        name = pathNode.name if pathNode.name and len(pathNode.name) > 0 else SDObj.name(pathNode.sdObj, type)
        foundMatch = pathNode.foundMatch
        children = None
        if pathNode.children and len(pathNode.children) > 0:
            children = []
            for c in pathNode.children:
                children.append(self.default(c))

        result = {"type":typeStr, "name":name}
        if foundMatch:
            result["foundMatch"] = foundMatch
        if children:
            result["children"] = children

        return result

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
        logSearchStr = "appendPathNode: " + SDObj.dumpStr(sdObj) + " isFoundMatch=" + str(isFoundMatch) + " assignToCurrent="+str(assignToCurrent)

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
