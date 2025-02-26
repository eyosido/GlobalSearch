# ---------------
# Global Search - Substance 3D Designer plugin
# (c) 2019-2022 Eyosido Software SARL
# ---------------

import sd
if sd.getContext().getSDApplication().getVersion() < "14.0.0":
    from PySide2 import QtCore, QtWidgets
    from PySide2.QtCore import Qt
else:
    from PySide6 import QtCore, QtWidgets
    from PySide6.QtCore import Qt

from globalsearch.gsui.uiutil import GSUIUtil

class GSUIPrefsDlg(QtWidgets.QDialog):
    """
    Preferences dialog
    """
    def __init__(self, gsuiMgr, parent=None):
        super().__init__(parent)
        self.gsuiMgr = gsuiMgr
        self.setObjectName("GSUIPrefsDlg")
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint | Qt.WindowCloseButtonHint) # remove the Help icon in title bar

        self.setWindowTitle(self.gsuiMgr.APPNAME + " Preferences")
        self.setFixedSize(480, 485)

        self.buttonBox = QtWidgets.QDialogButtonBox(self)
        self.buttonBox.setGeometry(QtCore.QRect(220, 450, 251, 32))
        self.buttonBox.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gb_search_criteria = QtWidgets.QGroupBox(self)
        self.gb_search_criteria.setGeometry(QtCore.QRect(10, 10, 411, 201))
        self.gb_search_criteria.setObjectName("gb_search_criteria")
        self.chk_graph_name = QtWidgets.QCheckBox(self.gb_search_criteria)
        self.chk_graph_name.setGeometry(QtCore.QRect(10, 30, 111, 23))
        self.chk_graph_name.setObjectName("chk_graph_name")
        self.chk_folder_name = QtWidgets.QCheckBox(self.gb_search_criteria)
        self.chk_folder_name.setGeometry(QtCore.QRect(10, 57, 111, 23))
        self.chk_folder_name.setObjectName("chk_folder_name")
        self.chk_comment = QtWidgets.QCheckBox(self.gb_search_criteria)
        self.chk_comment.setGeometry(QtCore.QRect(10, 84, 151, 23))
        self.chk_comment.setObjectName("chk_comment")
        self.chk_function = QtWidgets.QCheckBox(self.gb_search_criteria)
        self.chk_function.setGeometry(QtCore.QRect(200, 30, 70, 23))
        self.chk_function.setObjectName("chk_function")
        self.chk_func_name = QtWidgets.QCheckBox(self.gb_search_criteria)
        self.chk_func_name.setGeometry(QtCore.QRect(220, 57, 111, 23))
        self.chk_func_name.setObjectName("chk_func_name")
        self.chk_func_input_param = QtWidgets.QCheckBox(self.gb_search_criteria)
        self.chk_func_input_param.setGeometry(QtCore.QRect(220, 84, 111, 23))
        self.chk_func_input_param.setObjectName("chk_func_input_param")
        self.chk_func_getter = QtWidgets.QCheckBox(self.gb_search_criteria)
        self.chk_func_getter.setGeometry(QtCore.QRect(220, 111, 111, 23))
        self.chk_func_getter.setObjectName("chk_func_getter")
        self.chk_func_setter = QtWidgets.QCheckBox(self.gb_search_criteria)
        self.chk_func_setter.setGeometry(QtCore.QRect(220, 138, 101, 23))
        self.chk_func_setter.setObjectName("chk_func_setter")
        self.chk_graphParamFunc = QtWidgets.QCheckBox(self.gb_search_criteria)
        self.chk_graphParamFunc.setGeometry(QtCore.QRect(220, 165, 171, 23))
        self.chk_graphParamFunc.setObjectName("chk_graphParamFunc")
        self.l_about = QtWidgets.QLabel(self)
        self.l_about.setGeometry(QtCore.QRect(10, 455, 141, 20))
        self.l_about.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.l_about.setObjectName("l_about")
        self.gb_search_process = QtWidgets.QGroupBox(self)
        self.gb_search_process.setGeometry(QtCore.QRect(10, 320, 460, 121))
        self.gb_search_process.setObjectName("gb_search_process")
        self.chk_natural_search = QtWidgets.QCheckBox(self.gb_search_process)
        self.chk_natural_search.setGeometry(QtCore.QRect(10, 30, 141, 23))
        self.chk_natural_search.setObjectName("chk_natural_search")
        self.chk_case_sensitive = QtWidgets.QCheckBox(self.gb_search_process)
        self.chk_case_sensitive.setGeometry(QtCore.QRect(10, 57, 151, 23))
        self.chk_case_sensitive.setObjectName("chk_case_sensitive")
        self.chk_enter_pkg_func = QtWidgets.QCheckBox(self.gb_search_process)
        self.chk_enter_pkg_func.setGeometry(QtCore.QRect(220, 57, 280, 23))
        self.chk_enter_pkg_func.setObjectName("chk_enter_pkg_func")
        self.chk_enter_subgraphs = QtWidgets.QCheckBox(self.gb_search_process)
        self.chk_enter_subgraphs.setGeometry(QtCore.QRect(220, 30, 181, 23))
        self.chk_enter_subgraphs.setObjectName("chk_enter_subgraphs")
        self.chk_disp_node_ids = QtWidgets.QCheckBox(self.gb_search_process)
        self.chk_disp_node_ids.setGeometry(QtCore.QRect(10, 84, 141, 23))
        self.chk_disp_node_ids.setObjectName("chk_disp_node_ids")
        self.gb_search_history = QtWidgets.QGroupBox(self)
        self.gb_search_history.setGeometry(QtCore.QRect(10, 230, 411, 71))
        self.gb_search_history.setObjectName("gb_search_history")
        self.chk_sh_enable = QtWidgets.QCheckBox(self.gb_search_history)
        self.chk_sh_enable.setGeometry(QtCore.QRect(10, 30, 181, 23))
        self.chk_sh_enable.setObjectName("chk_sh_enable")
        self.pb_sh_clear = QtWidgets.QPushButton(self.gb_search_history)
        self.pb_sh_clear.setGeometry(QtCore.QRect(220, 25, 171, 23))
        self.pb_sh_clear.setObjectName("pb_sh_clear")

        self.gb_search_criteria.setTitle(QtWidgets.QApplication.translate("GSUIPrefsDlg", "Search Filters", None, -1))
        self.chk_graph_name.setToolTip(QtWidgets.QApplication.translate("GSUIPrefsDlg", "Search into graph id and label", None, -1))
        self.chk_graph_name.setText(QtWidgets.QApplication.translate("GSUIPrefsDlg", "Graph name", None, -1))
        self.chk_folder_name.setToolTip(QtWidgets.QApplication.translate("GSUIPrefsDlg", "Search into folder id", None, -1))
        self.chk_folder_name.setText(QtWidgets.QApplication.translate("GSUIPrefsDlg", "Folder name", None, -1))
        self.chk_comment.setToolTip(QtWidgets.QApplication.translate("GSUIPrefsDlg", "Search into comments and frames", None, -1))
        self.chk_comment.setText(QtWidgets.QApplication.translate("GSUIPrefsDlg", "Comment / Frame", None, -1))
        self.chk_function.setText(QtWidgets.QApplication.translate("GSUIPrefsDlg", "Function", None, -1))
        self.chk_func_name.setToolTip(QtWidgets.QApplication.translate("GSUIPrefsDlg", "Search into function id or label", None, -1))
        self.chk_func_name.setText(QtWidgets.QApplication.translate("GSUIPrefsDlg", "Function name", None, -1))
        self.chk_func_input_param.setToolTip(QtWidgets.QApplication.translate("GSUIPrefsDlg", "Search into function input parameter id", None, -1))
        self.chk_func_input_param.setText(QtWidgets.QApplication.translate("GSUIPrefsDlg", "Input parameter", None, -1))
        self.chk_func_getter.setToolTip(QtWidgets.QApplication.translate("GSUIPrefsDlg", "Search into variables used in Get function nodes", None, -1))
        self.chk_func_getter.setText(QtWidgets.QApplication.translate("GSUIPrefsDlg", "Variable Getter", None, -1))
        self.chk_func_setter.setToolTip(QtWidgets.QApplication.translate("GSUIPrefsDlg", "Search into variables used in Set function nodes", None, -1))
        self.chk_func_setter.setText(QtWidgets.QApplication.translate("GSUIPrefsDlg", "Variable Setter", None, -1))
        self.chk_graphParamFunc.setToolTip(QtWidgets.QApplication.translate("GSUIPrefsDlg", "Search into graph input parameter functions", None, -1))
        self.chk_graphParamFunc.setText(QtWidgets.QApplication.translate("GSUIPrefsDlg", "Graph parameter function", None, -1))
        self.l_about.setText(QtWidgets.QApplication.translate("GSUIPrefsDlg", "Global Search", None, -1))
        self.gb_search_process.setTitle(QtWidgets.QApplication.translate("GSUIPrefsDlg", "Search Options", None, -1))
        self.chk_natural_search.setToolTip(QtWidgets.QApplication.translate("GSUIPrefsDlg", "Natural mode searches in the content of parsed items. If disabled, search is made \n"
"for exact match except in comments or description fields where search is still being \n"
"made in content. Also, the * wildcard character may be used at the beginning and/or \n"
"end of the search string when Natural mode is disabled.", None, -1))
        self.chk_natural_search.setText(QtWidgets.QApplication.translate("GSUIPrefsDlg", "Natural search", None, -1))
        self.chk_case_sensitive.setToolTip(QtWidgets.QApplication.translate("GSUIPrefsDlg", "Whether the search is case sensitive", None, -1))
        self.chk_case_sensitive.setText(QtWidgets.QApplication.translate("GSUIPrefsDlg", "Case sensitive", None, -1))
        self.chk_enter_pkg_func.setToolTip(QtWidgets.QApplication.translate("GSUIPrefsDlg", "Search into package functions being called from graphs\'s parameter functions.\n"
"Package functions are already searched as located inside the package (or a folder)\n"
"so you may want to disable this option to avoid duplicate search results\n"
"if you are also searching in graphs.", None, -1))
        self.chk_enter_pkg_func.setText(QtWidgets.QApplication.translate("GSUIPrefsDlg", "Enter pkg functions in function graphs", None, -1))
        self.chk_enter_subgraphs.setToolTip(QtWidgets.QApplication.translate("GSUIPrefsDlg", "Enbter custom graphs being referenced into the currently parsed graph. Since these sub graphs are also\n"
"referenced independently in the package, this may lead to duplicate search results and longer search time.", None, -1))
        self.chk_enter_subgraphs.setText(QtWidgets.QApplication.translate("GSUIPrefsDlg", "Enter user sub-graphs", None, -1))
        self.chk_disp_node_ids.setText(QtWidgets.QApplication.translate("GSUIPrefsDlg", "Display node Ids", None, -1))
        self.gb_search_history.setTitle(QtWidgets.QApplication.translate("GSUIPrefsDlg", "Search History", None, -1))
        self.chk_sh_enable.setToolTip(QtWidgets.QApplication.translate("GSUIPrefsDlg", "The last few search entries leading to results will be kept in a persistent list", None, -1))
        self.chk_sh_enable.setText(QtWidgets.QApplication.translate("GSUIPrefsDlg", "Enable search history", None, -1))
        self.pb_sh_clear.setToolTip(QtWidgets.QApplication.translate("GSUIPrefsDlg", "Clear the current search history", None, -1))
        self.pb_sh_clear.setText(QtWidgets.QApplication.translate("GSUIPrefsDlg", "Clear search history", None, -1))

        self.enableStateChangeListeners()
        self.pb_sh_clear.clicked.connect(self.onClearSearchHistoryClicked)

        self.buttonBox.accepted.connect(self.onAccept)
        self.buttonBox.rejected.connect(self.onReject)

        from globalsearch.gsui.gsuimgr import GSUIManager
        from globalsearch.gscore.gs import GlobalSearch
        self.l_about.setText(GSUIManager.APPNAME + " v" + GlobalSearch.VERSION)

    def enableStateChangeListeners(self):
            self.chk_function.stateChanged.connect(self.onFunctionStateChanged)
            self.chk_func_name.stateChanged.connect(self.onFunctionSubStateChanged)
            self.chk_func_input_param.stateChanged.connect(self.onFunctionSubStateChanged)
            self.chk_func_getter.stateChanged.connect(self.onFunctionSubStateChanged)
            self.chk_func_setter.stateChanged.connect(self.onFunctionSubStateChanged)
            self.chk_graphParamFunc.stateChanged.connect(self.onFunctionSubStateChanged)

    def setupFromPrefs(self):
        prefs = self.gsuiMgr.prefs
        self.chk_graph_name.setChecked(prefs.sc_GraphName)
        self.chk_folder_name.setChecked(prefs.sc_FolderName)
        self.chk_comment.setChecked(prefs.sc_Comment)
        self.chk_func_name.setChecked(prefs.sc_FuncName)
        self.chk_func_input_param.setChecked(prefs.sc_FuncInputParam)
        self.chk_func_getter.setChecked(prefs.sc_FuncGetter)
        self.chk_func_setter.setChecked(prefs.sc_FuncSetter)
        self.chk_graphParamFunc.setChecked(prefs.sc_GraphParamFunc)

        self.chk_sh_enable.setChecked(prefs.sh_enable)

        self.chk_natural_search.setChecked(prefs.sp_naturalSearch)
        self.chk_case_sensitive.setChecked(prefs.sp_caseSensitive)
        self.chk_enter_pkg_func.setChecked(prefs.sp_enterGraphPkgFct)
        self.chk_enter_subgraphs.setChecked(prefs.sp_enterCustomSubGraphs)

        self.chk_disp_node_ids.setChecked(prefs.sp_display_node_ids)

    def saveToPrefs(self):
        prefs = self.gsuiMgr.prefs
        prefs.sc_GraphName = self.chk_graph_name.isChecked()
        prefs.sc_FolderName = self.chk_folder_name.isChecked()
        prefs.sc_Comment = self.chk_comment.isChecked()
        prefs.sc_FuncName = self.chk_func_name.isChecked()
        prefs.sc_FuncInputParam = self.chk_func_input_param.isChecked()
        prefs.sc_FuncGetter = self.chk_func_getter.isChecked()
        prefs.sc_FuncSetter = self.chk_func_setter.isChecked()
        prefs.sc_GraphParamFunc = self.chk_graphParamFunc.isChecked()

        newSearchHistoryEnable = self.chk_sh_enable.isChecked()
        if prefs.sh_enable != newSearchHistoryEnable:
            # search history has been enabled or disabled since opening, update UI
            if newSearchHistoryEnable:
                self.gsuiMgr.uiWidget.setupSearchHistory()
            else:
                self.gsuiMgr.uiWidget.disableSearchHistory()

            prefs.sh_enable = self.chk_sh_enable.isChecked()

        prefs.sp_naturalSearch = self.chk_natural_search.isChecked()
        prefs.sp_caseSensitive = self.chk_case_sensitive.isChecked()
        prefs.sp_enterGraphPkgFct = self.chk_enter_pkg_func.isChecked()
        prefs.sp_enterCustomSubGraphs = self.chk_enter_subgraphs.isChecked()
        prefs.sp_display_node_ids = self.chk_disp_node_ids.isChecked()
        prefs.save()

    def onFunctionStateChanged(self, state):
        self.chk_func_name.setChecked(state)
        self.chk_func_input_param.setChecked(state)
        self.chk_func_getter.setChecked(state)
        self.chk_func_setter.setChecked(state)
        self.chk_graphParamFunc.setChecked(state)

    def onFunctionSubStateChanged(self, state):
        allChecked = self.chk_func_name.isChecked() and self.chk_func_input_param.isChecked() and \
            self.chk_func_getter.isChecked() and self.chk_func_setter.isChecked() and self.chk_graphParamFunc.isChecked()

        self.chk_function.stateChanged.disconnect(self.onFunctionStateChanged)
        self.chk_function.setChecked(allChecked)
        self.chk_function.stateChanged.connect(self.onFunctionStateChanged)

    def onClearSearchHistoryClicked(self):
        if self.gsuiMgr.uiWidget.searchHistory:
            if GSUIUtil.askYesNoQuestion("Clear Search History?", self):
                self.gsuiMgr.uiWidget.searchHistory.clear()
        
    def onAccept(self):
        self.saveToPrefs()
        self.gsuiMgr.uiWidget.searchResultTreeWidget.updateFromPrefs()
        self.accept()

    def onReject(self):
        self.reject()
