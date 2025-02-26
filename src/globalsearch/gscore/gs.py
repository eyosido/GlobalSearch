# ---------------
# Global Search - Substance 3D Designer plugin
# (c) 2019-2022 Eyosido Software SARL
# ---------------

from sd.api.sdpackage import SDPackage
from sd.api.sdgraph import SDGraph
from sd.api.sbs.sdsbsfunctiongraph import SDSBSFunctionGraph
from sd.api.sdproperty import SDPropertyCategory
from sd.api.sdtypefloat import *
from sd.api.sdvaluefloat import *
from sd.api.sdnode import SDNode
from sd.api.sdvaluestring import SDValueString
from sd.api.sdresourcefolder import SDResourceFolder
from sd.api.sdgraphobjectcomment import SDGraphObjectComment
from sd.api.sdgraphobjectframe import SDGraphObjectFrame

from globalsearch.gscore import gslog
from globalsearch.gscore.sdobj import SDObj 

class GlobalSearch:
    """
    Main search class
    """ 
    VERSION = "1.4.3"

    def __init__(self, ctx, searchRoot, searchCriteria, searchResults):
        self.context = ctx
        self.searchRoot = searchRoot
        self.searchCriteria = searchCriteria
        self.searchResults = searchResults
        self.searchLogs = False # enable to log information about the search (debug only)
        self.searchResults.searchLogs = self.searchLogs
        self.depth = 0  # tree depth, used mostly for debugging

    # -------- Public
    def search(self):
        self.depth = 0
        self.searchInto(self.searchRoot)

    def logSearch(self, s):
        if self.searchLogs:
            gslog.debug('[SEARCH]' + s)

    # -------- Private
    def isContainerNode(self, sdObj):
        return sdObj == None or isinstance(sdObj, SDPackage) or isinstance(sdObj, SDGraph) \
            or isinstance(sdObj, SDResourceFolder)

    def pathEnterContainer(self, sdContainerObj):
        self.logSearch("pathEnterContainer: " + SDObj.dumpStr(sdContainerObj))
        return self.searchResults.appendPathNode(sdContainerObj)
    
    def pathLeaveContainer(self, containerPathNode, foundSearchResult):
        self.logSearch("pathLeaveContainer: " + SDObj.dumpStr(containerPathNode))
        if not foundSearchResult:
            self.searchResults.currentPathNode = containerPathNode   # restore currentPathNode
            self.logSearch("Dropping current branch")
            self.searchResults.dropCurrentPathBranch()
        
        self.searchResults.currentPathNode = containerPathNode.parent   # we're done with this container, move to parent

    def searchInto(self, sdObj, subType = SDObj.ROOT, name = ""):
        self.logSearch("searchInto " + SDObj.dumpStr(sdObj) + " depth="+str(self.depth))
        if sdObj == None:
            # we need to have root node when searching over multiple packages
            containerPathNode = self.pathEnterContainer(sdObj)
            containerPathNode.subType = SDObj.ROOT
            containerPathNode.name = "Root"
            foundSearchResult = self.searchPackages()
            self.pathLeaveContainer(containerPathNode, foundSearchResult)
        else:
            containerPathNode = self.pathEnterContainer(sdObj)
            self.depth += 1
            containerPathNode.subType = subType
            containerPathNode.name = name

            foundSearchResult = False
            if isinstance(sdObj, SDPackage):
                foundSearchResult = self.searchPackage(sdObj)
            elif isinstance(sdObj, SDSBSFunctionGraph):
                foundSearchResult = self.searchFunctionGraph(sdObj)
            elif isinstance(sdObj, SDGraph):
                foundSearchResult = self.searchGraph(sdObj)
            elif isinstance(sdObj, SDResourceFolder):
                foundSearchResult = self.searchFolder(sdObj)
            else:
                gslog.warning("Nothing to search into, this is not a container")

            self.pathLeaveContainer(containerPathNode, foundSearchResult)
            self.depth -= 1

        return foundSearchResult

    def searchPackages(self):
        self.logSearch("searchPackages ")
        foundSearchResult = False
        app = self.context.getSDApplication()
        packages = app.getPackageMgr().getUserPackages()
        if packages:
            count = packages.getSize()
            self.logSearch("searchPackages found " + str(count) + ' packages')
            for p in range(0, count):
                package = packages.getItem(p)
                if self.searchInto(package, subType=SDObj.PACKAGE):
                    foundSearchResult = True
        return foundSearchResult

    def searchPackage(self, package):
        self.logSearch("searchPackage " + SDObj.dumpStr(package))
        foundSearchResult = False
        resources = package.getChildrenResources(False)
        if resources:
            count = resources.getSize()
            self.logSearch("searchPackage found " + str(count) + ' resources')
            for r in range(0, count):
                resource = resources.getItem(r)
                subType, _ = SDObj.type(resource)
                if self.isContainerNode(resource) and self.searchInto(resource, subType=subType):
                    foundSearchResult = True

        return foundSearchResult

    def searchGraph(self, graph):
        self.logSearch("searchGraph " + SDObj.dumpStr(graph))
        foundSearchResult = False

        # search graph name
        if self.searchCriteria.graphName:
            [ident, label] = self.getIdAndLabelFromProperties(graph)
            match = self.getMatchingIdOrLabel(ident, label)
            if match:
                self.searchResults.setFoundMatchForCurrentPathNode(match)
                foundSearchResult = True

        # search comments and frames
        if self.searchCriteria.comment:
            if self.searchGraphObjects(graph):
                foundSearchResult = True

        # search graph param functions and subgraphs
        nodes = graph.getNodes()
        self.logSearch("searchGraph: parsing graph nodes")
        for n in range(0, nodes.getSize()):
            node = nodes.getItem(n)
            nodeType,_ = SDObj.type(node)   

            self.logSearch("searchGraph: current node: " + SDObj.dumpStr(node))

            containerPathNode_lev2 = self.pathEnterContainer(node)
            foundSearchResult_lev2 = False

            # search identifier
            identifier = node.getIdentifier()
            self.logSearch("searchGraph: node id="+identifier)
            if self.searchCriteria.searchString == identifier:
                self.logSearch("searchGraph: found id match")
                foundSearchResult_lev2 = True

            # search graph params functions in input properties
            self.logSearch("searchGraph: searching param functions for current node")
            properties = node.getProperties(SDPropertyCategory.Input)
            if properties:
                p = 0
                psize = properties.getSize()
                while p < psize:
                    prop = properties.getItem(p)
                    propGraph = node.getPropertyGraph(prop)
                    functionOnly = prop.isFunctionOnly()

                    self.logSearch("searchGraph: prop=" + str(prop) + " propGraph="+str(propGraph) + " functionOnly="+str(functionOnly))

                    if propGraph and not functionOnly:  # the Pixel Processor function is "function-only", we'll treat it below in the hasSystemContent case
                        self.logSearch("searchGraph: propGraph found" + str(propGraph) + " getReferencedResource=" + str(node.getReferencedResource())) 
                        if self.searchCriteria.graphParamFunc or self.searchCriteria.ss_param_func:
                            paramName = prop.getLabel()
                            if self.searchCriteria.ss_param_func:
                                # Special search in parameter functions only
                                self.logSearch("searchGraph: special search: param functions only, adding found param function")
                                pathNode = self.searchResults.appendPathNode(propGraph, "", isFoundMatch=True, assignToCurrent=False)
                                pathNode.contextNode = node
                                pathNode.subType = SDObj.FUNC_PARAM
                                pathNode.name = paramName
                                pathNode.graph = graph
                                foundSearchResult_lev2 = True
                            else:
                                # Search into regular parameter function
                                self.logSearch("searchGraph: searching into regular param function")
                                if self.searchInto(propGraph, SDObj.FUNC_PARAM, paramName):
                                    foundSearchResult_lev2 = True
                    p += 1
                    
            refRes = node.getReferencedResource()

            # system nodes having inner graphs (FX-Map, Pixel Processor, Value)
            if SDObj.hasSystemContent(nodeType):
                self.logSearch("searchGraph: Searching into system node " + str(refRes)) 
                if self.searchInto(refRes, SDObj.systemContentType(nodeType), SDObj.systemGraphName(nodeType)):
                    foundSearchResult_lev2 = True
            else:
                # search custom sub-graphs
                if isinstance(refRes, SDGraph):
                    isFunctionGraph = isinstance(refRes, SDSBSFunctionGraph)
                    nodeType,_ = SDObj.type(node)
                    isSpecialGraph = SDObj.hasSystemContent(nodeType)
                    isCustomGraph = not isSpecialGraph and not isFunctionGraph
                    self.logSearch("searchGraph: searching custom sub-graphs: refRes:" + str(refRes) + " isFunctionGraph:"+str(isFunctionGraph)+ " isSpecialGraph:"+str(isSpecialGraph) + " isCustomGraph:"+str(isCustomGraph))

                    containerPathNode_lev2.subType = SDObj.GRAPH
                    containerPathNode_lev2.name = refRes.getIdentifier()
                    containerPathNode_lev2.referencedRes = refRes

                    if (isCustomGraph and self.searchCriteria.enterCustomSubGraphs):
                        if self.searchGraph(refRes):
                            foundSearchResult_lev2 = True

            self.pathLeaveContainer(containerPathNode_lev2, foundSearchResult_lev2)

            if foundSearchResult_lev2:
                foundSearchResult = True
            
        self.logSearch("searchGraph: exiting with foundSearchResult="+str(foundSearchResult))
        return foundSearchResult

    def searchGraphObjects(self, graph):
        self.logSearch("searchGraphObjects into " + str(graph))
        foundSearchResult = False
        # search comments or frames
        graphObjects = graph.getGraphObjects()
        if graphObjects:
            for g in range(0, graphObjects.getSize()):
                graphObject = graphObjects.getItem(g) 
                if self.searchGraphObject(graphObject):
                    foundSearchResult = True

        return foundSearchResult

    def searchGraphObject(self, graphObject):
        self.logSearch("searchGraphObject " + SDObj.dumpStr(graphObject))
        foundSearchResult = False
        isFrame = False
        title = ""
        if isinstance(graphObject, SDGraphObjectFrame):            
            isFrame = True
            try:
                title = graphObject.getTitle()
            except:
                gslog.error("Error retreiving frame title")

            if title and len(title) > 0 and self.isMatchingCriteria(title):
                pathNode = self.searchResults.appendPathNode(graphObject, title, isFoundMatch=True, assignToCurrent=False)
                pathNode.name = title
                foundSearchResult = True

        # search in comment
        desc = graphObject.getDescription()
        if self.isMatchingCriteriaInText(desc):
            pathNode = self.searchResults.appendPathNode(graphObject, desc, isFoundMatch=True, assignToCurrent=False)
            if isFrame:
                pathNode.name = title
            if isinstance(graphObject, SDGraphObjectComment):
                pathNode.contextNode = graphObject.getParent()
            foundSearchResult = True

        return foundSearchResult

    def searchFolder(self, folder):
        self.logSearch("searchFolder " + SDObj.dumpStr(folder))
        foundSearchResult = False
        # search folder name
        if self.searchCriteria.folderId:
            s = folder.getIdentifier()
            if self.isMatchingCriteria(s):
                self.searchResults.setFoundMatchForCurrentPathNode(s)
                foundSearchResult = True

        # search inside folder
        resources = folder.getChildren(False)
        if resources:
            for r in range(0, resources.getSize()):
                resource = resources.getItem(r)
                subType, _ = SDObj.type(resource)
                if self.isContainerNode(resource) and self.searchInto(resource, subType=subType):
                    foundSearchResult = True

        return foundSearchResult

    def searchFunctionGraph(self, functionGraph):
        self.logSearch("searchFunctionGraph " + SDObj.dumpStr(functionGraph))
        foundSearchResult = False
        #search function name
        if self.searchCriteria.funcName:
            [ident, label] = self.getIdAndLabelFromProperties(functionGraph)
            match = self.getMatchingIdOrLabel(ident, label)
            if match:
                self.searchResults.setFoundMatchForCurrentPathNode(match)
                foundSearchResult = True

        # search function inputs
        if self.searchCriteria.funcInput:
            foundSearchResult_lev2 = False
            properties = functionGraph.getProperties(SDPropertyCategory.Input)
            if properties:
                containerPathNode = self.pathEnterContainer(properties)
                containerPathNode.subType = SDObj.FUNC_INPUTS
                p = 0
                psize = properties.getSize()
                while p < psize:
                    prop = properties.getItem(p)
                    [ident, label] =  self.getIdAndLabelFromProperty(prop)
                    match = self.getMatchingIdOrLabel(ident, label)
                    if match:
                        pathNode = self.searchResults.appendPathNode(prop, match, isFoundMatch=True, assignToCurrent=False)
                        pathNode.name = ident

                        pathNode.subType = SDObj.FUNC_INPUT
                        foundSearchResult_lev2 = True
                    p += 1
                self.pathLeaveContainer(containerPathNode, foundSearchResult_lev2)
                if foundSearchResult_lev2:
                    foundSearchResult = True

        # search comments and frames
        if self.searchCriteria.comment:
            if self.searchGraphObjects(functionGraph):
                foundSearchResult = True

        # search function nodes
        nodes = functionGraph.getNodes()
        for n in range(0, nodes.getSize()):
            node = nodes.getItem(n)

            # search identifier
            identifier = node.getIdentifier()
            self.logSearch("searchFunctionGraph: node id="+identifier)
            if self.searchCriteria.searchString == identifier:
                self.logSearch("searchFunctionGraph: found id match")
                pathNode = self.searchResults.appendPathNode(node, identifier, isFoundMatch=True, assignToCurrent=False)
                pathNode.graph = functionGraph
                foundSearchResult = True

            defId = node.getDefinition().getId()
            if (self.searchCriteria.varGetter and defId.startswith("sbs::function::get")) or \
                (self.searchCriteria.varSetter and defId.startswith("sbs::function::set")):
                if self.matchFirstStringInputProperty(node):
                    foundSearchResult = True
            elif defId == "sbs::function::instance":
                functionGraph = node.getReferencedResource()
                if functionGraph:
                    if self.searchCriteria.enterGraphPkgFct:
                        # enter package function
                        foundSearchResult_lev2 = False
                        containerPathNode = self.pathEnterContainer(node)
                        containerPathNode.subType = SDObj.FUNCTION
                        containerPathNode.name = functionGraph.getIdentifier()
                        containerPathNode.referencedRes = functionGraph

                        if self.searchFunctionGraph(functionGraph):
                            foundSearchResult_lev2 = True

                        self.pathLeaveContainer(containerPathNode, foundSearchResult_lev2)

                        if foundSearchResult_lev2:
                            foundSearchResult = True
                    else:
                        if self.isMatchingCriteria(functionGraph.getIdentifier()):
                            pathNode = self.searchResults.appendPathNode(node, functionGraph.getIdentifier(), isFoundMatch=True, assignToCurrent=False)
                            pathNode.contextString = "Function call"
                            pathNode.subType = SDObj.FUNC_CALL
                            foundSearchResult = True

        return foundSearchResult

    def getIdFromProperties(self, propertyHolder):
        sdIdVal = propertyHolder.getPropertyValueFromId("identifier", SDPropertyCategory.Annotation)
        ident = "" if not sdIdVal or sdIdVal.get() == None else sdIdVal.get()
        return ident

    def getIdAndLabelFromProperties(self, propertyHolder):
        ident = self.getIdFromProperties(propertyHolder)
        label = ""
        sdLabelVal = propertyHolder.getPropertyValueFromId("label", SDPropertyCategory.Annotation)
        label = "" if not sdLabelVal or sdLabelVal.get() == None else sdLabelVal.get()
        return [ident, label]

    def getIdAndLabelFromProperty(self, property):
        ident = property.getId()
        label = property.getLabel()
        if label == None:
            label = ""
        return [ident, label]

    def getMatchingIdOrLabel(self, ident, label):
        match = "" 
        if self.isMatchingCriteria(ident):
            match = ident
        elif self.isMatchingCriteria(label):
            match = label
        return match
    
    def processWildcard(self, s):
        startsWithWildcard = s.startswith("*")
        endsWithWildcard = s.endswith("*")
        stripped = s
        
        if startsWithWildcard:
            stripped = stripped[1:]

        if endsWithWildcard:
            stripped = stripped[:-1]

        return (stripped, startsWithWildcard, endsWithWildcard)

    def isMatchingCriteria(self, s):
        if self.searchCriteria.caseSensitive:
            searchStr_mod = self.searchCriteria.searchString
            str_mod = s
        else:
            searchStr_mod = self.searchCriteria.searchString.lower()
            str_mod = s.lower()

        (stripped, startsWithWildcard, endsWithWildcard) = self.processWildcard(searchStr_mod)

        if self.searchCriteria.naturalSearch or (startsWithWildcard and endsWithWildcard):
            i = str_mod.find(stripped)
            match = i != -1
        elif startsWithWildcard:
            match = str_mod.endswith(stripped)
        elif endsWithWildcard:
            match = str_mod.startswith(stripped)
        else:
            match = str_mod == searchStr_mod

        return match

    def isMatchingCriteriaInText(self, text):
        if self.searchCriteria.caseSensitive:
            searchStr_mod = self.searchCriteria.searchString
            text_mod = text
        else:            
            searchStr_mod = self.searchCriteria.searchString.lower()
            text_mod = text.lower()

        (stripped,_, _) = self.processWildcard(searchStr_mod)
        i = text_mod.find(stripped)

        return i != -1

    def matchFirstStringInputProperty(self, node):
        foundSearchResult = False
        properties = node.getProperties(SDPropertyCategory.Input)
        if properties:
            foundStr = False
            p = 0
            psize = properties.getSize()
            while p < psize and not foundStr:
                prop = properties.getItem(p)
                sdValStr = node.getPropertyValue(prop)
                if sdValStr and isinstance(sdValStr, SDValueString):
                    foundStr = True
                    valStr = sdValStr.get()
                    if self.isMatchingCriteria(valStr):
                        self.searchResults.appendPathNode(node, valStr, isFoundMatch=True, assignToCurrent=False)
                        foundSearchResult = True
                p += 1

        return foundSearchResult
