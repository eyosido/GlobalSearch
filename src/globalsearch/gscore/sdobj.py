# ---------------
# Global Search - Substance 3D Designer plugin
# (c) 2019-2022 Eyosido Software SARL
# ---------------

from pathlib import Path

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

    # Nodes that can be found inside a regular graph
    GRAPH_NODE = 100    # any graph node unless the specifics below
    FX_MAP = 101
    PIXEL_PROCESSOR = 102
    VALUE_PROCESSOR = 103
    GRAPH_INSTANCE = 104    # node representing a graph, either system (i.e. Switch node) or user graph
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
            if definitionId == "sbs::compositing::fxmaps":
                type = cls.FX_MAP
                typeStr = "fx-map"
            elif definitionId == "sbs::compositing::pixelprocessor":
                type = cls.PIXEL_PROCESSOR
                typeStr = "pixel processor"
            elif definitionId == "sbs::compositing::valueprocessor":
                type = cls.VALUE_PROCESSOR
                typeStr = "value processor"
            elif definitionId == "sbs::compositing::sbscompgraph_instance":
                type = cls.GRAPH_INSTANCE
                typeStr = "graph instance"
            else:
                type = cls.GRAPH_NODE
                typeStr = definitionId
        return (type, typeStr)

    @classmethod
    def isSpecialSubgraphType(cls, type):
        return type == cls.FX_MAP or type == cls.PIXEL_PROCESSOR or type == cls.VALUE_PROCESSOR

    @classmethod
    def isGraphNode(cls, type):
        return type >= cls.GRAPH_NODE and type < cls.GRAPH_NODE_LAST

    @classmethod
    def specialSubgraphTypeName(cls, type):
        name = ""
        if type == cls.FX_MAP:
            name = "FX-Map"
        elif type == cls.PIXEL_PROCESSOR:
            name = "Pixel Processor"
        elif type == cls.VALUE_PROCESSOR:
            name = "Value Procssor"
        elif type == cls.GRAPH_INSTANCE:
            name = "Graph instance"
        return name

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
    # Node that can be present in Exporer view
    def isExporerNode(cls, type):
        return type == cls.FUNCTION or type == cls.FOLDER or type == cls.GRAPH

    @classmethod
    def name(cls, sdObj, type):
        name = ""
        if type == cls.GRAPH_NODE:
            name = sdObj.getDefinition().getLabel()
        elif type == cls.PACKAGE:
            name = Path(sdObj.getFilePath()).stem
        elif cls.isTypeGraphObject(type):
            name = sdObj.getDescription()
        elif cls.isTypeFunctionNode(type):
            name = cls.functionNodeTypeName(type)
        elif type == cls.FUNC_INPUTS:
            name = cls.typeStrForNonObjType(type)
        elif cls.isSpecialSubgraphType(type):
            name = cls.specialSubgraphTypeName(type)
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
