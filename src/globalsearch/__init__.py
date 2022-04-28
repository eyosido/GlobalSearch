# ---------------
# Global Search - Substance 3D Designer plugin
# (c) 2019-2022 Eyosido Software SARL
# ---------------

import importlib

import sd
from sd.context import Context
from sd.api.sdpackage import SDPackage
from sd.api.sdarray import SDArray
from sd.api.sdgraph import SDGraph
from sd.api.sduimgr import SDUIMgr
from sd.api.sdapplication import SDApplication
from globalsearch.gscore import gslog
from globalsearch.gscore import gs
from globalsearch.gscore import sdobj
from globalsearch.gscore import searchdata
from globalsearch.gsui import gsuimgr
from globalsearch.gsui import prefs
from globalsearch.gsui import prefsdlg
from globalsearch.gsui import resulttree
from globalsearch.gsui import searchhistory
from globalsearch.gsui import searchroottree
from globalsearch.gsui import uiutil

def initializeSDPlugin():
    # module reloads enable modifications without restarting the host, used for development only
    importlib.reload(gslog)
    importlib.reload(gs)
    importlib.reload(sdobj)
    importlib.reload(searchdata)
    importlib.reload(gsuimgr)
    importlib.reload(prefs)
    importlib.reload(prefsdlg)
    importlib.reload(resulttree)
    importlib.reload(searchhistory)
    importlib.reload(searchroottree)
    importlib.reload(uiutil)

    gslog.GSLogger.instance().log(gsuimgr.GSUIManager.APPNAME + " starting")

    gsuimgr.GSUIManager.instance()

def uninitializeSDPlugin():
    gsuimgr.GSUIManager.instance().removeUI()
    gsuimgr.GSUIManager.inst = None
    gslog.log(gsuimgr.GSUIManager.APPNAME + " ending")
    gslog.GSLogger.destroyLogger()

