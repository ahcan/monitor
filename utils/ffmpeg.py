import time
from subprocess import call
import os, sys, subprocess, shlex, re, fnmatch,signal
from config import STIME, ETIME, CHANNEL
from datetime import datetime
import logging

class Ffmpeg:
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
            self.logger.debug("Souce check {0} video {1} audio {2}".format(source, video, audio))
            return 1
        if value == 1 and audio == 1 and video == 1:
            return 1
        if value == 1 and audio == 1 and video == 0:
            return 2
        if value == 1 and audio == 0 and video == 1:
            return 3
        return 0

    def capture_image(self, source, file_patch):
        from config.config import SYSTEM
        cmnd = [SYSTEM["libery"]["FFMPEG"],'-timeout','30','-i', source, '-v', 'quiet','-r','1','-f','image2',file_patch,'-y']
        p = subprocess.Popen(cmnd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        timeout = 15
        i = 0
        while p.poll() is None:
            time.sleep(1)
            i+=1
            if i > timeout:
                os.kill(p.pid, signal.SIGKILL)


