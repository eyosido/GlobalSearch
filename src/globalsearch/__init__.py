# ---------------
# Global Search - Substance 3D Designer plugin
# (c) 2019-2022 Eyosido Software SARL
# ---------------

import importlib

from globalsearch.gscore import gslog, gs, sdobj, searchdata
from globalsearch.gsui import gsuimgr, gsuiwidget, prefs, prefsdlg, resulttree, searchhistory, searchroottree, uiutil

def initializeSDPlugin():
    # reload libs for development only
    importlib.reload(gslog)
    importlib.reload(gs)
    importlib.reload(sdobj)
    importlib.reload(searchdata)
    importlib.reload(gsuimgr)
    importlib.reload(gsuiwidget)
    importlib.reload(prefs)
    importlib.reload(prefsdlg)
    importlib.reload(resulttree)
    importlib.reload(searchhistory)
    importlib.reload(searchroottree)
    importlib.reload(uiutil)

    gslog.GSLogger.classInit()
    gsuimgr.GSUIManager.classInit()
    gslog.info(gsuimgr.g_gsuimgr.APPNAME + " starting")
    gsuimgr.g_gsuimgr.setupUI()

def uninitializeSDPlugin():
    gslog.info(gsuimgr.GSUIManager.APPNAME + " ending")
    gsuimgr.g_gsuimgr.removeUI()
    gsuimgr.g_gsuimgr = None
    gslog.info(gsuimgr.GSUIManager.APPNAME + " ended")
    gslog.g_gslog.destroy()

