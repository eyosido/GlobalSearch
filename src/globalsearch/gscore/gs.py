# ---------------
# Global Search - Substance 3D Designer plugin
# (c) 2019-2022 Eyosido Software SARL
# ---------------

import sd
from sd.context import Context
from sd.api.sdpackage import SDPackage
from sd.api.sdgraph import SDGraph
from sd.api.sduimgr import SDUIMgr
from sd.api.sdapplication import SDApplication
from sd.api.sdarray import SDArray
from sd.api.sbs.sdsbsfunctiongraph import SDSBSFunctionGraph
from sd.api.sbs.sdsbsfunctionnode import SDSBSFunctionNode
from sd.api.sdproperty import SDProperty, SDPropertyCategory
from sd.api.sdvalue import SDValue
from sd.api.sdapiobject import SDAPIObject
from sd.api.sdtypefloat import *
from sd.api.sdvaluefloat import *
from sd.api.sdnode import SDNode
from sd.api.sdvaluestring import SDValueString
from sd.api.sddefinition import SDDefinition
from sd.api.sdresourcefolder import SDResourceFolder
from sd.api.sdgraphobject import SDGraphObject
from sd.api.sdgraphobjectcomment import SDGraphObjectComment
from sd.api.sdgraphobjectframe import SDGraphObjectFrame
from sd.api.sbs.sdsbscompnode import SDSBSCompNode
from sd.api.sbs.sdsbsfxmapnode import SDSBSFxMapNode
from sd.api.sbs.sdsbscompgraph import SDSBSCompGraph

from globalsearch.gscore import gslog
from globalsearch.gscore.sdobj import SDObj 

