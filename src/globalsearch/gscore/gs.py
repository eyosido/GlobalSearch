# ---------------
# Global Search - Substance 3D Designer plugin
# (c) 2019-2025 Eyosido Software SARL
# ---------------

import re
from sd.api.sdpackage import SDPackage
from sd.api.sdgraph import SDGraph
from sd.api.sbs.sdsbsfunctiongraph import SDSBSFunctionGraph
from sd.api.sdproperty import SDPropertyCategory
from sd.api.sdtypefloat import *
from sd.api.sdvaluefloat import *
from sd.api.sdvaluestring import SDValueString
from sd.api.sdresourcefolder import SDResourceFolder
from sd.api.sdgraphobjectcomment import SDGraphObjectComment
from sd.api.sdgraphobjectframe import SDGraphObjectFrame
from sd.api.sdgraphobjectpin import SDGraphObjectPin
from globalsearch.gscore import gslog
from globalsearch.gscore.sdobj import SDObj 
from globalsearch.gscore import gssdlibrary

class GlobalSearch:
    """
    Main search class
    """ 
    VERSION = "1.5"

    # A class keeping track of whether we currently are within the context of a node type filter
    # Filters are assigned when the parsing meets a node that matches the filter, and every node nested inside it.
    class NodeTypeFilterContext:
        def __init__(self, graphNodeFilter = None, functionNodeFilter = None):
            self.graphNodeFilter = graphNodeFilter # NoteTypeFilterData
            self.functionNodeFilter = functionNodeFilter # NoteTypeFilterData                

        def hasNodeFilter(self):
            return self.graphNodeFilter or self.functionNodeFilter
        
        def hasGraphNodeFilter(self):
            return self.graphNodeFilter is not None

        def hasFunctionNodeFilter(self):
            return self.functionNodeFilter is not None

    def __init__(self, ctx, prefs, searchRoot, searchCriteria, searchResults):
        self.context = ctx
        self.prefs = prefs
        self.searchRoot = searchRoot
        self.searchCriteria = searchCriteria
        self.nodeFilterContext = None
        self.searchResults = searchResults
        self.searchLogs = prefs.dev_searchLogs # enable to log information about the search (debug only)
        self.searchResults.searchLogs = self.searchLogs
        self.depth = 0  # tree depth, used mostly for debugging

    def search(self):
        self.depth = 0
        self.searchInto(self.searchRoot, self.NodeTypeFilterContext())

    def logSearch(self, s):
        if self.searchLogs:
            gslog.debug('[SEARCH]' + s)

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

    def searchInto(self, sdObj, nodeTypeFilterContext, subType = SDObj.ROOT, parentSubtype = SDObj.ROOT, name = ""):
        self.logSearch("searchInto " + SDObj.dumpStr(sdObj) + " depth="+str(self.depth))
        if sdObj == None:
            # we need to have root node when searching over multiple packages
            containerPathNode = self.pathEnterContainer(sdObj)
            containerPathNode.subType = SDObj.ROOT
            containerPathNode.name = "Root"
            foundSearchResult = self.searchPackages(nodeTypeFilterContext)
            self.pathLeaveContainer(containerPathNode, foundSearchResult)
        else:
            containerPathNode = self.pathEnterContainer(sdObj)
            self.depth += 1
            containerPathNode.subType = subType
            containerPathNode.name = name

            foundSearchResult = False
            if isinstance(sdObj, SDPackage):
                foundSearchResult = self.searchPackage(sdObj, nodeTypeFilterContext)
            elif isinstance(sdObj, SDSBSFunctionGraph):
                isPackageFctDef = parentSubtype == SDObj.ROOT or parentSubtype == SDObj.FOLDER or parentSubtype == SDObj.PACKAGE
                foundSearchResult = self.searchFunctionGraph(sdObj, nodeTypeFilterContext, isPackageFctDef=isPackageFctDef)
            elif isinstance(sdObj, SDGraph):
                foundSearchResult = self.searchGraph(sdObj, nodeTypeFilterContext)
            elif isinstance(sdObj, SDResourceFolder):
                foundSearchResult = self.searchFolder(sdObj, nodeTypeFilterContext)
            else:
                gslog.warning("Nothing to search into, this is not a container")

            self.pathLeaveContainer(containerPathNode, foundSearchResult)
            self.depth -= 1

        return foundSearchResult

    def searchPackages(self, nodeTypeFilterContext):
        self.logSearch("searchPackages ")
        foundSearchResult = False
        app = self.context.getSDApplication()
        packages = app.getPackageMgr().getUserPackages()
        if packages:
            count = packages.getSize()
            self.logSearch("searchPackages found " + str(count) + ' packages')
            for p in range(0, count):
                package = packages.getItem(p)
                if self.searchInto(package, nodeTypeFilterContext, subType=SDObj.PACKAGE):
                    foundSearchResult = True
        return foundSearchResult

    def searchPackage(self, package, nodeTypeFilterContext):
        self.logSearch("searchPackage " + SDObj.dumpStr(package))
        foundSearchResult = False
        resources = package.getChildrenResources(False)
        if resources:
            count = resources.getSize()
            self.logSearch("searchPackage found " + str(count) + ' resources')
            for r in range(0, count):
                resource = resources.getItem(r)
                subType, _ = SDObj.type(resource)
                if self.isContainerNode(resource) and self.searchInto(resource, nodeTypeFilterContext, subType=subType, parentSubtype=SDObj.PACKAGE):
                    foundSearchResult = True

        return foundSearchResult

    def searchGraph(self, graph, nodeTypeFilterContext):
        self.logSearch("searchGraph " + SDObj.dumpStr(graph))
        foundSearchResult = False

        # search graph name
        if not self.searchCriteria.hasNodeFilter():
            if self.searchCriteria.graphName:
                [ident, label] = self.getIdAndLabelFromProperties(graph)
                match = self.getMatchingIdOrLabel(ident, label)
                if match:
                    self.searchResults.setFoundMatchForCurrentPathNode(match)
                    foundSearchResult = True

        # Gather comments and frames
        if self.searchCriteria.comment:
            parentedComments, unparentedComments, frames, pins = self.gatherGraphObjects(graph)
        
            # search unparented graph objects (parented ones will be searched per node within the node loop underneath)
            if not self.searchCriteria.hasNodeFilter():
                if len(unparentedComments) > 0 and self.searchComments(unparentedComments):
                    foundSearchResult = True

                if len(pins) and self.searchPins(pins):
                    foundSearchResult = True

                if len(frames) and self.searchFrames(frames):
                    foundSearchResult = True

        # search graph param functions and subgraphs
        nodes = graph.getNodes()
        self.logSearch("searchGraph: parsing graph nodes")
        for n in range(0, nodes.getSize()):
            node = nodes.getItem(n)
            nodeType, typeStr = SDObj.type(node)   
            refRes = node.getReferencedResource()
            currentNodeTypeFilterContext = nodeTypeFilterContext # reset to original context for each new node
            ap_identifier = None
            self.logSearch("searchGraph: current node: " + SDObj.dumpStr(node))

            # node type filter
            graphNodefilter = self.searchCriteria.graphNodeFilter
            graphNodefilterMatch = False
            graphNodefilterPartialMatch = False
            if graphNodefilter:
                stringMatch = ""
                graphNodefilterMatch, graphNodefilterPartialMatch, isSystem = self.searchCriteria.isGraphNodeFilterMatchingWithTypeAndRefRes(nodeType, refRes)
                if graphNodefilterPartialMatch:
                    self.logSearch("searchGraph: partial match found")

                if graphNodefilterMatch or graphNodefilterPartialMatch:
                    if isSystem:
                        self.logSearch("searchGraph: found system node filter match/partial match: " + str(nodeType) + " " + typeStr)
                    else:
                        graph_id = refRes.getIdentifier()
                        self.logSearch("searchGraph: found library node filter match: " + str(nodeType) + " " + typeStr + " " + graph_id)
                        stringMatch = graph_id
                    
                    # if we have a function node filter, we don't consider the graph node filter as a match, it is only a condition to reach the function node filter
                    if not self.searchCriteria.hasSearchString() and not self.searchCriteria.functionNodeFilter:
                        # no search string so we're searching by node type only and we found one that matches
                        pathNode = self.searchResults.appendPathNode(node, stringMatch, isFoundMatch=True, assignToCurrent=False)
                        foundSearchResult = True

                    # as we found a node type match, set up a new node type filter context, so nested nodes will have it too
                    currentNodeTypeFilterContext = self.NodeTypeFilterContext(self.searchCriteria.graphNodeFilter, None)
                else:
                    # filtering by node type and not having node type match, continue to next node unless this is a graph container
                    if not isinstance(refRes, SDGraph):
                        self.logSearch("searchGraph: node filter not matching, skipping this node")
                        continue
                    else:
                        self.logSearch("searchGraph: node filter not matching but not skipping to enter its content (subgraph)")

            passedGraphNodeFiltering = (not graphNodefilter) or graphNodefilterMatch
            if passedGraphNodeFiltering and (not self.searchCriteria.functionNodeFilter):
                identifier = node.getIdentifier()
                if self.searchCriteria.comment and len(parentedComments) > 0:
                    # search parented comments
                    comments = parentedComments.get(identifier)
                    if comments and self.searchComments(comments, node):
                        foundSearchResult = True

                # search identifier
                self.logSearch("searchGraph: node id="+identifier)
                if self.searchCriteria.searchString == identifier:
                    self.logSearch("searchGraph: found id match")
                    pathNode = self.searchResults.appendPathNode(node, identifier, isFoundMatch=True, assignToCurrent=False)
                    foundSearchResult = True

                # search identifier on Output and Input nodes
                if SDObj.isInputNode(nodeType) or nodeType == SDObj.OUTPUT:
                    ap_identifier = node.getAnnotationPropertyValueFromId('identifier').get()
                    if self.isMatchingSearchStringCriteria(ap_identifier):
                        self.logSearch("searchGraph: found Input or Output node with identifier=" + ap_identifier)
                        pathNode = self.searchResults.appendPathNode(node, ap_identifier, isFoundMatch=True, assignToCurrent=False)
                        foundSearchResult = True

            containerPathNode_lev2 = self.pathEnterContainer(node)
            foundSearchResult_lev2 = False

            if passedGraphNodeFiltering:
                # search graph param functions in input properties
                self.logSearch("searchGraph: searching param functions for current node")
                properties = node.getProperties(SDPropertyCategory.Input)
                if properties:
                    p = 0
                    psize = properties.getSize()
                    while p < psize:
                        prop = properties.getItem(p)
                        propGraph = node.getPropertyGraph(prop)
                        functionOnly = prop.isFunctionOnly()

                        self.logSearch("searchGraph: input prop id=" + prop.getId() + " propGraph="+str(propGraph) + " functionOnly="+str(functionOnly))

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
                                    if self.searchInto(propGraph, currentNodeTypeFilterContext, SDObj.FUNC_PARAM, parentSubtype=SDObj.GRAPH_NODE, name=paramName):
                                        foundSearchResult_lev2 = True
                        p += 1
                    
            # system nodes having inner graphs (FX-Map, Pixel Processor, Value)
            if (passedGraphNodeFiltering or graphNodefilterPartialMatch) and SDObj.hasSystemContent(nodeType):
                self.logSearch("searchGraph: Searching into system node " + str(refRes)) 
                if self.searchInto(refRes, nodeTypeFilterContext, subType=SDObj.systemContentType(nodeType), parentSubtype=nodeType, name=SDObj.systemGraphName(nodeType)):
                    foundSearchResult_lev2 = True
            else:
                # search custom sub-graphs
                if isinstance(refRes, SDGraph):
                    isFunctionGraph = isinstance(refRes, SDSBSFunctionGraph)
                    isSpecialGraph = SDObj.hasSystemContent(nodeType)
                    isCustomGraph = not isSpecialGraph and not isFunctionGraph

                    if (isCustomGraph and self.searchCriteria.enterCustomSubGraphs):
                        subgraph_identifier = None
                        v = refRes.getAnnotationPropertyValueFromId('identifier')
                        if v:
                            subgraph_identifier = v.get()

                        if subgraph_identifier and gssdlibrary.g_gssdlibrary.entry(subgraph_identifier) == None:   # don't descend into system library nodes
                            containerPathNode_lev2.subType = SDObj.GRAPH
                            containerPathNode_lev2.name = SDObj.name(node, SDObj.GRAPH_INSTANCE)
                            containerPathNode_lev2.referencedRes = refRes
                            self.logSearch("searchGraph: searching custom sub-graphs: refRes:" + str(refRes) + " isFunctionGraph:"+str(isFunctionGraph)+ " isSpecialGraph:"+str(isSpecialGraph) + " isCustomGraph:"+str(isCustomGraph))
                            if self.searchGraph(refRes, currentNodeTypeFilterContext):
                                foundSearchResult_lev2 = True

            self.pathLeaveContainer(containerPathNode_lev2, foundSearchResult_lev2)

            if foundSearchResult_lev2:
                foundSearchResult = True
            
        self.logSearch("searchGraph: exiting with foundSearchResult="+str(foundSearchResult))
        return foundSearchResult
    
    # Gather graph objects in the given graph and place them into 3 collections:
    # - parentedComments: comments having a parent node. This is a dict whose keys are the parent node, this enables to process comments within the context of a node (helps with node type filters)
    # - unparentedComments: comments without parent node
    # - frames: frames (unparented)
    def gatherGraphObjects(self, graph):
        # gather comments or frames
        graphObjects = graph.getGraphObjects()
        parentedComments = {} # key: parent.getIdentifier() value: comment
        unparentedComments = []
        frames = []
        pins = []
        if graphObjects:
            for g in range(0, graphObjects.getSize()):
                graphObject = graphObjects.getItem(g)
                if isinstance(graphObject, SDGraphObjectFrame):
                    frames.append(graphObject)
                elif isinstance(graphObject, SDGraphObjectPin):
                    pins.append(graphObject)
                elif isinstance(graphObject, SDGraphObjectComment):
                    parentNode = graphObject.getParent()
                    if parentNode:
                        key = parentNode.getIdentifier()
                        if not parentedComments.get(key):
                            parentedComments[key] = list()                            
                        parentedComments[key].append(graphObject)
                    else:
                        unparentedComments.append(graphObject)

        self.logSearch("gatherGraphObjects into " + str(graph) + " parentedComments:"+str(len(parentedComments)) + \
                       " unparentedComments:"+str(len(unparentedComments)) + \
                       " frames:"+str(len(frames)))
        return parentedComments, unparentedComments, frames, pins
    
    def searchComments(self, comments, parentNode = None):
        foundSearchResult = False
        for comment in comments:
            desc = comment.getDescription()
            if self.isMatchingSearchStringCriteria(desc):
                self.logSearch('searchComments appendPathNode "' + desc + '"')
                pathNode = self.searchResults.appendPathNode(comment, desc, isFoundMatch=True, assignToCurrent=False)                
                pathNode.contextNode = parentNode
                foundSearchResult = True
        return foundSearchResult

    def searchPins(self, pins):
        foundSearchResult = False
        for pin in pins:
            desc = pin.getDescription()
            if self.isMatchingSearchStringCriteria(desc):
                self.logSearch('searchPins appendPathNode "' + desc + '"')
                pathNode = self.searchResults.appendPathNode(pin, desc, isFoundMatch=True, assignToCurrent=False)                
                foundSearchResult = True
        return foundSearchResult

    def searchFrames(self, frames):
        foundSearchResult = False
        for frame in frames:
            # frame title
            try:
                title = frame.getTitle()
            except:
                gslog.error("Error retreiving frame title")

            if title and len(title) > 0 and self.isMatchingSearchStringCriteria(title):
                self.logSearch('searchFrames title appendPathNode "' + title + '"')
                pathNode = self.searchResults.appendPathNode(frame, title, isFoundMatch=True, assignToCurrent=False)
                pathNode.name = title
                foundSearchResult = True

            # frame content
            desc = frame.getDescription()
            if self.isMatchingSearchStringCriteria(desc):
                self.logSearch('searchFrames content appendPathNode"' + desc + '"')
                pathNode = self.searchResults.appendPathNode(frame, desc, isFoundMatch=True, assignToCurrent=False)                
                pathNode.name = title
                foundSearchResult = True

        return foundSearchResult

    def searchFolder(self, folder, nodeTypeFilterContext):
        self.logSearch("searchFolder " + SDObj.dumpStr(folder))
        foundSearchResult = False

        if not self.searchCriteria.hasNodeFilter():
            # search folder name
            if self.searchCriteria.folderId:
                s = folder.getIdentifier()
                if self.isMatchingSearchStringCriteria(s):
                    self.searchResults.setFoundMatchForCurrentPathNode(s)
                    foundSearchResult = True

        # search inside folder
        resources = folder.getChildren(False)
        if resources:
            for r in range(0, resources.getSize()):
                resource = resources.getItem(r)
                subType, _ = SDObj.type(resource)
                if self.isContainerNode(resource) and self.searchInto(resource, nodeTypeFilterContext, subType=subType, parentSubtype=SDObj.FOLDER):
                    foundSearchResult = True

        return foundSearchResult

    # isPackageFctDef: tells whether the function is a package function definition (in a folder in the Explorer), i.e. not within the context of a node
    def searchFunctionGraph(self, functionGraph, nodeTypeFilterContext, isPackageFctDef):
        self.logSearch("searchFunctionGraph " + SDObj.dumpStr(functionGraph) + " isPackageFctDef="+str(isPackageFctDef))
        foundSearchResult = False

        if isPackageFctDef and self.searchCriteria.graphNodeFilter:
            # if this is a package function definition, it is not related to a graph node, so if a graph node filter is enabled, we don't search into this function
            self.logSearch("searchFunctionGraph exiting as we have graph node filter and inside package function definition")
            return False

        if not self.searchCriteria.functionNodeFilter:
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

        # Gather comments and frames
        if self.searchCriteria.comment:
            parentedComments, unparentedComments, frames, pins = self.gatherGraphObjects(functionGraph)
        
            # search unparented graph objects (parented ones will be searched per node within the node loop underneath)
            if not self.searchCriteria.functionNodeFilter:
                if len(unparentedComments) > 0 and self.searchComments(unparentedComments):
                    foundSearchResult = True

                if len(pins) and self.searchPins(pins):
                    foundSearchResult = True

                if len(frames) > 0 and self.searchFrames(frames):
                    foundSearchResult = True

        # search function nodes
        nodes = functionGraph.getNodes()
        for n in range(0, nodes.getSize()):
            node = nodes.getItem(n)
            defId = node.getDefinition().getId()
            identifier = node.getIdentifier()

            searchNodeType = self.searchCriteria.functionNodeFilter and not self.searchCriteria.hasSearchString()
            searchIdentifier = not searchNodeType
            noFilterOrFilterMatch = (not self.searchCriteria.functionNodeFilter) or (self.searchCriteria.functionNodeFilter.definition == defId)

            if searchNodeType:
                # searching for function nodes only without search string
                if self.searchCriteria.isFunctionNodeFilterMatching(node):
                    self.logSearch("searchFunctionGraph: found node type filter match ")
                    pathNode = self.searchResults.appendPathNode(node, "", isFoundMatch=True, 
                    assignToCurrent=False)
                    pathNode.name = self.searchCriteria.functionNodeFilter.label
                    pathNode.graph = functionGraph
                    foundSearchResult = True                

            if searchIdentifier:
                # search identifier                
                self.logSearch("searchFunctionGraph: node id="+identifier)
                if self.searchCriteria.searchString == identifier:
                    self.logSearch("searchFunctionGraph: found id match")
                    pathNode = self.searchResults.appendPathNode(node, identifier, isFoundMatch=True, assignToCurrent=False)
                    pathNode.graph = functionGraph
                    foundSearchResult = True

            if noFilterOrFilterMatch:
                # search parented comments
                if self.searchCriteria.comment and len(parentedComments) > 0:
                    comments = parentedComments.get(identifier)
                    if comments and self.searchComments(comments, node):
                        foundSearchResult = True
                
                if ((self.searchCriteria.varGetter and defId.startswith("sbs::function::get")) or (self.searchCriteria.varSetter and defId.startswith("sbs::function::set"))):
                    if self.matchFirstStringInputProperty(node):
                        self.logSearch("searchFunctionGraph: found match for getter or setter")
                        foundSearchResult = True
            
            if defId == "sbs::function::instance":
                functionGraph = node.getReferencedResource()
                if functionGraph:
                    if self.searchCriteria.enterGraphPkgFct:
                        # enter package function
                        foundSearchResult_lev2 = False
                        containerPathNode = self.pathEnterContainer(node)
                        containerPathNode.subType = SDObj.FUNCTION
                        containerPathNode.name = functionGraph.getIdentifier()
                        containerPathNode.referencedRes = functionGraph

                        if self.searchFunctionGraph(functionGraph, nodeTypeFilterContext, isPackageFctDef=False):
                            foundSearchResult_lev2 = True

                        self.pathLeaveContainer(containerPathNode, foundSearchResult_lev2)

                        if foundSearchResult_lev2:
                            foundSearchResult = True
                    elif self.searchCriteria.funcName and (not self.searchCriteria.functionNodeFilter and self.isMatchingSearchStringCriteria(functionGraph.getIdentifier())):
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
        if self.isMatchingSearchStringCriteria(ident):
            match = ident
        elif self.isMatchingSearchStringCriteria(label):
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
    
    def prepareForCaseSensitivity(self, searchedContent, searchString):
        if self.searchCriteria.caseSensitive:
            searchString_mod = self.searchCriteria.searchString
            seachedContent_mod = searchedContent
        else:
            searchString_mod = self.searchCriteria.searchString.lower()
            seachedContent_mod = searchedContent.lower()
        return seachedContent_mod, searchString_mod
    
    # returns whether searchedContent has searchString as whole word
    def hasWholeWord(self, searchedContent, searchString):
        patternStart = r'\b'
        patternEnd = r'\b'

        # handle potential wildcards
        if searchString.startswith('*'):
            patternStart += r'\w*'
            searchString = searchString[1:] # remove first *
        if searchString.endswith('*'):
            patternEnd = r'\w*' + patternEnd
            searchString = searchString[:-1] # remove last *
        
        match = re.search( patternStart + re.escape(searchString) + patternEnd, searchedContent)        
        return bool(match)      

    def isMatchingSearchStringCriteria(self, content):
        if self.searchCriteria.hasSearchString():
            content_mod, searchStr_mod = self.prepareForCaseSensitivity(content, self.searchCriteria.searchString)

            if self.searchCriteria.wholeWord:
                return self.hasWholeWord(content_mod, searchStr_mod)
            else:
                (stripped, startsWithWildcard, endsWithWildcard) = self.processWildcard(searchStr_mod)
                (stripped,_, _) = self.processWildcard(searchStr_mod)
                i = content_mod.find(stripped)
                return i != -1

        return False            

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
                    if self.isMatchingSearchStringCriteria(valStr):
                        self.searchResults.appendPathNode(node, valStr, isFoundMatch=True, assignToCurrent=False)
                        foundSearchResult = True
                p += 1

        return foundSearchResult
