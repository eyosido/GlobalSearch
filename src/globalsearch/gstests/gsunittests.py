# ---------------
# Global Search - Substance 3D Designer plugin
# (c) 2019-2025 Eyosido Software SARL
# ---------------

import json, sd, os
if sd.getContext().getSDApplication().getVersion() < "14.0.0":
    from PySide2.QtCore import QTimer
else:
    from PySide6.QtCore import QTimer

from sd.api.sdgraph import SDGraph
from sd.api.sdresourcefolder import SDResourceFolder
from sd.api.sbs.sdsbsfunctiongraph import SDSBSFunctionGraph

from globalsearch.gscore import gslog
from globalsearch.gscore.gs import GlobalSearch
from globalsearch.gscore.searchdata import SearchResults, SearchCriteria, SearchResultPathNodeJSONEncoder, NoteTypeFilterData
from globalsearch.gscore.sdobj import SDObj
from globalsearch.gscore import gssdlibrary

class GSUnitTests:
    # HOW TO RUN TESTS:
    # To run these tests, the reference packages "gs_unit_tests_pkg1.sbs" and "gs_unit_tests_pkg2.sbs" must be open in Designer (and only these). Running a test compares its result
    # with a reference test results found into file "gs_unit_test_results.json" located into the "gstests" folder. If test results are same the test is displayed as
    # PASSED else as FAILED. When making modifications to the plugin code, the reference packages or the tests descriptions below (either modifying an existing test or adding new ones),
    # the reference test results "gs_unit_test_results.json" must be regenerated, this is explained below in section "HOW TO RECORD TESTS".
    #
    # To run the tests:
    # - Start the plugin with "dev_unitTests" to true in Preferences file gsprefs.json, this make a "Global Search" top level menu in the application menu bar available (plusing needs to be restarted).
    # - To run all the tests, use the "Global Search/Run Unit Tests" menu, test results will be logged into the Console view. 
    # - To run a single test, use the "Global Search/Tests" menu which contains individual tests. If "Display Test Result In Tree View" menu is selected, the test result
    # and search string will be displayed in the tree view. This is useful to verify a test is providing the expected result before recording.
    #
    # HOW TO RECORD TESTS:
    # When making modifications to the plugin code, reference packages ("gs_unit_tests_pkg1.sbs" and "gs_unit_tests_pkg2.sbs") or the test description below such as modifying
    # a test description or adding a new one, the reference test results file "gs_unit_test_results.json" must be regenerated, else the comparison of the new tests with a not
    # up-to-date test results file will fail. To regernate this file, please proceed as follows:
    # - test your new of modified tests individually, displaying their results into the tree view.
    # - use the "Global Search/Run Unit Tests" menu to make sure the other tests are still passing (in case of modification of the plugin code, this helps checking for regressions).
    # The new tests will not be marked as PASSED at this stage but this is normal since they are not in the reference test results file. If modifications have been made into the
    # reference packages, some tests may fail, even though they are still valid, make sure to double-check these after the new reference test results is generated.
    # - when you are done checking the validity of the new tests or changes, use the "Global Search/Run Unit Tests (Record)" menu. This will generate a "gs_unit_test_results.json" file
    # in the "globalsearch" directory (same location as the "gsprefs.json"). To make this file the new reference test result file, it needs to moved manually to the "gstests" folder and
    # replace the former one.
    # - "Global Search/Run Unit Tests" can now be run and all the tests should be PASSED.
    #
    # Reference test results into "gs_unit_test_results.json" provided with the tool have been generated with the current version of Substance 3D Designer at the time of release. They may
    # not all pass when using a different version, it doesn't necessarilly mean the tool has a problem with these tests, but some differences in naming or other content may occur.

    # These are the test descriptions. Each test is dedined by a dict item whose key is the test id (string) and value has the following fields:
    # - name: name of the test (free form text)
    # - root: name of the root to search from, format: x:name where x is the type of container, either of:
    #   p: package
    #   f: folder
    #   g: graph
    #   pf: package function
    # - searchCriteria: an override of the default search criteria (see SearchCriteria() constructor for default values) except for node filters (see below)
    # - graphNodeFilter and functionNodeFilter: these are defined outside of searchCriteria and their value is either:
    #   . the definition of the node for system nodes
    #   . the id of the node for library nodes

    TESTS = {
        # Filters in Preferences
        'preferences_filter_1': { 'name': '"graph" no comments/frames', 'root': '', 'searchCriteria':{'searchString': "graph", 'comment':False}},
        'preferences_filter_2': { 'name': '"graph_" no graph name', 'root': '', 'searchCriteria':{'searchString': "graph_", 'graphName':False}},
        'preferences_filter_3': { 'name': '"package" no folder name', 'root': '', 'searchCriteria':{'searchString': "package", 'folderId':False}},
        'preferences_filter_4': { 'name': '"pkg" no function name', 'root': '', 'searchCriteria':{'searchString': "pkg", 'funcName':False}},
        'preferences_filter_5': { 'name': '"input" no function input', 'root': '', 'searchCriteria':{'searchString': "input", 'funcInput':False}},
        'preferences_filter_6': { 'name': '"var" no getter', 'root': '', 'searchCriteria':{'searchString': "var", 'varGetter':False}},
        'preferences_filter_7': { 'name': '"var" no setter', 'root': '', 'searchCriteria':{'searchString': "var", 'varSetter':False}},
        'preferences_filter_8': { 'name': '"return" no param func', 'root': '', 'searchCriteria':{'searchString': "return", 'graphParamFunc':False}},

        # Search types
        'search_type_1': { 'name': '"my" Whole Word disabled', 'root': '', 'searchCriteria':{'searchString': "my"}},
        'search_type_2': { 'name': '"my" Whole Word enabled', 'root': '', 'searchCriteria':{'searchString': "my", "wholeWord":True}},
        'search_type_3': { 'name': '"my*" post-wildcard search, Whole Word enabled', 'root': '', 'searchCriteria':{'searchString': "my*", "wholeWord":True}},
        'search_type_4': { 'name': '"*var" pre-wildcard search, Whole Word enabled', 'root': '', 'searchCriteria':{'searchString': "*var", "wholeWord":True}},
        'search_type_5': { 'name': '"*va*" pre-post-wildcard search, Whole Word enabled', 'root': '', 'searchCriteria':{'searchString': "*va*", "wholeWord":True}},
        'search_type_6': { 'name': '"this" case insensitive', 'root': '', 'searchCriteria':{'searchString': "this"}},
        'search_type_7': { 'name': '"this" case sensitive', 'root': '', 'searchCriteria':{'searchString': "this", "caseSensitive":True}},

        # Search roots:
        'search_root_1': { 'name': '"test" from global root', 'root': '', 'searchCriteria':{'searchString': "test"}},
        'search_root_2': { 'name': '"test" from root package gs_unit_tests_pkg1', 'root': 'p:gs_unit_tests_pkg1', 'searchCriteria':{'searchString': "test"}},
        'search_root_3': { 'name': '"test" from root graph test_graph_1', 'root': 'g:test_graph_1', 'searchCriteria':{'searchString': "test"}},
        'search_root_4': { 'name': '"test" from graph test_subgraph_1 in folder', 'root': 'g:test_subgraph_1', 'searchCriteria':{'searchString': "test"}},
        'search_root_5': { 'name': '"test" from folder test_package_functions', 'root': 'f:test_package_functions', 'searchCriteria':{'searchString': "test"}},
        'search_root_6': { 'name': '"test" from nested folder test_util_functions', 'root': 'f:test_util_functions', 'searchCriteria':{'searchString': "test"}},
        'search_root_7': { 'name': '"test" from root pkg function root_pkg_function', 'root': 'pf:root_pkg_function', 'searchCriteria':{'searchString': "test"}},
        'search_root_8': { 'name': '"test" from pkg function test_return_1 in folder', 'root': 'pf:test_return_1', 'searchCriteria':{'searchString': "test"}},

        # Containers:
        'containers_1': { 'name': '"here" enter sub-graph', 'root': '', 'searchCriteria':{'searchString': "here", 'enterCustomSubGraphs':True}},
        'containers_2': { 'name': '"var" enter package function', 'root': '', 'searchCriteria':{'searchString': "var", 'enterGraphPkgFct':True}},

        # Single result
        'single_result_1': { 'name': '"this is a test return" single result from root', 'root': '', 'searchCriteria':{'searchString': "this is a test return"}},
        'single_result_2': { 'name': '"this is a test return" single result item', 'root': 'pf:root_pkg_function', 'searchCriteria':{'searchString': "this is a test return"}},
        
        # FX-Map:
        'fxmap_1':  { 'name': '"fxm" enter an FX-Map', 'root': '', 'searchCriteria':{'searchString': "fxm"}},
        'fxmap_2':  { 'name': '"my_fmx_var" inside FX-Map Switch selector fct', 'root': '', 'searchCriteria':{'searchString': "my_fmx_var"}},
        'fxmap_3':  { 'name': '"size" inside FX-Map Quadrant size fct', 'root': '', 'searchCriteria':{'searchString': "size"}},

        # Pixel Processor:
        'pixelprocessor_1':  { 'name': '"pixproc" enter a Pixel Processor', 'root': '', 'searchCriteria':{'searchString': "pixproc"}},
        'pixelprocessor_2':  { 'name': '"#test_offset" in Pixel Processor', 'root': '', 'searchCriteria':{'searchString': "#test_offset"}},
        'pixelprocessor_3':  { 'name': '"return" pkg function call in Pixel Processor', 'root': '', 'searchCriteria':{'searchString': "return"}},
        'pixelprocessor_4':  { 'name': '"$pos" in Pixel Processor', 'root': '', 'searchCriteria':{'searchString': "$pos"}},

        # Value Processor
        'valueprocessor_1':  { 'name': '"valproc" in Value Processor', 'root': '', 'searchCriteria':{'searchString': "valproc"}},
        'valueprocessor_2':  { 'name': '"add" in Value Processor', 'root': '', 'searchCriteria':{'searchString': "add"}},

        # Search into labels:
        'labels_1': { 'name': '"My test graph 2" graph label', 'root': '', 'searchCriteria':{'searchString': "My test graph 2"}},
        
        # graph node filters for nodes having system content (Pixel Processor etc.)
        'gnf_sys_content_1':  { 'name': '"test_offset" filtered by Pixel Processor', 'root': '', 'searchCriteria':{'searchString': "test_offset"}, 'graphNodeFilter': "sbs::compositing::pixelprocessor"},
        'gnf_sys_content_2':  { 'name': '"my_fmx_var" filtered by FX-Map', 'root': '', 'searchCriteria':{'searchString': "my_fmx_var"}, 'graphNodeFilter': "sbs::compositing::fxmaps"},
        'gnf_sys_content_3':  { 'name': '"fxm Switch" filtered by FX-Map', 'root': '', 'searchCriteria':{'searchString': "fxm Switch"}, 'graphNodeFilter': "sbs::compositing::fxmaps"},
        'gnf_sys_content_4':  { 'name': '"size" in test_graph_1 filtered by Quadrant', 'root': 'g:test_graph_1', 'searchCriteria':{'searchString': "size"}, 'graphNodeFilter': "sbs::fxmap::paramset"},
        'gnf_sys_content_5':  { 'name': '"test" in test_graph_1 filtered by Switch', 'root': 'g:test_graph_1', 'searchCriteria':{'searchString': "test"}, 'graphNodeFilter': "sbs::fxmap::markov2"},
        'gnf_sys_content_6':  { 'name': '"test" in test_graph_1 filtered by FX-Map', 'root': 'g:test_graph_1', 'searchCriteria':{'searchString': "test"}, 'graphNodeFilter': "sbs::compositing::fxmaps"},
        
        # Input and Output node identifiers
        'input_output_1': { 'name': '"dirt" part the id of an Input node', 'root': '', 'searchCriteria':{'searchString': "dirt"}},
        'input_output_2': { 'name': '"normal" part the id of an output node', 'root': '', 'searchCriteria':{'searchString': "normal"}},

        # System graph node filters
        'sys_graph_node_filters_1': { 'name': '"test" in Blend nodes', 'root': '', 'searchCriteria':{'searchString': "test"}, 'graphNodeFilter': "sbs::compositing::blend"},
        'sys_graph_node_filters_2': { 'name': '"test" in Normal nodes', 'root': '', 'searchCriteria':{'searchString': "test", 'enterCustomSubGraphs':True}, 'graphNodeFilter': "sbs::compositing::normal"},
        'sys_graph_node_filters_3': { 'name': '"test" in Normal nodes, enter pkg fcts', 'root': '', 'searchCriteria':{'searchString': "test", 'enterGraphPkgFct':True}, 'graphNodeFilter': "sbs::compositing::normal"},
        'sys_graph_node_filters_4': { 'name': 'All Blend nodes', 'root': '', 'searchCriteria':{'searchString': ""}, 'graphNodeFilter': "sbs::compositing::blend"},
        'sys_graph_node_filters_5': { 'name': '"test" in Input Grayscale nodes', 'root': '', 'searchCriteria':{'searchString': "test"}, 'graphNodeFilter': "sbs::compositing::input_grayscale"},
        'sys_graph_node_filters_6': { 'name': '"test" in Ouput nodes', 'root': '', 'searchCriteria':{'searchString': "test"}, 'graphNodeFilter': "sbs::compositing::output"},

        # Library graph node filters
        'lib_graph_node_filters_1': { 'name': '"test" in Blur HQ Grayscale', 'root': '', 'searchCriteria':{'searchString': "test"}, 'graphNodeFilter': "blur_hq_grayscale"},
        'lib_graph_node_filters_2': { 'name': 'Blur HQ Grayscale nodes', 'root': '', 'searchCriteria':{'searchString': ""}, 'graphNodeFilter': "blur_hq_grayscale"},
        'lib_graph_node_filters_3': { 'name': 'test_return_1 pkg function in Blur HQ Grayscale nodes', 'root': '', 'searchCriteria':{'searchString': "test_return_1"}, 'graphNodeFilter': "blur_hq_grayscale"},

        # Function node filters
        'function_node_filters_1': { 'name': '"my_test_var" get float1 from test_return_1', 'root': 'pf:test_return_1', 'searchCriteria':{'searchString': "my_test_var"}, 'functionNodeFilter': "sbs::function::get_float1"},
        'function_node_filters_2': { 'name': '"my_test_var" set float1 from test_return_1', 'root': 'pf:test_return_1', 'searchCriteria':{'searchString': "my_test_var"}, 'functionNodeFilter': "sbs::function::set"},
        'function_node_filters_3': { 'name': '"my_test_var" get float1 from root', 'root': '', 'searchCriteria':{'searchString': "my_test_var"}, 'functionNodeFilter': "sbs::function::get_float1"},
        'function_node_filters_4': { 'name': 'subtraction from root', 'root': '', 'searchCriteria':{'searchString': ""}, 'functionNodeFilter': "sbs::function::sub"},
        'function_node_filters_5': { 'name': 'subtraction from test_return_1', 'root': 'pf:test_return_1', 'searchCriteria':{'searchString': ""}, 'functionNodeFilter': "sbs::function::sub"},
        'function_node_filters_6': { 'name': 'addition from root', 'root': '', 'searchCriteria':{'searchString': ""}, 'functionNodeFilter': "sbs::function::add"},
        'function_node_filters_7': { 'name': 'float from test_return_1', 'root': 'pf:test_return_1', 'searchCriteria':{'searchString': ""}, 'functionNodeFilter': "sbs::function::const_float1"},
        'function_node_filters_8': { 'name': '"another" float from root', 'root': '', 'searchCriteria':{'searchString': "another"}, 'functionNodeFilter': "sbs::function::const_float1"},

        # Graph and Function node filters
        'gf_node_filters_1': { 'name': 'float in Blend nodes', 'root': '', 'searchCriteria':{'searchString': ""}, 'graphNodeFilter': "sbs::compositing::blend", 'functionNodeFilter': "sbs::function::const_float1"},
        'gf_node_filters_2': { 'name': 'substraction in Blend nodes entering pkg func', 'root': '', 'searchCriteria':{'searchString': "", 'enterGraphPkgFct':True}, 'graphNodeFilter': "sbs::compositing::blend", 'functionNodeFilter': "sbs::function::sub"},
        'gf_node_filters_3': { 'name': '"another" float in Blend nodes', 'root': '', 'searchCriteria':{'searchString': "another"}, 'graphNodeFilter': "sbs::compositing::blend", 'functionNodeFilter': "sbs::function::const_float1"},

        # Function calls
        'func_call_1': { 'name': '"test_return_1" function call and definition', 'root': '', 'searchCriteria':{'searchString': "test_return_1"}},

        # Param functions (incl. preset)
        'paramfunc_1': { 'name': 'Preset: Param functions', 'root': '', 'searchCriteria':{'searchString': "", 'ss_param_func':True}},
        'paramfunc_2': { 'name': '"library" into param function of a library node (pkg2)', 'root': 'p:gs_unit_tests_pkg2', 'searchCriteria':{'searchString': "library"}},
        'paramfunc_3': { 'name': '"param func" into param functions', 'root': '', 'searchCriteria':{'searchString': "param func"}},

        # Presets: TODO
        'todo_1': { 'name': 'TODO preset', 'root': '', 'searchCriteria':{'searchString': "TODO", 'caseSensitive':True}},

        # Presets: TMP
        'todo_1': { 'name': 'TMP preset', 'root': '', 'searchCriteria':{'searchString': "TMP", 'caseSensitive':True}},

        # Node identifier
        'node_id_1': { 'name': '"1534176499" node id', 'root': '', 'searchCriteria':{'searchString': "1534176499"}},
        'node_id_2': { 'name': '"1534182345" node id', 'root': '', 'searchCriteria':{'searchString': "1534182345"}},
        
        # Getters / setters
        'getset_1': { 'name': 'Getters for my_test_var', 'root': '', 'searchCriteria':{'searchString': "my_test_var", 'varSetter':False, 'folderId':False, 'graphName':False, 'funcName':False, 'funcInput':False, 'comment':False}},
        'getset_2': { 'name': 'Setters for my_test_var', 'root': '', 'searchCriteria':{'searchString': "my_test_var", 'varGetter':False, 'folderId':False, 'graphName':False, 'funcName':False, 'funcInput':False, 'comment':False}},

        # Pins
        'pins_1': { 'name': '"pin"', 'root': '', 'searchCriteria':{'searchString': "pin"}},

        # Multiple packages
        'multiple_packages_1': { 'name': '"test_return_1"', 'root': '', 'searchCriteria':{'searchString': "test_return_1"}},
    }

    TEST_RESULTS_FNAME = 'gs_unit_test_results.json'

    @classmethod
    def systemCompNodeFilter(cls, definition):
        data = SDObj.SDNODE_COMPOSITING_TYPE[definition]
        return NoteTypeFilterData.fromSystem(data[1], definition, data[0])

    @classmethod
    def systemFXMapNodeFilter(cls, definition):
        data = SDObj.SDNODE_FXMAP_TYPE[definition]
        return NoteTypeFilterData.fromSystem(data[1], definition, data[0])
    
    @classmethod
    def libraryNodeFilter(cls, identifier):
        lib = gssdlibrary.g_gssdlibrary
        data = lib.nodes[identifier]
        label = data[gssdlibrary.GSSDLibrary.LABEL]
        return NoteTypeFilterData.fromLibrary(label, identifier)
    
    @classmethod
    def functionNodeFilter(cls, definition):
        data = SDObj.NODE_FUNCTION_TYPE[definition]
        return NoteTypeFilterData.fromSystem(data[1], definition, data[0])

    def __init__(self, prefs):
        self.prefs = prefs
        gstests_path = os.path.dirname(__file__) # go one folder up
        globalsearch_path = os.path.dirname(gstests_path) # go one folder up
        self.reference_test_result_path = os.path.join(gstests_path , self.TEST_RESULTS_FNAME)
        self.recorded_test_result_path = os.path.join(globalsearch_path , self.TEST_RESULTS_FNAME)
        self.testIds = list(self.TESTS.keys())
        self.record = False
        self.reset()

    def reset(self, resetReferenceTestResults = True):
        if resetReferenceTestResults:
            self.referenceTestResults = dict()
        self.recordedTestResults = dict()
        self.passedCount = 0

        # contextual for current test
        self.prepareToRunTestIndex(0)

    def loadReferenceTestResults(self):
        self.referenceTestResults = dict()
        try:
            with open(self.reference_test_result_path, 'r') as readFile:
                j = json.load(readFile)
            self.referenceTestResults.update(j)
            return True
        except:
            gslog.error("Error loading reference test results: " + self.reference_test_result_path)
            return False
        
    def saveRecordedTestResults(self):
        try:
            with open(self.recorded_test_result_path, 'w') as writeFile: 
                json.dump(self.recordedTestResults, writeFile)
            gslog.debug("Test result file written to: " + self.recorded_test_result_path)
            return True
        except:
            gslog.error("Error writing test result file: " + self.recorded_test_result_path)
            return False
        
    def prepareSearchCriteria(self, test):
        sc = self.defaultSearchCriteria()
        testSc = test.get('searchCriteria')
        if testSc:
            sc.__dict__.update(testSc)

        # node filters
        graphNodeFilterDef = test.get('graphNodeFilter')
        if graphNodeFilterDef:
            if graphNodeFilterDef.startswith("sbs::compositing::"):
                graphNodeFilter = self.systemCompNodeFilter(graphNodeFilterDef)
            elif graphNodeFilterDef.startswith("sbs::fxmap::"):
                graphNodeFilter = self.systemFXMapNodeFilter(graphNodeFilterDef)
            else:
                graphNodeFilter = self.libraryNodeFilter(graphNodeFilterDef)

            sc.graphNodeFilter = graphNodeFilter

        functionNodeFilterDef = test.get('functionNodeFilter')
        if functionNodeFilterDef:
            sc.functionNodeFilter = self.functionNodeFilter(functionNodeFilterDef)

        return sc
        
    def runTest(self, test):
        jsonResult = self.performSearch(self.searchCriteria, test['root'])
        return jsonResult
    
    def prepareTestReport(self):
        self.testReport = self.testId + " - " + self.test['name']
    
    def completeTestReport(self, passed):
        s = "PASSED" if passed else "FAILED" 
        self.testReport += " -> " + s

    # prepare test output and run the test
    def preTest(self):
        self.prepareTestReport()
        if self.record:
            gslog.debug(self.testReport)

        self.searchCriteria = self.prepareSearchCriteria(self.test)
        self.jsonResult = self.runTest(self.test)

        QTimer.singleShot(0, lambda:self.postTest())

    # process test result and launch the next test or terminate if no remaining test
    def postTest(self):
        if self.record:
            self.recordedTestResults[self.testId] = self.jsonResult
        else:
            if len(self.referenceTestResults) > 0 and self.referenceTestResults.get(self.testId):
                referenceTestResult = self.referenceTestResults[self.testId]
                if self.jsonResult == referenceTestResult:
                    self.passedCount += 1

                passed = self.jsonResult == referenceTestResult
                self.completeTestReport(passed)
                if passed:
                    gslog.debug(self.testReport)
                else:
                    gslog.error(self.testReport)
            else:
                gslog.debug(self.testReport)

        # next test
        if self.prepareToRunNextTest():
            QTimer.singleShot(0, lambda:self.preTest())
        else:
            self.endRunTest()

    def endRunTest(self, totalReport=True):
        if self.record:
            self.saveRecordedTestResults()
        elif totalReport:
            totalRun = len(self.testIds)
            totalFailed = totalRun - self.passedCount
            gslog.debug("Total test RUN:" + str(totalRun) + " - PASSED:" + str(self.passedCount) + " - FAILED:"+str(totalFailed))

    def prepareToRunNextTest(self):
        hasNextTest = False
        if self.currentTestIdIndex < len(self.testIds)-1:
            self.prepareToRunTestIndex(self.currentTestIdIndex + 1)
            hasNextTest = True
        return hasNextTest

    def prepareToRunTestId(self, testId):
        self.testId = testId
        self.test = self.TESTS[testId]
        self.searchCriteria = None
        self.searchResults = None # SearchResults instance, contains pathTree
        self.jsonResult = None  # json
        self.testReport = ''

    def prepareToRunTestIndex(self, index):
        self.currentTestIdIndex = index
        self.prepareToRunTestId(self.testIds[index])

    # record: if True, the serialized results are written into file TEST_RESULTS_FNAME as a dictionary with the following format: key: test id, value: test result tree
    # if False, TEST_RESULTS_FNAME is loaded and its content is compared to the test results being performed.
    # These recorded test results (TEST_RESULTS_FNAME file) will then serve as reference for unit tests, which will be compared to it.
    # The recorded test results are written at the root of the globalsearch module. However, the file needs to be moved into the gstests module to be read as serve as reference when running unit tests
    def runAllTests(self, record = False):
        if record:
            gslog.debug("Running all unit tests and writing results to file:")
        else:
            gslog.debug("Running all unit tests and comparing results with reference result file:")
        self.reset()
        self.record = record

        # load reference test results unless we are recording
        if not record:
            if not self.loadReferenceTestResults():
                return
            
        # we run the tests on timer so each print to console can be seen after each test instead of all at the end.
        QTimer.singleShot(0, lambda:self.preTest())

    def runTestId(self, testId):
        self.reset(resetReferenceTestResults=False)
        if len(self.referenceTestResults) == 0:
            self.loadReferenceTestResults()

        self.prepareToRunTestId(testId)
        self.prepareTestReport()
        self.searchCriteria = self.prepareSearchCriteria(self.test)
        self.jsonResult = self.runTest(self.test)
        if len(self.referenceTestResults) > 0 and self.referenceTestResults.get(self.testId):
            referenceTestResult = self.referenceTestResults[self.testId]
            passed = self.jsonResult == referenceTestResult
            self.completeTestReport(passed)
            if passed:
                gslog.debug(self.testReport)
            else:
                gslog.error(self.testReport)
        else:
            gslog.debug(self.testReport)

    def defaultSearchCriteria(self, searchString=""):
        sc = SearchCriteria(searchString)
        return sc
    
    # Finds a search root by name/type, return the matching SDObj if found
    def findSearchRoot(self, name, type):
        if type == SDObj.ROOT:
            return None
        
        packages = sd.getContext().getSDApplication().getPackageMgr().getUserPackages()
        for p in range(0, packages.getSize()):
            pkg = packages.getItem(p)

            if type == SDObj.PACKAGE:
                pkgName = SDObj.name(pkg, SDObj.PACKAGE)
                if name == pkgName:
                    return pkg
                
            resources = pkg.getChildrenResources(False)
            if resources:
                for r in range(0, resources.getSize()):
                    resource = resources.getItem(r)
                    found = self.findSearchRootResourceCheck(resource, name, type)
                    if found:
                        return found
        return None
    
    def findSearchRootResourceCheck(self, resource, name, type):
        if type == SDObj.GRAPH and isinstance(resource, SDGraph):
            graphName = SDObj.name(resource, SDObj.GRAPH)
            if name == graphName:
                return resource
        elif type == SDObj.FUNCTION and isinstance(resource, SDSBSFunctionGraph):
            funcName = SDObj.name(resource, SDObj.FUNCTION)
            if name == funcName:
                return resource
        elif isinstance(resource, SDResourceFolder):
            if type == SDObj.FOLDER:
                folderName = SDObj.name(resource, SDObj.FOLDER)
                if name == folderName:
                    return resource

            folderItems = resource.getChildren(False)
            if folderItems:
                for r in range(0, folderItems.getSize()):
                    folderItem = folderItems.getItem(r)
                    found = self.findSearchRootResourceCheck(folderItem, name, type)
                    if found:
                        return found
        return None
                                                       
    def performSearch(self, searchCriteria, searchRoot = None):
        if searchRoot is not None and len(searchRoot) == 0:
            searchRootObj = None
        else:
            comps = searchRoot.split(':')
            typeStr = comps[0]
            if typeStr == 'p':
                type = SDObj.PACKAGE
            elif typeStr == 'f':
                type = SDObj.FOLDER
            elif typeStr == 'g':
                type = SDObj.GRAPH
            elif typeStr == 'pf':
                type = SDObj.FUNCTION
            searchRootObj = self.findSearchRoot(comps[1], type)
            # t, tstr = SDObj.type(searchRootObj)
            # gslog.debug("found search root: " + str(searchRootObj) + " " + SDObj.name(searchRootObj, t))

        self.searchResults = SearchResults()
        gs = GlobalSearch(sd.getContext(), self.prefs, searchRootObj, searchCriteria, self.searchResults)
        gs.search()
        jsonResult = json.dumps(self.searchResults.pathTree, cls=SearchResultPathNodeJSONEncoder)
        return jsonResult



