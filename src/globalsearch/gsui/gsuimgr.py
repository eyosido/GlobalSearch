# ---------------
# Global Search - Substance 3D Designer plugin
# (c) 2019-2022 Eyosido Software SARL
# ---------------

from enum import Enum
import os

import sd
if sd.getContext().getSDApplication().getVersion() < "14.0.0":
    from PySide2 import QtCore, QtWidgets, QtGui
    from PySide2.QtCore import QObject, Signal, Slot, QModelIndex, Qt, QEvent, QTimer
    from PySide2.QtUiTools import QUiLoader
    from PySide2.QtWidgets import QVBoxLayout, QWidget, QSlider, QLabel, QTreeWidget, QComboBox, QLineEdit, QTreeWidgetItemIterator, QSizePolicy
else:
    from PySide6 import QtCore, QtWidgets, QtGui
    from PySide6.QtCore import QObject, Signal, Slot, QModelIndex, Qt, QEvent, QTimer
    from PySide6.QtUiTools import QUiLoader
    from PySide6.QtWidgets import QVBoxLayout, QWidget, QSlider, QLabel, QTreeWidget, QComboBox, QLineEdit, QTreeWidgetItemIterator, QSizePolicy

from globalsearch.gscore import gslog
from globalsearch.gsui.prefs import GSUIPref
from globalsearch.gsui.gsuiwidget import GSUIWidget

class GSUIManager:
    """
    Main UI handler
    """
    APPNAME = "Global Search"

    @classmethod
    def classInit(cls):
        global g_gsuimgr
        g_gsuimgr = GSUIManager()
 
    def __init__(self):
        app = sd.getContext().getSDApplication()
        self.uiMgr = app.getQtForPythonUIMgr()
        self.prefs = GSUIPref()
        self.uiWidget = None

    def setupUI(self):
        self.dockWidget =  self.uiMgr.newDockWidget('global_search', self.__class__.APPNAME)
        self.uiWidget = GSUIWidget(self)

        boxLayout = QVBoxLayout()
        self.dockWidget.setLayout(boxLayout)
        boxLayout.addWidget(self.uiWidget.ui)

    def removeUI(self):
        gslog.info("Remove UI")
                
        if self.dockWidget:
            if self.uiWidget.ui:
                self.uiWidget.ui.deleteLater()
                self.uiWidget.ui = None

            self.dockWidget.close()
            self.dockWidget.parent().close()

            # self.uiMgr.getMainWindow().removeDockWidget(self.dockWidget.parent())
            self.dockWidget = None
        else:
            gslog.error("dockWidget not found, cannot delete it.")

