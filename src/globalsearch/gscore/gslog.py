# ---------------
# Global Search - Substance 3D Designer plugin
# (c) 2019-2025 Eyosido Software SARL
# ---------------

import logging
import sd

class GSLogger:
    DEBUG = 0
    INFO = 1
    WARNING = 2 
    ERROR = 3

    @classmethod
    def classInit(cls):
        global g_gslog
        g_gslog = GSLogger()

    @classmethod
    def classDeinit(cls):
        logger = globals()["g_gslog"]
        if logger.nativeLogger:
            logger.nativeLogger.removeHandler(logger.handler)
            logger.nativeLogger = None
        globals()["g_gslog"] = None

    def __init__(self):
        self.useNativeLogger = isinstance(sd.getContext().getLogger(), logging.Logger)
        self.nativeLogger = None
        if self.useNativeLogger:
            self.nativeLogger = logging.getLogger("GlobalSearch")
            self.handler = sd.getContext().createRuntimeLogHandler()
            self.nativeLogger.addHandler(self.handler)
            self.nativeLogger.setLevel(logging.DEBUG)
            self.nativeLogger.propagate = False
            self.log(self.INFO, "Using native logger")
        else:
            self.log(self.INFO, "Not using native logger")
    
    def log(self, level, msg):
        if self.useNativeLogger:
            # SD 2020 API
            if level == self.DEBUG:
                self.nativeLogger.debug(msg)
            elif level == self.INFO:
                self.nativeLogger.info(msg)
            elif level == self.WARNING:
                self.nativeLogger.warning(msg)
            elif level == self.ERROR:
                self.nativeLogger.error(msg)
        else:
            # SD 2019 API
            from sd.logger import LogLevel
            logger = sd.getContext().getLogger()
            gs = "GlobalSearch"
            if level == self.INFO or level == self.DEBUG:
                logger.log(msg, LogLevel.Info, gs)
            elif level == self.WARNING:
                logger.log(msg, LogLevel.Warning, gs)
            elif level == self.ERROR:
                logger.log(msg, LogLevel.Error, gs)

def debug(msg):
    g_gslog.log(GSLogger.DEBUG, '[DEBUG]' + msg)

def info(msg):
    g_gslog.log(GSLogger.INFO, msg)

def warning(msg):
    g_gslog.log(GSLogger.WARNING, '[WARNING]' + msg)

def error(msg):
    g_gslog.log(GSLogger.ERROR, '[ERROR]' +msg)


