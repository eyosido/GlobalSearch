# ---------------
# Global Search - Substance 3D Designer plugin
# (c) 2019-2022 Eyosido Software SARL
# ---------------

import os, json
from globalsearch.gscore import gslog

class GSUISearchHistory:
    """
    Search history management
    Callbacks (required!):
        searchHistoryUpdateStarting()
        searchHistoryUpdatEnded()
        searchHistoryPushed(text)
        searchHistoryRemoved(index)
        searchHistoryCleared()
    """
    DEFAULT_MAX_SEARCH_HISTORY_COUNT = 20
    DEFAULT_MAX_SEARCH_NAVIGATION_COUNT = 100

    @classmethod
    def filename(cls):
        path = os.path.dirname(os.path.dirname(__file__)) # go one folder up
        path = os.path.join(path ,"gshistory.json")
        return path

    def __init__(self, callback, maxCount = DEFAULT_MAX_SEARCH_HISTORY_COUNT):
        self.callback = callback
        self.maxCount = maxCount # max item count in history
        self.history = []   # found searches without duplicates, persistent
        self.navigation = []  # found searches in the order they are made, duplicates possible, not persistent  
        self.nav_index = 0  # current position in self.navigation to enable prev/next

    def count(self):
        return len(self.history)

    def push(self, text):
        # check whether already existing
        text_l = text.lower()
        found = False
        i = 0
        historyLen = len(self.history)
        while i < historyLen and not found:
            item = self.history[i]
            if text_l == item.lower():
                found = True
            else:
                i += 1

        self.callback.searchHistoryUpdateStarting()

        if found:
            # move found item to top, also replacing the text by the new one in case the case changed
            del self.history[i]
            self.callback.searchHistoryRemoved(i)
            self.history.insert(0, text)
            self.callback.searchHistoryPushed(text)
        else:
            self.history.insert(0, text)
            self.callback.searchHistoryPushed(text)
            if len(self.history) > self.maxCount:
                self.history.pop()
                self.callback.searchHistoryRemoved(len(self.history))

        self.callback.searchHistoryUpdateEnded()
        self.save()

    def clear(self):
        self.history = []
        self.save()
        self.callback.searchHistoryUpdateStarting()
        self.callback.searchHistoryCleared()
        self.callback.searchHistoryUpdateEnded()

    def load(self):
        path = self.__class__.filename()
        if os.path.exists(path):
            try:
                self.callback.searchHistoryUpdateStarting()
                with open(path, "r") as readFile: 
                    self.history = json.load(readFile)
            except:
                gslog.error("Error loading search history.")
            finally:
                self.callback.searchHistoryUpdateEnded()

    def save(self):
        path = self.__class__.filename()
        try:
            self.callback.searchHistoryUpdateStarting()
            with open(path, "w") as writeFile: 
                json.dump(self.history, writeFile)
        except:
            gslog.error("Error saving search history.")
        finally:
                self.callback.searchHistoryUpdateEnded()

    def delete(self):
        path = self.__class__.filename()
        if os.path.exists(path):
            try:
                os.remove(path)
                self.callback.searchHistoryCleared()
            except:
                gslog.error("Error deleting search history file.")

    def nav_append(self, text):
        gslog.debug("nav_append "+ text)
        self.navigation.append(text)
        if len(self.navigation) > self.DEFAULT_MAX_SEARCH_NAVIGATION_COUNT:
            self.navigation.pop(0)  # remove first item

        self.nav_index = len(self.navigation) - 1
        self.logNav()

    def nav_has_next(self):
        b = self.nav_index < len(self.navigation)-1
        return b

    def nav_has_prev(self):
        b = self.nav_index > 0
        return b

    def nav_next(self):
        text = None
        if self.nav_has_next():
            self.nav_index += 1
            text = self.navigation[self.nav_index]
        gslog.debug("nav_next ->"+ text)
        self.logNav()
        return text

    def nav_prev(self):
        text = None
        if self.nav_has_prev():
            self.nav_index -= 1
            text = self.navigation[self.nav_index]
        gslog.debug("nav_prev ->"+ text)
        self.logNav()
        return text
    
    def logNav(self):
        s = ""
        i=0
        for n in self.navigation:
            if len(s)>0:
                s+=', '
            s += str(i) + ': ' + n
            i += 1
        gslog.debug('Nav list:' + s)
        gslog.debug('Nav index: ' + str(self.nav_index))