class GlobalSearch:
    """
    Main search class
    """ 
    VERSION = "1.2.3"

    def __init__(self, ctx, searchRoot, searchCriteria, searchResults):
        self.context = ctx
        self.searchRoot = searchRoot
        self.searchCriteria = searchCriteria
        self.searchResults = searchResults

    # -------- Public
    def search(self):
        self.searchInto(self.searchRoot)

    # -------- Private
    def isContainerNode(self, sdObj):
        return sdObj == None or isinstance(sdObj, SDPackage) or isinstance(sdObj, SDGraph) \
            or isinstance(sdObj, SDResourceFolder)

    def pathEnterContainer(self, sdContainerObj):
        return self.searchResults.appendPathNode(sdContainerObj)
    
    def pathLeaveContainer(self, containerPathNode, foundSearchResult):
        if not foundSearchResult:
            self.searchResults.currentPathNode = containerPathNode   # restore currentPathNode
            self.searchResults.dropCurrentPathBranch()
        
        self.searchResults.currentPathNode = containerPathNode.parent   # we're done with this container, move to parent

    def searchInto(self, sdObj, subType = SDObj.UNDEFINED, name = ""):
        if sdObj == None:
            foundSearchResult = self.searchPackages()
        else:
            containerPathNode = self.pathEnterContainer(sdObj)
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

            self.pathLeaveContainer(containerPathNode, foundSearchResult)

        return foundSearchResult

    def searchPackages(self):
        foundSearchResult = False
        app = self.context.getSDApplication()
        packages = app.getPackageMgr().getUserPackages()
        if packages:
            for p in range(0, packages.getSize()):
                package = packages.getItem(p)
                if self.searchInto(package):
                    foundSearchResult = True
        return foundSearchResult

    def searchPackage(self, package):
        foundSearchResult = False
        resources = package.getChildrenResources(False)
        if resources:
            for r in range(0, resources.getSize()):
                resource = resources.getItem(r)
                if self.isContainerNode(resource) and self.searchInto(resource):
                    foundSearchResult = True

        return foundSearchResult

    def searchGraph(self, graph):
        foundSearchResult = False

        # search graph name
        if self.searchCriteria.graphName:
            [id, label] = self.getIdAndLabelFromProperties(graph)
            match = self.getMatchingIdOrLabel(id, label)
            if match:
                self.searchResults.setFoundMatchForCurrentPathNode(match)
                foundSearchResult = True

        # search comments and frames
        if self.searchCriteria.comment:
            if self.searchGraphObjects(graph):
                foundSearchResult = True

        # search graph param functions and subgraphs
        nodes = graph.getNodes()
        for n in range(0, nodes.getSize()):
            node = nodes.getItem(n)
            
            if self.searchCriteria.graphParamFunc or self.searchCriteria.ss_param_func:
                # search graph params functions
                properties = node.getProperties(SDPropertyCategory.Input)
                if properties:
                    foundSearchResult_lev2 = False
                    containerPathNode = self.pathEnterContainer(node)
                    p = 0
                    psize = properties.getSize()
                    while p < psize:
                        prop = properties.getItem(p)
                        propGraph = node.getPropertyGraph(prop)
                        functionOnly = prop.isFunctionOnly()

                        if propGraph and not functionOnly: # ignore function props of graphs having subgraphs like pixel processor
                            # a function graph is controlling this property
                            paramName = prop.getLabel()
                            if self.searchCriteria.ss_param_func:
                                pathNode = self.searchResults.appendPathNode(propGraph, "", True, False)
                                pathNode.contextNode = node
                                pathNode.subType = SDObj.FUNC_PARAM
                                pathNode.name = paramName
                                foundSearchResult_lev2 = True
                            else:
                                 if self.searchInto(propGraph, SDObj.FUNC_PARAM, paramName):
                                     foundSearchResult_lev2 = True
                        p += 1
                    self.pathLeaveContainer(containerPathNode, foundSearchResult_lev2)
                    if foundSearchResult_lev2:
                        foundSearchResult = True

            # search sub-graphs
            refRes = node.getReferencedResource()
            if isinstance(refRes, SDGraph):
                isFunctionGraph = isinstance(refRes, SDSBSFunctionGraph)
                nodeType,_ = SDObj.type(node)
                isSpecialGraph = SDObj.isSpecialSubgraphType(nodeType)
                isCustomGraph = not isSpecialGraph and not isFunctionGraph

                if (isCustomGraph and self.searchCriteria.enterCustomSubGraphs) or\
                    isSpecialGraph or\
                    (isFunctionGraph and self.searchCriteria.enterGraphPkgFct):
                    # we are not using searchInto() as this would insert an SDGraph path node,
                    # rather we want to insert an SDNode path node as this one holds the type (i.e. fx-map)
                    foundSearchResult_lev2 = False
                    containerPathNode = self.pathEnterContainer(node)

                    if isCustomGraph or isFunctionGraph:
                        resType,_ = SDObj.type(refRes)
                        containerPathNode.name = SDObj.name(refRes, resType) # graph name

                    if self.searchGraph(refRes):
                        foundSearchResult_lev2 = True

                    self.pathLeaveContainer(containerPathNode, foundSearchResult_lev2)
                    if foundSearchResult_lev2:
                        foundSearchResult = True

        return foundSearchResult

    def searchGraphObjects(self, graph):
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
        foundSearchResult = False
        foundInTitle = False
        if isinstance(graphObject, SDGraphObjectFrame):
            title = ""
            try:
                title = graphObject.getTitle()
            except:
                gslog.log("Error retreiving frame title")

            if title and len(title) > 0 and self.isMatchingCriteria(title):
                foundInTitle = True
                self.searchResults.appendPathNode(graphObject, title, True, False)
                foundSearchResult = True

        if not foundInTitle: # do not search description if already found in title
            desc = graphObject.getDescription()
            if self.isMatchingCriteriaInText(desc):
                self.searchResults.appendPathNode(graphObject, desc, True, False)
                foundSearchResult = True
        return foundSearchResult

    def searchFolder(self, folder):
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
                if self.isContainerNode(resource) and self.searchInto(resource):
                    foundSearchResult = True

        return foundSearchResult

    def searchFunctionGraph(self, functionGraph):
        foundSearchResult = False
        #search function name
        if self.searchCriteria.funcName:
            [id, label] = self.getIdAndLabelFromProperties(functionGraph)
            match = self.getMatchingIdOrLabel(id, label)
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
                    [id, label] =  self.getIdAndLabelFromProperty(prop)
                    match = self.getMatchingIdOrLabel(id, label)
                    if match:
                        pathNode = self.searchResults.appendPathNode(prop, match, True, False)
                        pathNode.name = id
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
            defId = node.getDefinition().getId()
            if (self.searchCriteria.varGetter and defId.startswith("sbs::function::get")) or \
                (self.searchCriteria.varSetter and defId.startswith("sbs::function::set")):
                if self.matchFirstStringInputProperty(node):
                    foundSearchResult = True
            elif defId == "sbs::function::instance":
                functionGraph = node.getReferencedResource()
                if functionGraph:
                    if self.isMatchingCriteria(functionGraph.getIdentifier()):
                        pathNode = self.searchResults.appendPathNode(node, functionGraph.getIdentifier(), True, False)
                        pathNode.contextString = "Function call"
                        pathNode.subType = SDObj.FUNC_CALL
                        foundSearchResult = True

        return foundSearchResult

    def getIdFromProperties(self, propertyHolder):
        sdIdVal = propertyHolder.getPropertyValueFromId("identifier", SDPropertyCategory.Annotation)
        id = "" if not sdIdVal or sdIdVal.get() == None else sdIdVal.get()
        return id

    def getIdAndLabelFromProperties(self, propertyHolder):
        id = self.getIdFromProperties(propertyHolder)
        label = ""
        sdLabelVal = propertyHolder.getPropertyValueFromId("label", SDPropertyCategory.Annotation)
        label = "" if not sdLabelVal or sdLabelVal.get() == None else sdLabelVal.get()
        return [id, label]

    def getIdAndLabelFromProperty(self, property):
        id = property.getId()
        label = property.getLabel()
        if label == None:
            label = ""
        return [id, label]

    def getMatchingIdOrLabel(self, id, label):
        match = "" 
        if self.isMatchingCriteria(id):
            match = id
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
                        self.searchResults.appendPathNode(node, valStr, True, False)
                        foundSearchResult = True
                p += 1

        return foundSearchResult
