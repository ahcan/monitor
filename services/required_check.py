import json
import time
import logging
import threading
from utils.file import File
from utils import Ffmpeg
from BLL.log import Log as LogBLL
from config.config import SYSTEM

class RequiredCheck(object):
    def __init__(self, ipsource):
        "ip multicast"
        self.logger = logging.getLogger(self.__class__.__name__)
        self.ip = "udp://+{0}".format(ipsource)
    def check(self):
        self.logger.debug("Check source: {0}".format(self.ip))
        ffmpeg = Ffmpeg()
        check = ffmpeg.check_source(self.ip)
        status = {0: "DOWN       ", 1: "UP         ", 2: "VIDEO ERROR", 3: "AUDIO ERROR"} [check]
        self.logger.debug("Debugsoure {0}-status: {1}".format(self.ip, status))
        return 1