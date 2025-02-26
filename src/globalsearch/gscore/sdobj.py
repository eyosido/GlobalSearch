# ---------------
# Global Search - Substance 3D Designer plugin
# (c) 2019-2022 Eyosido Software SARL
# ---------------

import inspect
from pathlib import Path

from sd.api.sdpackage import SDPackage
from sd.api.sdgraph import SDGraph
from sd.api.sbs.sdsbsfunctiongraph import SDSBSFunctionGraph
from sd.api.sbs.sdsbsfunctionnode import SDSBSFunctionNode
from sd.api.sdtypefloat import *
from sd.api.sdvaluefloat import *
from sd.api.sdnode import SDNode
from sd.api.sdresourcefolder import SDResourceFolder
from sd.api.sdgraphobjectcomment import SDGraphObjectComment
from sd.api.sdgraphobjectframe import SDGraphObjectFrame

class SDObj:
    """
    Helper for SD API objects
    """
    UNDEFINED = 0
    ROOT = 1
    PACKAGE = 2
    GRAPH = 3
    FOLDER = 4
    FUNCTION = 5
    FUNC_INPUT = 6   # function input param
    PARAM_INPUT = 7  # graph input param
    FUNC_PARAM = 8   # parameter driven by a function
    
    SYSTEM_CONTENT = 20 # system nodes having subgraph or function to drive them
    FX_MAP_GRAPH = 21
    PIXEL_PROCESSOR_FUNC = 22
    VALUE_PROCESSOR_FUNC = 23
    SYSTEM_CONTENT_END = 29

    # Nodes that can be found inside a regular graph
    GRAPH_NODE = 100    # any graph node unless the specifics below
    FX_MAP = 101
    PIXEL_PROCESSOR = 102
    VALUE_PROCESSOR = 103
    GRAPH_INSTANCE = 104    # node representing a graph, either system (i.e. Switch node) or user graph

    # Nodes that can be found inside FX-MAP graphs
    FXMAP_GRAPH_NODE = 180
    FXMAP_QUADRANT = 181
    FXMAP_SWITCH = 182
    FXMAP_ITERATE = 183
    FXMAP_DOT = 184
    FXMAP_GRAPH_NODE_LAST = 198

    GRAPH_NODE_LAST = 199

    # nodes with no specific name associated to them
    UNNAMED_NODE = 200

    FUNC_INPUTS = 201 # SDArray of function of input params

    # graph objects (comment/frame)
    GRAPHOBJECT = 300
    COMMENT = 301
    FRAME = 302
    GRAPHOBJECT_LAST = 399

    # Nodes that can be found inside functions
    FUNCTION_NODE = 400
    FNODE_GET = 401
    FNODE_SET = 402
    FUNCTION_NODE_LAST = 499

    # Node associated to a role
    FUNC_CALL = 500 # a function being called inside another function

    NODE_WITH_SYSTEM_CONTENT_NAME = {
        FX_MAP: "FX-Map",
        PIXEL_PROCESSOR: "Pixel Processor",
        VALUE_PROCESSOR: "Value Procssor"
    }

    SYSTEM_GRAPH_NAME = {
        FX_MAP: "FX-Map Graph",
        PIXEL_PROCESSOR: "Per Pixel Function",
        VALUE_PROCESSOR: "Value Processor Graph"
    }

    SDNODE_TYPE = { # mapping definitionId to node (type,typeStr)
        "sbs::compositing::pixelprocessor": (PIXEL_PROCESSOR, "pixel processor"),
        "sbs::compositing::valueprocessor": (VALUE_PROCESSOR, "value processor"),
        "sbs::compositing::sbscompgraph_instance": (GRAPH_INSTANCE, "graph instance"),

        # FX-MAP specific
        "sbs::compositing::fxmaps": (FX_MAP, "fx-map"),
        "sbs::fxmap::paramset": (FXMAP_QUADRANT, "Quadrant"),
        "sbs::fxmap::markov2": (FXMAP_SWITCH, "Switch"),
        "sbs::fxmap::addnode": (FXMAP_ITERATE, "Iterate"),
        "sbs::fxmap::passthrough": (FXMAP_DOT, "Dot"),
    } 

    @classmethod
    def type(cls, sdObj):
        type = cls.UNDEFINED
        typeStr = ""
        if isinstance(sdObj, SDPackage):
            type = cls.PACKAGE
            typeStr = "package"
        elif isinstance(sdObj, SDSBSFunctionGraph):
            type = cls.FUNCTION
            typeStr = "function"
        elif isinstance(sdObj, SDGraph):
            type = cls.GRAPH
            typeStr = "graph"
        elif isinstance(sdObj, SDSBSFunctionNode):
            defId = sdObj.getDefinition().getId()
            if defId.startswith("sbs::function::get"):
                type = cls.FNODE_GET
                typeStr = "get"
            elif defId.startswith("sbs::function::set"):
                type = cls.FNODE_SET
                typeStr = "set"
        elif isinstance(sdObj, SDGraphObjectComment):
            type = cls.COMMENT
            typeStr = "comment"
        elif isinstance(sdObj, SDGraphObjectFrame):
            type = cls.FRAME
            typeStr = "frame"
        elif isinstance(sdObj, SDResourceFolder):  
            type = cls.FOLDER  
            typeStr = "folder"
        elif isinstance(sdObj, SDNode):
            definitionId = sdObj.getDefinition().getId()
            typeTuple = cls.SDNODE_TYPE.get(definitionId)
            if typeTuple:
                type = typeTuple[0]
                typeStr = typeTuple[1]
            else:
                type = cls.GRAPH_NODE
                typeStr = definitionId
        return (type, typeStr)

    @classmethod
    def hasSystemContent(cls, type):
        return type == cls.FX_MAP or type == cls.PIXEL_PROCESSOR or type == cls.VALUE_PROCESSOR
    
    @classmethod
    def isSystemContent(cls, type):
        return type >= cls.SYSTEM_CONTENT and type < cls.SYSTEM_CONTENT_END

    @classmethod
    def isGraphNode(cls, type):
        return type >= cls.GRAPH_NODE and type < cls.GRAPH_NODE_LAST

    @classmethod
    def isGraph(cls, type):
        return type == cls.GRAPH or type == cls.FX_MAP_GRAPH

    @classmethod
    def isFunction(cls, type):
        return type == cls.FUNCTION or type == cls.VALUE_PROCESSOR_FUNC or type == cls.PIXEL_PROCESSOR_FUNC

    @classmethod
    def nodeWithSystemContentName(cls, type):
        name = cls.NODE_WITH_SYSTEM_CONTENT_NAME.get(type)
        return name if name else ""

    @classmethod
    def systemGraphName(cls, type):
        name = cls.SYSTEM_GRAPH_NAME.get(type)
        return name if name else ""
    
    @classmethod
    def systemContentType(cls, nodeWithSystemContentType):
        type = None
        if nodeWithSystemContentType == cls.FX_MAP:
            type = cls.FX_MAP_GRAPH
        elif nodeWithSystemContentType == cls.PIXEL_PROCESSOR:
            type = cls.PIXEL_PROCESSOR_FUNC
        elif nodeWithSystemContentType == cls.VALUE_PROCESSOR:
            type = cls.VALUE_PROCESSOR_FUNC
        return type

    @classmethod
    def functionNodeTypeName(cls, type):
        name = ""
        if type == cls.FNODE_GET:
            name = "Get"
        elif type == cls.FNODE_SET:
            name = "Set"
        return name

    @classmethod
    def typeStrForNonObjType(cls, type):
    # typeStr from type when type cannot be determined from the sdObj alone
        typeStr = ""
        if type == cls.FUNC_INPUTS:
            typeStr = "Function inputs"
        elif type == cls.FUNC_INPUT:
            typeStr = "Function input"
        return typeStr

    @classmethod
    def isTypeGraphObject(cls, type):
        return type >= cls.GRAPHOBJECT and type < cls.GRAPHOBJECT_LAST

    @classmethod
    def isTypeFunctionNode(cls, type):
        return type >= cls.FUNCTION_NODE and type < cls.FUNCTION_NODE_LAST

    @classmethod
    # Node that can be present in Explorer view
    def isExplorerNode(cls, type):
        return type == cls.FUNCTION or type == cls.FOLDER or type == cls.GRAPH

    @classmethod
    def name(cls, sdObj, type):
        name = ""
        if type == cls.GRAPH_NODE:
            name = sdObj.getDefinition().getLabel()
        elif type >= cls.FXMAP_GRAPH_NODE and type <= cls.FXMAP_GRAPH_NODE_LAST:
            _,typeStr = cls.type(sdObj)
            name = typeStr
        elif type == cls.PACKAGE:
            name = Path(sdObj.getFilePath()).stem
        elif cls.isTypeGraphObject(type):
            name = sdObj.getDescription()
        elif cls.isTypeFunctionNode(type):
            name = cls.functionNodeTypeName(type)
        elif type == cls.FUNC_INPUTS:
            name = cls.typeStrForNonObjType(type)
        elif cls.hasSystemContent(type):
            name = cls.nodeWithSystemContentName(type)
        elif type == cls.GRAPH or type == cls.FUNCTION or type == cls.FOLDER:
            name = sdObj.getIdentifier()
            if not name or len(name) == 0:
                name = sdObj.getClassName()
        elif type == cls.GRAPH_INSTANCE:
            graph = sdObj.getReferencedResource()
            if graph and isinstance(graph, SDGraph):
                try:
                    name = graph.getAnnotationPropertyValueFromId("label").get()
                except:
                    pass
                finally:
                    if not name or len(name) == 0:
                        name = graph.getIdentifier()
        return name
    
    @classmethod
    def dumpStr(cls, sdObj):
        if sdObj is None:
            return "(None)"
        type, typeStr = cls.type(sdObj)
        name = cls.name(sdObj, type)
        return "sdObj: " +str(sdObj) + " type: " + typeStr + " name: " + name
    
    @classmethod
    def constantName(cls, constantValue):
        for name, value in inspect.getmembers(cls):
            if not name.startswith("__") and value == constantValue:
                return name
        return None    
