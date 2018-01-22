#!/usr/bin/python
import time
import threading
import subprocess
from subprocess import call
###-image compare#########
from PIL import Image #pip install Pillow
import math, operator
##########################
import os, sys, shlex, re, fnmatch, signal
from utils.ffmpeg import Ffmpeg
from BLL.profile import Profile as ProfileBLL
from BLL.log import Log as LogBLL
from config.config import IP as ip

class CheckVideo:
    def __init__(self, id, name, type, protocol, source, last_status, last_video_status, agent):
        self.image_path = '/tmp/capture/image.'+str(id)+'.png'
        self.id = id
        self.name = name
        self.type = type
        self.protocol = protocol
        self.source = source
        self.last_status = last_status
        self.last_video_status = last_video_status
        self.agent = agent
        self.ip = ip

    def get_histogram_previous_image(self):
        if os.path.isfile(self.image_path):
            previous_image = Image.open(self.image_path)
        else:
            previous_image = Image.open('/tmp/capture/error.png')
        histogram_previous = previous_image.histogram()
        return histogram_previous

    def get_histogram_curent_image(self):
        if os.path.isfile(self.image_path):
            os.remove(self.image_path)
        ffmpeg = Ffmpeg()
        ffmpeg.capture_image(self.protocol+"://"+self.source, self.image_path)
        if os.path.isfile(self.image_path):
            curent_image = Image.open(self.image_path)
        else:
            curent_image = Image.open('/tmp/capture/error.png')
        histogram_curent = curent_image.histogram()
        return histogram_curent

    def compare_two_images(self, histogram_previous, histogram_curent):
        rms = int(math.sqrt(reduce(operator.add,map(lambda a,b: (a-b)**2, histogram_previous, histogram_curent))/len(histogram_previous)))
        return rms

    def get_human_readable_status(self, status):
        alarm_status = {0: "DOWN       ", 1: "UP         ", 2: "VIDEO ERROR", 3: "AUDIO ERROR"} [status]
        return alarm_status

    def update_data(self, video_status, source_status):
        child_thread_list = []
        profile = ProfileBLL()
        profile_data = {"video": video_status, "agent": self.agent, "ip": self.ip}
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
        log = LogBLL()
        child_thread = threading.Thread(target=log.post, args=(log_data,))
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
        if rms < 150:
            if int(self.last_video_status) == 1:
                time.sleep(1)
                histogram_recheck = self.get_histogram_curent_image()
                rms = self.compare_two_images(histogram_curent, histogram_recheck)
                if rms < 150:
                    video_status = 0
                    source_status = 2
                    self.update_data(video_status, source_status)
        else:
            if int(self.last_video_status) == 0:
                time.sleep(1)
                histogram_recheck = self.get_histogram_curent_image()
                rms = self.compare_two_images(histogram_curent, histogram_recheck)
                if rms >= 200:
                    video_status = 1
                    source_status = 1
                    self.update_data(video_status, source_status)
        return 0


if __name__ == '__main__':
    try:
        profileBLL = ProfileBLL()
        data = profileBLL.get_video_check_list()
        if data["status"] == 200:
            profile_list = data["data"]
        else:
            print "Error code: " + str(data["status"])
            print data["message"]
            exit(1)
        # ancestor_thread_list = []
        for profile in profile_list:
            while threading.activeCount() > profile['thread']:
                time.sleep(1)
            check_video = CheckVideo(
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
        """
            ancestor_thread_list.append(t)
        Wait for all threads finish
        for ancestor_thread in ancestor_thread_list:
            ancestor_thread.join()
        """
        time.sleep(60)
    except Exception as e:
        print "Exception: " + str(e)
        time.sleep(10)
