# ---------------
# Global Search - Substance 3D Designer plugin
# (c) 2019-2025 Eyosido Software SARL
# ---------------

import importlib

from globalsearch.gscore import gslog, gs, sdobj, searchdata, gssdlibrary, gspresets
from globalsearch.gstests import gsunittests
from globalsearch.gsui import gsuimgr, gsuiwidget, prefs, prefsdlg, resulttree, searchhistory, searchroottree, uiutil

def initializeSDPlugin():
    importlib.reload(gslog)
    importlib.reload(gs)
    importlib.reload(sdobj)
    importlib.reload(searchdata)
    importlib.reload(gspresets)    
    importlib.reload(gssdlibrary)
    importlib.reload(gsuimgr)
    importlib.reload(gsuiwidget)
    importlib.reload(prefs)
    importlib.reload(prefsdlg)
    importlib.reload(resulttree)
    importlib.reload(searchhistory)
    importlib.reload(searchroottree)
    importlib.reload(uiutil)
    importlib.reload(gsunittests)

    gslog.GSLogger.classInit()
    gsuimgr.GSUIManager.classInit()
    gssdlibrary.GSSDLibrary.classInit()
    gslog.info(gsuimgr.g_gsuimgr.APPNAME + " starting")
    gsuimgr.g_gsuimgr.setupUI()

def uninitializeSDPlugin():
    gslog.info(gsuimgr.GSUIManager.APPNAME + " ending")
    gsuimgr.g_gsuimgr.removeUI()
    gsuimgr.GSUIManager.classDeinit()
    gssdlibrary.GSSDLibrary.classDeinit()
    gslog.info(gsuimgr.GSUIManager.APPNAME + " ended")
    gslog.GSLogger.classDeinit()

