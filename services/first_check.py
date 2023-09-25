import sys
import time
import logging
import threading
from utils.file import File
from utils.ffmpeg import Ffmpeg
from BLL.profile import Profile as ProfileBLL
from config.config import SYSTEM
from rabbit import Rabbit
import json

class FirstCheck(object):
    """docstring for FirstCheck"""
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def check_source(self, source, last_status, id, agent, thread, name, type):
        """
        Get status of profile, if stastus not change then update check equal 1.
        Ffmpeg: Use Ffprobe to check stastus profile (source) and return flag
        0 is down
        1 is up
        2 is video error
        3 is audio eror
        """
        ffmpeg = Ffmpeg()
        check = ffmpeg.check_source(source)
        #self.check_audio(source, agent, name, type, vmin=-23)
        self.logger.debug("Source: {0} Curent :{1} <> Last: {2}".format(source, check, last_status))
        if check != last_status:
            json_data = """{"source":"%s","status":%s,"pa_id":%s,"agent": "%s","thread":%s,"name":"%s","type":"%s"}"""%(source, last_status, id, agent, thread, name, type)
            file = File()
            replicate = file.append_to_check_list(json_data)
            if not replicate:
                self.logger.info("Doubt curent %s <> Last %s : %s"%(check, last_status, str(json_data)))

    def check_audio(self, source, agent, name, type, vmin):
        """
        Get value audio
        vmin: audio volume for alarm
        """
        ffmpeg = Ffmpeg()
        self.audio_logger = logging.getLogger("AudioCheck")
        vmean, vmax= ffmpeg.dectect_audio_volume(source=source, duration=3)
        if vmean <= vmin or vmax == 0:
            self.logger.debug ("'name': {0}, 'volume': {1}-{2}".format(name, vmean, vmax))
        json_data = {'source':source, 'vmean':vmean, 'vmax':vmax, 'agent':agent, 'name':name, 'type':type}
        self.audio_logger.info("{0}".format(json.dumps(json_data)))


    def check(self):
        if not SYSTEM["monitor"]["SOURCE"]:
            message = "Black screen monitor is disable, check your config!"
            self.logger.warning(message)
            #print message
            time.sleep(60)
            exit(0)
        try:
            ctime = datetime.now().strftime("%H:%M:%S")
            profileBLL = ProfileBLL()
            data = profileBLL.get()
            if data["status"] == 200:
                profile_list = data["data"]
            else:
                self.logger.error(str(data["status"]) + " " + data["message"])
                #print "Error code: " + str(data["status"])
                #print data["message"]
                exit(1)
            ancestor_thread_list = []
            for profile in profile_list:
                while threading.activeCount() > profile['thread']:
                    time.sleep(1)
                t = threading.Thread(target=self.check_source, args=(profile['protocol']+'://'+profile['ip'], profile['status'],
                        profile['id'],
                        profile['agent'],
                        profile['thread'],
                        profile['name'],
                        profile['type'],
                    )
                )
                t.start()
                time.sleep(0.2)
                ancestor_thread_list.append(t)
                #self.logger.debug("thread is active:{0}".format(threading.activeCount()))
                while threading.activeCount() > profile['thread']:
                    time.sleep(1)
            # Wait for all threads finish
            for ancestor_thread in ancestor_thread_list:
                 ancestor_thread.join()
            self.logger.info("Start: {0} End First check: {1}".format(ctime, datetime.now().strftime("%H:%M:%S")))
        except Exception as e:
            self.logger.error(str(e))
            # print(e)
        finally:
            time.sleep(20)
