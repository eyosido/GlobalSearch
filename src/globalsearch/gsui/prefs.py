# ---------------
# Global Search - Substance 3D Designer plugin
# (c) 2019-2025 Eyosido Software SARL
# ---------------

import os
import json

from globalsearch.gscore import gslog
from globalsearch.gscore.searchdata import SearchCriteria

class GSUIPref:
    """
    Holding Preferences, non UI form
    """

    """
    Preferences file format versions:
    4: removed sp_naturalSearch, added sp_wholeWord, dev_unitTests, dev_searchLogs
    3: added sp_displayNodeIds
    2: added sc_GraphParamFunc
    1: initial version
    """
    VERSION = "4"
    
    def __init__(self):
        self.setupDefaults()
        self.path = self.__class__.filename()
        self.load()
        if not os.path.exists(self.path):
            self.save()
     
    def setupDefaults(self):
        self.version = self.__class__.VERSION
        self.sc_GraphName = True
        self.sc_FolderName = True
        self.sc_Comment = True
        self.sc_DisplayNodeTypeFilters = True
        self.sc_FuncName = True
        self.sc_FuncInputParam = True
        self.sc_FuncGetter = True
        self.sc_FuncSetter = True
        self.sc_GraphParamFunc = True

        self.sh_enable = True 

        self.sp_caseSensitive = False
        self.sp_wholeWord = False
        self.sp_enterGraphPkgFct = False
        self.sp_enterCustomSubGraphs = False
        self.sp_displayNodeIds = True
        
        # development only, not visible in the UI
        self.dev_unitTests = False # enables unit test menus
        self.dev_searchLogs = False # detailed logs during a search
        
    @classmethod
    def filename(cls):
        path = os.path.dirname(os.path.dirname(__file__)) # go one folder up
        path = os.path.join(path ,"gsprefs.json")
        return path

    def load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r") as readFile:
                    j = json.load(readFile)
                self.__dict__.update(j)
                self.version = self.__class__.VERSION # force current version
            except:
                gslog.error("Error loading preferences.")

    def save(self):
        try:
            with open(self.path, "w") as writeFile: 
                json.dump(self.__dict__, writeFile)
        except:
            gslog.error("Error saving preferences.")

    def toSearchCriteria(self):
        sc = SearchCriteria()

        sc.caseSensitive = self.sp_caseSensitive
        sc.wholeWord = self.sp_wholeWord
        sc.enterGraphPkgFct = self.sp_enterGraphPkgFct
        sc.enterCustomSubGraphs = self.sp_enterCustomSubGraphs

        # filters
        sc.varGetter = self.sc_FuncGetter
        sc.varSetter = self.sc_FuncSetter
        sc.folderId = self.sc_FolderName
        sc.graphName = self.sc_GraphName
        sc.graphParamFunc = self.sc_GraphParamFunc
        sc.funcName = self.sc_FuncName
        sc.funcInput = self.sc_FuncInputParam
        sc.comment = self.sc_Comment

        return sc
