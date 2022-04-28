# ---------------
# Global Search - Substance 3D Designer plugin
# (c) 2019-2022 Eyosido Software SARL
# ---------------

import os
from PySide2.QtUiTools import QUiLoader
from PySide2 import QtGui, QtWidgets
from PySide2.QtCore import Qt

import sd
from globalsearch.gscore.sdobj import SDObj 

class GSUIUtil:
    """
    General purpose UI and UI+SD related utilities
    """
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
        if nodeType == SDObj.PACKAGE:
            iconFilename = "gs_package.png"
        elif nodeType == SDObj.GRAPH:
            iconFilename = "gs_graph.png"
        elif nodeType == SDObj.FOLDER:
            iconFilename = "gs_folder.png"
        elif nodeType == SDObj.FUNCTION:
            iconFilename = "gs_function.png"
        elif nodeType == SDObj.COMMENT:
            iconFilename = "gs_comment.png"
        elif nodeType == SDObj.FRAME:
            iconFilename = "gs_frame.png"
        elif nodeType == SDObj.FNODE_GET:
            iconFilename = "gs_func_get.png"
        elif nodeType == SDObj.FNODE_SET:
            iconFilename = "gs_func_set.png"
        elif nodeType == SDObj.FUNC_INPUT:
            iconFilename = "gs_func_input.png"
        elif nodeType == SDObj.PARAM_INPUT:
            iconFilename = "gs_input.png"
        elif SDObj.isGraphNode(nodeType):
            iconFilename = "gs_graph_node.png"
        elif nodeType == SDObj.FUNC_CALL:
            iconFilename = "gs_func_call.png"
        elif nodeType == SDObj.FUNC_PARAM:
            iconFilename = "gs_func_param.png"
                       
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