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
    DEFAULT_MAX_SEARCH_HISTORY_COUNT = 10

    def __init__(self, callback, maxCount = DEFAULT_MAX_SEARCH_HISTORY_COUNT):
        self.callback = callback
        self.maxCount = maxCount # max item count in history
        self.history = []

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
                gslog.log("Error loading search history.")
            finally:
                self.callback.searchHistoryUpdateEnded()

    def save(self):
        path = self.__class__.filename()
        try:
            self.callback.searchHistoryUpdateStarting()
            with open(path, "w") as writeFile: 
                json.dump(self.history, writeFile)
        except:
            gslog.log("Error saving search history.")
        finally:
                self.callback.searchHistoryUpdateEnded()

    def delete(self):
        path = self.__class__.filename()
        if os.path.exists(path):
            try:
                os.remove(path)
                self.callback.searchHistoryCleared()
            except:
                gslog.log("Error deleting search history file.")

    @classmethod
    def filename(cls):
        path = os.path.dirname(os.path.dirname(__file__)) # go one folder up
        path = os.path.join(path ,"gshistory.json")
        return path
