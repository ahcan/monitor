import time
import logging
import threading
import subprocess
import json
from subprocess import call
###-image compare#########
from PIL import Image #pip install Pillow
import math, operator
##########################
import os, sys, shlex, re, fnmatch, signal
from utils import Ffmpeg
from utils import DateTime
from BLL.profile import Profile as ProfileBLL
from BLL.log import Log as LogBLL
from config.config import SYSTEM
from config import STIME, ETIME, CHANNEL
from datetime import datetime
from snmp_agent import AgentSnmp as LocalSnmp

class VideoCheck(object):
    """docstring for VideoCheck"""
    def __init__(self, id = None, name = None, type = None, protocol = None, source = None, last_status = None, last_video_status = None, agent = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.image_path = '/ramdisk/capture/image.'+str(id)+'.png'
        self.id = id
        self.name = name
        self.type = type
        self.protocol = protocol
        self.source = source
        self.last_status = last_status
        self.last_video_status = last_video_status
        self.agent = agent
        self.ip =SYSTEM["HOST"]

    def get_histogram_previous_image(self):
        #self.logger.debug("Source {0}-path previous image: {1}".format(self.source,self.image_path))
        if os.path.isfile(self.image_path):
            previous_image = Image.open(self.image_path)
        else:
            previous_image = Image.open('/monitor/error.png')
            self.logger.debug("previous image {0}: Error".format(self.source))
        histogram_previous = previous_image.histogram()
        return histogram_previous

    def get_histogram_curent_image(self):
        if os.path.isfile(self.image_path):
            os.remove(self.image_path)
        ffmpeg = Ffmpeg()
        return_code = ffmpeg.capture_image(self.protocol+"://"+self.source, self.image_path)
        # self.logger.debug("Process capture: {0}".format(return_code))
        if os.path.isfile(self.image_path):
            curent_image = Image.open(self.image_path)
        else:
            curent_image = Image.open('/monitor/error.png')
            self.logger.debug("curent image {0}: Error".format(self.source))
        histogram_curent = curent_image.histogram()
        # self.logger.debug("curent image {0}: {1}".format(self.source, histogram_curent))
        return histogram_curent

    def compare_two_images(self, histogram_previous, histogram_curent):
        rms = 0
        try:
                rms = int(math.sqrt(reduce(operator.add,map(lambda a,b: (a-b)**2, histogram_previous, histogram_curent))/len(histogram_previous)))
        except Exception as ex:
            self.logger.debug("Compare images: {0}".format(ex))
            return rms

    def get_human_readable_status(self, status):
        alarm_status = {0: "DOWN       ", 1: "VIDEO OK   ", 2: "VIDEO ERROR", 3: "AUDIO ERROR"} [status]
        return alarm_status

    def update_data(self, video_status, source_status):
        date_time = DateTime()
        opdate = date_time.get_now()
        child_thread_list = []
        profile = ProfileBLL()
        profile_data = {"video": video_status, "agent": self.agent, "ip": self.ip}
        self.logger.debug("update profile data: video{0} - agent{1} - ip{2}".format(video_status,self.agent, self.ip))
        child_thread = threading.Thread(target=profile.put, args=(self.id, profile_data,))
        child_thread.start()
        child_thread_list.append(child_thread)
        human_readable_status = self.get_human_readable_status(source_status)
        message = """%s %s (ip:%s) %s in host: %s (%s)"""%(self.name, self.type, self.source, human_readable_status, self.ip, self.agent)
        log_data = {
                    "host": self.protocol + "://" + self.source,
                    "tag": "status",
                    "msg": message
        }
        rslog = {
                 "sev"        : "Critical",
                 "jname"      : self.name,
                 "type"       : self.type,
                 "res"        : self.source,
                 "desc"       : human_readable_status,
                 "cat"        : "Communication",
                 "host"       : self.agent,
                 "opdate"     : opdate,
                 "cldate"     : opdate
        }
        self.logger.critical(json.dumps(rslog))
        log = LogBLL()
        child_thread = threading.Thread(target=log.post, args=(log_data,))
        child_thread.start()
        child_thread_list.append(child_thread)
        """Update local snmp IPTV"""
        local_snmp = LocalSnmp(profile = self.source + "-" + self.type, name = self.name, status = 2)
        child_thread = threading.Thread(target=local_snmp.set)
        child_thread.start()
        child_thread_list.append(child_thread)
        """
        Wait for update database complete
        """
        for child_thread in child_thread_list:
            child_thread.join()
        return 0

    def check_video(self):
        histogram_previous = self.get_histogram_previous_image()
        histogram_curent = self.get_histogram_curent_image()
        rms = self.compare_two_images(histogram_previous, histogram_curent)
        #self.logger.debug("First check RMS soure(%s) :%d"%(self.source,rms))
        ctime = datetime.now().strftime("%H:%M:%S").split(":")
        chour, cminute,csecond = ctime
        shour, sminute, ssecond = STIME
        ehour, eminute, esecond = ETIME
        chour, cminute, csecond, shour, sminute,ssecond, ehour, eminute, esecond = int(chour),int(cminute),int(csecond),int(shour),int(sminute),int(ssecond),int(ehour),int(eminute),int(esecond)
        self.logger.debug("First check RMS soure(%s) :%d"%(self.source.split(":")[0],rms))
        if rms < 150:
            if (self.source.split(":")[0] in CHANNEL) and chour <= ehour and chour >= shour:
                # check soure in time no check video
                self.logger.debug("Soures don't check %s %s %s: %d"%(self.source, self.name, self.type, rms))
                video_status = 1
                source_status = 1
                self.update_data(video_status, source_status)
                return 0
            if int(self.last_video_status) == 1:
                time.sleep(SYSTEM["BREAK_TIME"] * 3)
                histogram_recheck = self.get_histogram_curent_image()
                rms = self.compare_two_images(histogram_curent, histogram_recheck)
                self.logger.info("Recheck RMS %s %s %s: %d"%(self.source, self.name, self.type, rms))
                if rms < 150:
                    video_status = 0
                    source_status = 2
                    self.update_data(video_status, source_status)
        else:
            if int(self.last_video_status) == 0:
                time.sleep(SYSTEM["BREAK_TIME"] * 3)
                histogram_recheck = self.get_histogram_curent_image()
                rms = self.compare_two_images(histogram_curent, histogram_recheck)
                self.logger.info("Recheck RMS %s %s %s: %d"%(self.source, self.name, self.type, rms))
                if rms >= 200:
                    video_status = 1
                    source_status = 1
                    self.update_data(video_status, source_status)
        return 0


    def check(self):
        if not SYSTEM["monitor"]["BLACK_SCREEN"]:
            message = "Black screen monitor is disable, check your config!"
            self.logger.warning(message)
            print message
            time.sleep(60)
            exit(0)
        try:
            ctime = datetime.now().strftime("%H:%M:%S")
            profileBLL = ProfileBLL()
            data = profileBLL.get_video_check_list()
            if data["status"] == 200:
                profile_list = data["data"]
            else:
                print "Error code: " + str(data["status"])
                print data["message"]
                self.logger.error("Error code: " + str(data["status"]) + " " + data["message"])
                exit(1)
            ancestor_thread_list = []
            for profile in profile_list:
                #while threading.activeCount() > profile['thread']:
                #self.logger.debug("thread is active:{0}".format(threading.activeCount()))
                #while threading.activeCount() > 3:
                #    time.sleep(1)
                check_video = VideoCheck(
                                        id          = profile["id"],
                                        name        = profile["name"],
                                        type        = profile["type"],
                                        protocol    = profile["protocol"],
                                        source      = profile["ip"],
                                        last_status = profile["status"],
                                        last_video_status = profile["video_status"],
                                        agent       = profile["agent"]
                )
                t = threading.Thread(target=check_video.check_video)
                t.start()
                time.sleep(0.2)
                ancestor_thread_list.append(t)
                self.logger.debug("thread is active:{0}".format(threading.activeCount()))
                while threading.activeCount() > profile['thread']:
                    time.sleep(1)
            """
                ancestor_thread_list.append(t)
            Wait for all threads finish
            for ancestor_thread in ancestor_thread_list:
                ancestor_thread.join()
                while threading.activeCount() > 3:
                    time.sleep(1)
            """
            #for ancestor_thread in ancestor_thread_list:
        #    #ancestor_thread.setDaemon(True)
            #    ancestor_thread.start()
            #    self.logger.debug("thread is active:{0}".format(threading.activeCount()))
            #    while threading.activeCount() > profile['thread']:
            #        time.sleep(1)
            for ancestor_thread in ancestor_thread_list:
                ancestor_thread.join()
            # time.sleep(60)
            self.logger.info("Start: {0} End Video check:{1}".format(ctime, datetime.now().strftime("%H:%M:%S")))
        except Exception as e:
            self.logger.error(e)
            #print "Exception: " + str(e)
            time.sleep(2)
