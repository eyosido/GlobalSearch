# ---------------
# Global Search - Substance 3D Designer plugin
# (c) 2019-2025 Eyosido Software SARL
# ---------------

import sd
if sd.getContext().getSDApplication().getVersion() < "14.0.0":
    from PySide2 import QtCore, QtWidgets
    from PySide2.QtCore import Qt
    from PySide2.QtWidgets import QVBoxLayout, QHBoxLayout
else:
    from PySide6 import QtCore, QtWidgets
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout

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
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint | Qt.WindowCloseButtonHint)
        self.setWindowTitle(self.gsuiMgr.APPNAME + " Preferences")
        self.setupStaticUI()

    def showEvent(self, event):
        super().showEvent(event)
        self.setFixedSize(self.size())  # makes the window fixed size/not resizeable

    def setupStaticUI(self):
        main_layout = QVBoxLayout(self)

        # --- Search Criteria
        self.gb_search_criteria = QtWidgets.QGroupBox("Search Filters")
        main_layout.addWidget(self.gb_search_criteria)

        search_criteria_group_layout = QVBoxLayout()
        self.gb_search_criteria.setLayout(search_criteria_group_layout)

        filters_layout = QHBoxLayout()
        search_criteria_group_layout.addLayout(filters_layout)

        general_filters_layout = QVBoxLayout()
        filters_layout.addLayout(general_filters_layout)

        self.chk_graph_name = QtWidgets.QCheckBox(self.gb_search_criteria)
        general_filters_layout.addWidget(self.chk_graph_name)
        self.chk_graph_name.setToolTip("Search into graph id and label")
        self.chk_graph_name.setText("Graph name")
        self.chk_folder_name = QtWidgets.QCheckBox(self.gb_search_criteria)
        general_filters_layout.addWidget(self.chk_folder_name)
        self.chk_folder_name.setToolTip("Search into folder id")
        self.chk_folder_name.setText("Folder name")
        self.chk_comment = QtWidgets.QCheckBox(self.gb_search_criteria)
        general_filters_layout.addWidget(self.chk_comment)
        self.chk_comment.setToolTip("Search into comments and frames")
        self.chk_comment.setText("Comment / Frame")
        self.chk_display_node_type_filters = QtWidgets.QCheckBox(self.gb_search_criteria)
        general_filters_layout.addWidget(self.chk_display_node_type_filters)
        self.chk_display_node_type_filters.setToolTip("Display Node Type filters in the main search view. These enable to tailor the search to certain node types.")
        self.chk_display_node_type_filters.setText("Display Node Type filters")
        general_filters_layout.addStretch(1)

        function_filters_layout = QVBoxLayout()
        filters_layout.addLayout(function_filters_layout)

        self.chk_func_name = QtWidgets.QCheckBox(self.gb_search_criteria)
        function_filters_layout.addWidget(self.chk_func_name)
        self.chk_func_name.setToolTip("Search into function id or label")   
        self.chk_func_name.setText("Function name")
        self.chk_func_input_param = QtWidgets.QCheckBox(self.gb_search_criteria)
        function_filters_layout.addWidget(self.chk_func_input_param)
        self.chk_func_input_param.setToolTip("Search into function input parameter id")
        self.chk_func_input_param.setText("Input parameter")
        self.chk_func_getter = QtWidgets.QCheckBox(self.gb_search_criteria)
        function_filters_layout.addWidget(self.chk_func_getter)
        self.chk_func_getter.setToolTip("Search into variables used in Get function nodes")
        self.chk_func_getter.setText("Variable Getter")
        self.chk_func_setter = QtWidgets.QCheckBox(self.gb_search_criteria)
        function_filters_layout.addWidget(self.chk_func_setter)
        self.chk_func_setter.setToolTip("Search into variables used in Set function nodes")
        self.chk_func_setter.setText("Variable Setter")
        self.chk_graphParamFunc = QtWidgets.QCheckBox(self.gb_search_criteria)
        function_filters_layout.addWidget(self.chk_graphParamFunc)
        self.chk_graphParamFunc.setToolTip("Search into graph input parameter functions")
        self.chk_graphParamFunc.setText("Graph parameter function")

        # --- Search History
        self.gb_search_history = QtWidgets.QGroupBox("Search History")
        main_layout.addWidget(self.gb_search_history)

        search_history_group_layout = QVBoxLayout()
        self.gb_search_history.setLayout(search_history_group_layout)

        search_history_content_layout = QHBoxLayout()
        search_history_group_layout.addLayout(search_history_content_layout)

        self.chk_sh_enable = QtWidgets.QCheckBox(self.gb_search_history)
        search_history_content_layout.addWidget(self.chk_sh_enable)
        self.chk_sh_enable.setToolTip("The last few search entries leading to results will be kept in a persistent list")
        self.chk_sh_enable.setText("Enable search history")
        self.pb_sh_clear = QtWidgets.QPushButton(self.gb_search_history)
        search_history_content_layout.addWidget(self.pb_sh_clear)
        self.pb_sh_clear.setToolTip("Clear the current search history")
        self.pb_sh_clear.setText("Clear search history")

        # --- Search Options
        self.gb_search_process = QtWidgets.QGroupBox("Search Options")
        main_layout.addWidget(self.gb_search_process)

        search_process_group_layout = QVBoxLayout()
        self.gb_search_process.setLayout(search_process_group_layout)

        search_process_content_layout = QHBoxLayout()
        search_process_group_layout.addLayout(search_process_content_layout)

        search_process_left_col_layout = QVBoxLayout()
        search_process_content_layout.addLayout(search_process_left_col_layout)

        self.chk_whole_word = QtWidgets.QCheckBox(self.gb_search_process)
        search_process_left_col_layout.addWidget(self.chk_whole_word)
        self.chk_whole_word.setToolTip("Whether the search is matching whole words (i.e. not searching inside words/terms)")
        self.chk_whole_word.setText("Whole Word")

        self.chk_case_sensitive = QtWidgets.QCheckBox(self.gb_search_process)
        search_process_left_col_layout.addWidget(self.chk_case_sensitive)
        self.chk_case_sensitive.setToolTip("Whether the search is case sensitive")
        self.chk_case_sensitive.setText("Case sensitive")

        self.chk_disp_node_ids = QtWidgets.QCheckBox(self.gb_search_process)
        search_process_left_col_layout.addWidget(self.chk_disp_node_ids)
        self.chk_disp_node_ids.setToolTip("Displays numerical node identifiers in search results")
        self.chk_disp_node_ids.setText("Display node Ids")

        search_process_right_col_layout = QVBoxLayout()
        search_process_content_layout.addLayout(search_process_right_col_layout)

        self.chk_enter_subgraphs = QtWidgets.QCheckBox(self.gb_search_process)
        search_process_right_col_layout.addWidget(self.chk_enter_subgraphs)
        self.chk_enter_subgraphs.setToolTip("Enbter custom graphs being referenced into the currently parsed graph. Since these sub graphs are also\n"
"referenced independently in the package, this may lead to duplicate search results and longer search time.")
        self.chk_enter_subgraphs.setText("Enter user sub-graphs")

        self.chk_enter_pkg_func = QtWidgets.QCheckBox(self.gb_search_process)
        search_process_right_col_layout.addWidget(self.chk_enter_pkg_func)
        self.chk_enter_pkg_func.setToolTip("Search into package functions being called from graphs\'s parameter functions.\n"
"Package functions are already searched as located inside the package (or a folder)\n"
"so you may want to disable this option to avoid duplicate search results\n"
"if you are also searching in graphs.")
        self.chk_enter_pkg_func.setText("Enter pkg functions in function graphs")

        search_process_right_col_layout.addStretch(1)

        # gb_bottom = QtWidgets.QGroupBox()
        # main_layout.addWidget(gb_bottom)

        bottom_group_layout = QHBoxLayout()
        # gb_bottom.setLayout(bottom_group_layout)
        # main_layout.addWidget(gb_bottom)
        main_layout.addLayout(bottom_group_layout)

        from globalsearch.gsui.gsuimgr import GSUIManager
        from globalsearch.gscore.gs import GlobalSearch
        l_about = QtWidgets.QLabel("<i>"+GSUIManager.APPNAME + " v" + GlobalSearch.VERSION+"</i>")
        bottom_group_layout.addWidget(l_about)

        self.buttonBox = QtWidgets.QDialogButtonBox()
        bottom_group_layout.addWidget(self.buttonBox)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Ok)

        self.enableStateChangeListeners()
        self.pb_sh_clear.clicked.connect(self.onClearSearchHistoryClicked)

        self.buttonBox.accepted.connect(self.onAccept)
        self.buttonBox.rejected.connect(self.onReject)

    def enableStateChangeListeners(self):
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
        self.chk_display_node_type_filters.setChecked(prefs.sc_DisplayNodeTypeFilters)
        self.chk_func_name.setChecked(prefs.sc_FuncName)
        self.chk_func_input_param.setChecked(prefs.sc_FuncInputParam)
        self.chk_func_getter.setChecked(prefs.sc_FuncGetter)
        self.chk_func_setter.setChecked(prefs.sc_FuncSetter)
        self.chk_graphParamFunc.setChecked(prefs.sc_GraphParamFunc)

        self.chk_sh_enable.setChecked(prefs.sh_enable)

        self.chk_case_sensitive.setChecked(prefs.sp_caseSensitive)
        self.chk_whole_word.setChecked(prefs.sp_wholeWord)
        self.chk_enter_pkg_func.setChecked(prefs.sp_enterGraphPkgFct)
        self.chk_enter_subgraphs.setChecked(prefs.sp_enterCustomSubGraphs)

        self.chk_disp_node_ids.setChecked(prefs.sp_displayNodeIds)

    def saveToPrefs(self):
        prefs = self.gsuiMgr.prefs
        prefs.sc_GraphName = self.chk_graph_name.isChecked()
        prefs.sc_FolderName = self.chk_folder_name.isChecked()
        prefs.sc_Comment = self.chk_comment.isChecked()
        prefs.sc_DisplayNodeTypeFilters = self.chk_display_node_type_filters.isChecked()
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

        prefs.sp_caseSensitive = self.chk_case_sensitive.isChecked()
        prefs.sp_wholeWord = self.chk_whole_word.isChecked()
        prefs.sp_enterGraphPkgFct = self.chk_enter_pkg_func.isChecked()
        prefs.sp_enterCustomSubGraphs = self.chk_enter_subgraphs.isChecked()
        prefs.sp_displayNodeIds = self.chk_disp_node_ids.isChecked()
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

    def onClearSearchHistoryClicked(self):
        if self.gsuiMgr.uiWidget.searchHistory:
            if GSUIUtil.askYesNoQuestion("Clear Search History?", self):
                self.gsuiMgr.uiWidget.searchHistory.clear()
        
    def onAccept(self):
        self.saveToPrefs()
        self.gsuiMgr.updateFromPrefs()
        self.gsuiMgr.uiWidget.searchResultTreeWidget.updateFromPrefs()
        self.accept()

    def onReject(self):
        self.reject()
