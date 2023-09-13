import time
import os, sys, subprocess, shlex, re, fnmatch,signal
from config import STIME, ETIME, CHANNEL
from datetime import datetime
import logging
from requests.exceptions import ConnectionError
from threading import Timer
import cv2
#import numpy as np  # Import NumPy

class Ffmpeg:
    def __init__(self):
        self.logger = logging.getLogger("Ffmpeg")

    def check_source(self, source):
        self.logger = logging.getLogger("Ffmpeg")
        from config.config import SYSTEM
        cmnd = [SYSTEM["libery"]["FFPROBE"], source, '-v', 'quiet' , '-show_format', '-show_streams']
        p = subprocess.Popen(cmnd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        timeout = 15
        i = 0
        while p.poll() is None:
            time.sleep(1)
            i+=1
            if i > timeout:
                os.kill(p.pid, signal.SIGKILL)
        p.wait()
        out, err = p.communicate()
        value=0
        audio=0
        video=0
        for line in out.split('\n'):
            line = line.strip()
            if (line.startswith('filename=')):
                value=1
            if (line.startswith('codec_type=audio')):
                audio=1
            if (line.startswith('codec_type=video')):
                video=1
        ctime = datetime.now().strftime("%H:%M:%S").split(":")
        chour, cminute,csecond = ctime
        shour, sminute, ssecond = STIME
        ehour, eminute, esecond = ETIME
        chour, cminute, csecond, shour, sminute, ssecond, ehour, eminute, esecond = int(chour),int(cminute),int(csecond),int(shour),int(sminute),int(ssecond),int(ehour),int(eminute),int(esecond)
        if value == 1 and (source.split(":")[1].split('/')[2] in CHANNEL) and chour <= ehour and chour >= shour:
            #if cminute <= eminute and cminute >= sminute:
            #self.logger.debug("Souce check {0} video {1} audio {2}".format(source, video, audio))
            return 1
        if value == 1 and audio == 1 and video == 1:
            return 1
        if value == 1 and audio == 1 and video == 0:
            return 2
        if value == 1 and audio == 0 and video == 1:
            return 3
        return 0

    def capture_image(self, source, file_patch):
    # Set the FFmpeg log level to quiet (hide FFmpeg log)
    cv2.setUseOptimized(True)  # Optional: Enable optimizations for video capturing
    cv2.CAP_PROP_FFMPEG_LOG_LEVEL = 0
    #cap = cv2.VideoCapture('{0}?overrun_nonfatal=1&fifo_size=1500000 -hide_banner -loglevel panic'.format(source), cv2.CAP_FFMPEG)
    cap = cv2.VideoCapture(source, cv2.CAP_FFMPEG)
        #time.sleep(3)
    if cap is None or not cap.isOpened():
        self.logger.error('OpenCV cap {0} is: {1}'.format(source, ConnectionError))
        # raise ConnectionError
            sys.exit(1)
        # Suppress FFmpeg log output by redirecting stderr to /dev/null or NUL
        if sys.platform.startswith('win'):
            stderr_redirect = 'NUL'
        else:
            stderr_redirect = os.devnull
    cap.setExceptionMode(True) # quan trong, khi mat luong se throw exception, neu ko set thi ko throw
    frame = None
    while frame == None:
        ret, frame = cap.read()
        if ret:
               cv2.imwrite(file_patch, frame)
               cap.release()
               break

    def dectect_audio_volume(self, source, duration):
        '''source: udp://ip:port
        duration: time decode (seconds)
        return: max_volume, mean_volume (-db) '''
        from config.config import SYSTEM
        cmnd = [SYSTEM["libery"]["FFMPEG"], '-i', source, '-t', '{0}'.format(duration), '-af', 'volumedetect', '-f', 'null', '/dev/null']
        p = subprocess.Popen(cmnd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, bufsize=8192)
        timer = Timer(duration+10, p.kill)
        try:
            timer.start()
            out, err = p.communicate()
        finally:
            timer.cancel()
        #timeout = 15
        #i = 0
        #while p.poll() is None:
        #    # wait for get multicast source
        #    time.sleep(1)
        #    i+=1
        #    if i > timeout:
        #        os.kill(p.pid, signal.SIGKILL)

        #out, err = p.communicate()
        #print("Error code:{0}-{1}".format(errorcode,err))
        mean = 0
        max = 0
        for line in err.splitlines():
            self.logger = logging.getLogger("Ffmpeg")
            self.logger.debug("FFmpeg audio: {0}".format(line))
            if('mean_volume' in line):
                mean = float(line[line.rfind(':')+2:-3])
            elif ('max_volume' in line):
                max = float(line[line.rfind(':')+2:-3])
        return mean, max
