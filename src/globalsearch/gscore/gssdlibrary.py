# ---------------
# Global Search - Substance 3D Designer plugin
# (c) 2019-2025 Eyosido Software SARL
# ---------------

import os, json
from globalsearch.gscore import gslog

# Accesses the default Designer Substance library nodes
class GSSDLibrary:
    DB_PATH_WIN = "Adobe/Adobe Substance 3D Designer/databases/resources.json" # inside %LOCALAPPDATA%
    DB_PATH_MAC = "~/Library/Application Support/Adobe/Adobe Substance 3D Designer/databases/resources.json"

    # indices of fields inside self.nodes values
    LABEL = 0
    SBS_PATH = 1

    @classmethod
    def classInit(cls):
        global g_gssdlibrary
        g_gssdlibrary = GSSDLibrary()

    @classmethod
    def classDeinit(cls):
        globals()["g_gssdlibrary"] = None

    def __init__(self):
        self.nodes = {} # key: node id, value: (label, sbs_path)

    def entry(self, identifier):
        return self.nodes.get(identifier)

    def load(self):
        if len(self.nodes) == 0:            
            db_path = os.path.join(os.getenv('LOCALAPPDATA'), self.DB_PATH_WIN) if os.name == 'nt' else self.DB_PATH_MAC
            db = None

            if os.path.isfile(db_path):
                try:
                    with open(db_path, "r") as file:
                        db = json.load(file)
                    gslog.info("SD DB loaded from " + db_path)               
                except Exception as e:
                    gslog.error("Loading SD DB failed: " + str(e))
            else:
                gslog.info("SD DB was not found, SD library nodes won't be available as search filter. Path=" + db_path)

            if db:
                try:
                    resources = db["resources"]
                    for r in resources:
                        if r.get("is_listable"):
                            extension = r.get("extension")
                            if extension and extension == "graph":
                                ident = r.get("basename")
                                if ident:
                                    sbs = r.get("archive_url")
                                    if sbs:
                                        metadata = r.get("metadata")
                                        if metadata:
                                            hideInLibrary = metadata.get("hideInLibrary")
                                            if not hideInLibrary or hideInLibrary == "0":
                                                label = metadata.get("label")
                                                if label:
                                                    self.nodes[ident] = (label, sbs)
                except Exception as e:
                    gslog.error("Parsing SD DB failed: " + str(e))

        return self.nodes




    
