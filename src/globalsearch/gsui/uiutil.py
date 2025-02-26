# ---------------
# Global Search - Substance 3D Designer plugin
# (c) 2019-2022 Eyosido Software SARL
# ---------------

import os

import sd
if sd.getContext().getSDApplication().getVersion() < "14.0.0":
    from PySide2.QtUiTools import QUiLoader
    from PySide2 import QtGui, QtWidgets
    from PySide2.QtCore import Qt
else:
    from PySide6.QtUiTools import QUiLoader
    from PySide6 import QtGui, QtWidgets
    from PySide6.QtCore import Qt
    
from globalsearch.gscore.sdobj import SDObj 
from globalsearch.gscore.gslog import GSLogger

class GSUIUtil:
    """
    General purpose UI and UI+SD related utilities
    """
    TYPE_ICON_FILE = {
        SDObj.PACKAGE: "gs_package.png",
        SDObj.GRAPH: "gs_graph.png",
        SDObj.FX_MAP_GRAPH: "gs_graph.png",
        SDObj.PIXEL_PROCESSOR_FUNC: "gs_function.png",
        SDObj.VALUE_PROCESSOR_FUNC: "gs_function.png",
        SDObj.FOLDER: "gs_folder.png",
        SDObj.FUNCTION: "gs_function.png",
        SDObj.COMMENT: "gs_comment.png",
        SDObj.FRAME: "gs_frame.png",
        SDObj.FNODE_GET: "gs_func_get.png",
        SDObj.FNODE_SET: "gs_func_set.png",
        SDObj.FUNC_INPUT: "gs_func_input.png",
        SDObj.PARAM_INPUT: "gs_input.png",
        SDObj.FUNC_CALL: "gs_func_call.png",
        SDObj.FUNC_PARAM: "gs_func_param.png"
    }

    @classmethod
    def loadUI(cls, uiFilename):
        curdir = os.path.dirname(__file__)
        path = os.path.join(curdir,"ui/" + uiFilename)
        return QUiLoader().load(path)

    @classmethod
    def filePathForIcon(cls, iconFilename):
        return os.path.join(os.path.dirname(__file__), "img", iconFilename)

    @classmethod
    def iconWithFilename(cls, iconFilename, scaledHeight = -1):
        pixmap = QtGui.QPixmap(cls.filePathForIcon(iconFilename))
        if scaledHeight != -1:
            pixmap = pixmap.scaledToHeight(scaledHeight, Qt.TransformationMode.SmoothTransformation)
        icon = QtGui.QIcon(pixmap)
        return icon

    @classmethod
    def iconForSDObj(cls, nodeType, scaledHeight = -1):
        iconFilename = None
        icon = None

        if SDObj.isGraphNode(nodeType):
            iconFilename = "gs_graph_node.png"
        else:
            iconFilename = cls.TYPE_ICON_FILE.get(nodeType)
                       
        if iconFilename:
            icon = cls.iconWithFilename(iconFilename, scaledHeight)
        
        return icon

    @classmethod
    def croppedText(cls, text, maxLen = 50):
        if text and len(text) > maxLen:
            finalText = text[:maxLen] + "(...)"
        else:
            finalText = text
        return finalText

    @classmethod
    def croppedTextCenteredAroundSubstring(cls, substring, text, maxLen = 50):
        # return text centered around substring
        textLen = len(text)
        if text and textLen > maxLen:
            subStart = text.find(substring)
            posAtSubMid = subStart + int(len(substring)/2)
            start = posAtSubMid - int(maxLen/2)
            if start < 0:
                start = 0

            lastIndex = textLen - 1
            end = start + maxLen
            if end >= textLen:
                end = lastIndex
            
            finalText = ""
            if start > 0:
                finalText += "(...)"
            finalText += text[start:end+1]
            if end < lastIndex:
                finalText += "(...)"
        else:
            finalText = text
        return finalText

    @classmethod
    def displayErrorMsg(cls, msg, parent = None):
        from globalsearch.gsui.gsuimgr import GSUIManager
        p = parent if parent else sd.getContext().getSDApplication().getQtForPythonUIMgr().getMainWindow()
        QtWidgets.QMessageBox.critical(p, GSUIManager.APPNAME, msg)

    @classmethod
    def displayInfoMsg(cls, msg, parent = None):
        from globalsearch.gsui.gsuimgr import GSUIManager
        p = parent if parent else sd.getContext().getSDApplication().getQtForPythonUIMgr().getMainWindow()
        QtWidgets.QMessageBox.information(p, GSUIManager.APPNAME, msg)

    @classmethod
    def askYesNoQuestion(cls, msg, parent = None):
        from globalsearch.gsui.gsuimgr import GSUIManager
        p = parent if parent else sd.getContext().getSDApplication().getQtForPythonUIMgr().getMainWindow()
        return QtWidgets.QMessageBox.question(p, GSUIManager.APPNAME, msg) == QtWidgets.QMessageBox.Yes
    
    @classmethod
    def graphViewIDFromGraph(cls, graph):
        uiMgr = sd.getContext().getSDApplication().getUIMgr()
        count = uiMgr.getGraphViewIDCount()
        for i in range(0, count):
            graphViewID = uiMgr.getGraphViewIDAt(i)
            g = uiMgr.getGraphFromGraphViewID(graphViewID)
            if g.getIdentifier() == graph.getIdentifier():
                return graphViewID
        return None
