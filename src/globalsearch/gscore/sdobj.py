# ---------------
# Global Search - Substance 3D Designer plugin
# (c) 2019-2025 Eyosido Software SARL
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
from sd.api.sbs.sdsbsfxmapnode import SDSBSFxMapNode
from sd.api.sdresourcefolder import SDResourceFolder
from sd.api.sdgraphobjectcomment import SDGraphObjectComment
from sd.api.sdgraphobjectframe import SDGraphObjectFrame
from sd.api.sdgraphobjectpin import SDGraphObjectPin

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
    VALUE_PROCESSOR = 101
    FX_MAP = 102
    BLEND = 103
    CURVE = 104
    PIXEL_PROCESSOR = 105
    SVG = 106
    BITMAP = 107
    SHUFFLE = 108
    NORMAL = 109
    UNIFORM = 110
    HSL = 111
    BLUR = 112
    GRADIENT = 113 
    DYN_GRADIENT = 114
    PASSTHROUGH = 115
    DIRMOTION_BLUR = 116
    SHARPEN = 117
    TEXT = 118
    TRANSFORMATION = 119
    DIRECTIONAL_WARP = 120
    GRAYSCALE_CONVERSION = 121 
    DISTANCE = 122
    LEVELS = 123
    EMBOSS = 124
    WARP = 125
    INPUT_COLOR = 126
    INPUT_GRAYSCALE = 127
    INPUT_VALUE = 128
    OUTPUT = 129

    GRAPH_INSTANCE = 150    # node representing a graph, either system (i.e. Switch node) or user graph

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

    # graph objects (comment/frame/pins)
    GRAPHOBJECT = 300
    COMMENT = 301
    FRAME = 302
    PIN = 303
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

    SDNODE_COMPOSITING_TYPE = { # mapping definitionId to node (type, typeStr)
        # Compositing nodes
        "sbs::compositing::valueprocessor": (VALUE_PROCESSOR, "Value Processor"),
        "sbs::compositing::fxmaps": (FX_MAP, "FX-Map"),
        "sbs::compositing::blend": (BLEND, "Blend"),
        "sbs::compositing::curve": (CURVE, "Curve"),
        "sbs::compositing::pixelprocessor": (PIXEL_PROCESSOR, "Pixel Processor"),
        "sbs::compositing::svg": (SVG, "SVG"),
        "sbs::compositing::bitmap": (BITMAP, "Bitmap"),
        "sbs::compositing::shuffle": (SHUFFLE, "Channels Suffle"),
        "sbs::compositing::normal": (NORMAL, "Normal"),
        "sbs::compositing::uniform": (UNIFORM, "Uniform Color"),
        "sbs::compositing::hsl": (HSL, "HSL"),
        "sbs::compositing::blur": (BLUR, "Blur"),
        "sbs::compositing::gradient": (GRADIENT, "Gradient Map"),
        "sbs::compositing::dyngradient": (DYN_GRADIENT, "Dynamic Gradient"),
        "sbs::compositing::passthrough": (PASSTHROUGH, "Dot"),
        "sbs::compositing::dirmotionblur": (DIRMOTION_BLUR, "Directional Blur"),
        "sbs::compositing::sharpen": (SHARPEN, "Sharpen"),
        "sbs::compositing::text": (TEXT, "Text"),
        "sbs::compositing::transformation": (TRANSFORMATION, "Transformation"),
        "sbs::compositing::directionalwarp": (DIRECTIONAL_WARP, "Directional Warp"),
        "sbs::compositing::grayscaleconversion": (GRAYSCALE_CONVERSION, "Grayscale Conversion"),
        "sbs::compositing::distance": (DISTANCE, "Distance"),
        "sbs::compositing::levels": (LEVELS, "Levels"),
        "sbs::compositing::emboss": (EMBOSS, "Emboss"),
        "sbs::compositing::warp": (WARP, "Warp"),
        "sbs::compositing::input_color": (INPUT_COLOR, "Input Color"),
        "sbs::compositing::input_grayscale": (INPUT_GRAYSCALE, "Input Grayscale"),
        "sbs::compositing::input_value": (INPUT_VALUE, "Input Value"),
        "sbs::compositing::output": (OUTPUT, "Output"),

        "sbs::compositing::sbscompgraph_instance": (GRAPH_INSTANCE, "Graph Instance")
    }

    SDNODE_FXMAP_TYPE = {
        "sbs::fxmap::paramset": (FXMAP_QUADRANT, "Quadrant"),
        "sbs::fxmap::markov2": (FXMAP_SWITCH, "Switch"),
        "sbs::fxmap::addnode": (FXMAP_ITERATE, "Iterate"),
        "sbs::fxmap::passthrough": (FXMAP_DOT, "Dot")
    }

    NODE_FUNCTION_TYPE = {
        "sbs::function::const_float1": (FUNCTION_NODE, "Float"),
        "sbs::function::const_float2": (FUNCTION_NODE, "Float2"),
        "sbs::function::const_float3": (FUNCTION_NODE, "Float3"),
        "sbs::function::const_float4": (FUNCTION_NODE, "Float4"),
        "sbs::function::const_int1": (FUNCTION_NODE, "Int"),
        "sbs::function::const_int2": (FUNCTION_NODE, "Int2"),
        "sbs::function::const_int3": (FUNCTION_NODE, "Int3"),
        "sbs::function::const_int4": (FUNCTION_NODE, "Int4"),
        "sbs::function::const_bool": (FUNCTION_NODE, "Bool"),
        "sbs::function::const_string": (FUNCTION_NODE, "String"),
        "sbs::function::vector2": (FUNCTION_NODE, "Vector Float2"),
        "sbs::function::vector3": (FUNCTION_NODE, "Vector Float3"),
        "sbs::function::vector4": (FUNCTION_NODE, "Vector Float4"),
        "sbs::function::swizzle1": (FUNCTION_NODE, "Swizzle Float1"),
        "sbs::function::swizzle2": (FUNCTION_NODE, "Swizzle Float2"),
        "sbs::function::swizzle3": (FUNCTION_NODE, "Swizzle Float3"),
        "sbs::function::swizzle4": (FUNCTION_NODE, "Swizzle Float4"),
        "sbs::function::ivector2": (FUNCTION_NODE, "Vector Integer2"),
        "sbs::function::ivector3": (FUNCTION_NODE, "Vector Integer3"),
        "sbs::function::ivector4": (FUNCTION_NODE, "Vector Integer4"),
        "sbs::function::iswizzle1": (FUNCTION_NODE, "Swizzle Integer1"),
        "sbs::function::iswizzle2": (FUNCTION_NODE, "Swizzle Integer2"),
        "sbs::function::iswizzle3": (FUNCTION_NODE, "Swizzle Integer3"),
        "sbs::function::iswizzle4": (FUNCTION_NODE, "Swizzle Integer4"),
        "sbs::function::set": (FUNCTION_NODE, "Set"),
        "sbs::function::get_float1": (FUNCTION_NODE, "Get Float"),
        "sbs::function::get_float2": (FUNCTION_NODE, "Get Float2"),
        "sbs::function::get_float3": (FUNCTION_NODE, "Get Float3"),
        "sbs::function::get_float4": (FUNCTION_NODE, "Get Float4"),
        "sbs::function::get_integer1": (FUNCTION_NODE, "Get Integer"),
        "sbs::function::get_integer2": (FUNCTION_NODE, "Get Integer2"),
        "sbs::function::get_integer3": (FUNCTION_NODE, "Get Integer3"),
        "sbs::function::get_integer4": (FUNCTION_NODE, "Get Integer4"),
        "sbs::function::get_bool": (FUNCTION_NODE, "Get Bool"),
        "sbs::function::samplelum": (FUNCTION_NODE, "Sample Gray"),
        "sbs::function::samplecol": (FUNCTION_NODE, "Sample Color"),
        "sbs::function::tofloat": (FUNCTION_NODE, "To Float"),
        "sbs::function::tofloat2": (FUNCTION_NODE, "To Float2"),
        "sbs::function::tofloat3": (FUNCTION_NODE, "To Float3"),
        "sbs::function::tofloat4": (FUNCTION_NODE, "To Float4"),
        "sbs::function::toint1": (FUNCTION_NODE, "To Int"),
        "sbs::function::toint2": (FUNCTION_NODE, "To Int2"),
        "sbs::function::toint3": (FUNCTION_NODE, "To Int3"),
        "sbs::function::toint4": (FUNCTION_NODE, "To Int4"),
        "sbs::function::add": (FUNCTION_NODE, "Add"),
        "sbs::function::sub": (FUNCTION_NODE, "Subtraction"),
        "sbs::function::mul": (FUNCTION_NODE, "Multiplication"),
        "sbs::function::mulscalar": (FUNCTION_NODE, "Scalar Multiplication"),
        "sbs::function::div": (FUNCTION_NODE, "Division"),
        "sbs::function::neg": (FUNCTION_NODE, "Negation"),
        "sbs::function::mod": (FUNCTION_NODE, "Modulo"),
        "sbs::function::dot": (FUNCTION_NODE, "Dot Product"),
        "sbs::function::and": (FUNCTION_NODE, "And"),
        "sbs::function::or": (FUNCTION_NODE, "Or"),
        "sbs::function::not": (FUNCTION_NODE, "Not"),
        "sbs::function::eq": (FUNCTION_NODE, "Equal"),
        "sbs::function::noteq": (FUNCTION_NODE, "Not Equal"),
        "sbs::function::gt": (FUNCTION_NODE, "Greater"),
        "sbs::function::gteq": (FUNCTION_NODE, "Greater or Equal"),
        "sbs::function::lr": (FUNCTION_NODE, "Lower"),
        "sbs::function::lreq": (FUNCTION_NODE, "Lower or Equal"),
        "sbs::function::abs": (FUNCTION_NODE, "Absolute"),
        "sbs::function::floor": (FUNCTION_NODE, "Floor"),
        "sbs::function::ceil": (FUNCTION_NODE, "Ceil"),
        "sbs::function::cos": (FUNCTION_NODE, "Cosine"),
        "sbs::function::sin": (FUNCTION_NODE, "Sine"),
        "sbs::function::tan": (FUNCTION_NODE, "Tangent"),
        "sbs::function::atan2": (FUNCTION_NODE, "Arc Tangent 2"),
        "sbs::function::cartesian": (FUNCTION_NODE, "Cartesian"),
        "sbs::function::sqrt": (FUNCTION_NODE, "Square Root"),
        "sbs::function::log": (FUNCTION_NODE, "Logarithm"),
        "sbs::function::exp": (FUNCTION_NODE, "Exponential"),
        "sbs::function::log2": (FUNCTION_NODE, "Logarithm base 2"),
        "sbs::function::pow2": (FUNCTION_NODE, "2Pow"),
        "sbs::function::pow2": (FUNCTION_NODE, "Pow"),
        "sbs::function::lerp": (FUNCTION_NODE, "Linear Interpolation"),
        "sbs::function::min": (FUNCTION_NODE, "Minimum"),
        "sbs::function::max": (FUNCTION_NODE, "Maximum"),
        "sbs::function::rand": (FUNCTION_NODE, "Random"),
        "sbs::function::sequence": (FUNCTION_NODE, "Sequence"),
        "sbs::function::ifelse": (FUNCTION_NODE, "If...Else"),
        "sbs::function::while": (FUNCTION_NODE, "While Loop"),
        "sbs::function::passthrough": (FUNCTION_NODE, "Dot"),
    }

    @classmethod
    def type(cls, sdObj):
        type = cls.UNDEFINED
        typeStr = ""
        if isinstance(sdObj, SDPackage):
            type = cls.PACKAGE
            typeStr = "Package"
        elif isinstance(sdObj, SDSBSFunctionGraph):
            type = cls.FUNCTION
            typeStr = "Function"
        elif isinstance(sdObj, SDGraph):
            type = cls.GRAPH
            typeStr = "Graph"
        elif isinstance(sdObj, SDSBSFunctionNode):
            defId = sdObj.getDefinition().getId()
            if defId.startswith("sbs::function::get"):
                type = cls.FNODE_GET
                typeStr = "Get"
            elif defId.startswith("sbs::function::set"):
                type = cls.FNODE_SET
                typeStr = "Set"
        elif isinstance(sdObj, SDGraphObjectComment):
            type = cls.COMMENT
            typeStr = "Comment"
        elif isinstance(sdObj, SDGraphObjectPin):
            type = cls.PIN
            typeStr = "Pin"
        elif isinstance(sdObj, SDGraphObjectFrame):
            type = cls.FRAME
            typeStr = "Frame"
        elif isinstance(sdObj, SDResourceFolder):  
            type = cls.FOLDER  
            typeStr = "Folder"
        elif isinstance(sdObj, SDSBSFxMapNode):
            definitionId = sdObj.getDefinition().getId()
            typeTuple = cls.SDNODE_FXMAP_TYPE.get(definitionId)
            if typeTuple:
                type = typeTuple[0]
                typeStr = typeTuple[1]
        elif isinstance(sdObj, SDNode):
            definitionId = sdObj.getDefinition().getId()
            typeTuple = cls.SDNODE_COMPOSITING_TYPE.get(definitionId)
            if typeTuple:
                type = typeTuple[0]
                typeStr = typeTuple[1]
            else:
                type = cls.GRAPH_NODE
                typeStr = definitionId
        return (type, typeStr)
    
    @classmethod
    def isInputNode(cls, type):
        return type == cls.INPUT_GRAYSCALE or type == cls.INPUT_COLOR or type == cls.INPUT_VALUE

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
    # Node that can be present in Explorer view
    def isFXMapNode(cls, type):
        return type >= cls.FXMAP_GRAPH_NODE and type <= cls.FXMAP_GRAPH_NODE_LAST

    @classmethod
    def name(cls, sdObj, type):
        name = ""
        if type == cls.GRAPH_NODE:
            name = sdObj.getDefinition().getLabel()
        elif cls.isFXMapNode(type):
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
