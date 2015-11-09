#!/usr/bin/python
import sys
import json
import urllib2
import time
import os
import platform
import datetime
import logging


from logging.handlers import RotatingFileHandler

from string import Template


from PyQt4.QtWebKit import QWebView
from PyQt4.QtWebKit import QWebSettings
from PyQt4.QtCore import Qt
from PyQt4.QtCore import SIGNAL
from PyQt4.QtCore import QThread
from PyQt4.QtGui import QApplication
from PyQt4.QtGui import QCursor
from PyQt4.QtCore import QUrl


test = False

if platform.system() == "Linux":    
    CONFIG  = "/etc/infoscreen"
    LOGPATH = "/var/log/infoscreen.log"
else:
    CONFIG  = "../win"
    LOGPATH = "./infoscreen.log"
    
logger = logging.getLogger("Infocscreen")

class WebView(QWebView):    
    
    loading = False
    loaded = True
        
        
    def __init__(self, startPage, config, parent=None):
        super(WebView, self).__init__(parent)
        
        self.settings().setAttribute(QWebSettings.PluginsEnabled, True)
        self.settings().setAttribute(QWebSettings.PrivateBrowsingEnabled, True)
        self.settings().setAttribute(QWebSettings.LocalContentCanAccessRemoteUrls, True)
        
        self.loadFinished.connect(self._loadFinished)
        self.loadStarted.connect(self._loadStarted)
        self.loadProgress.connect(self._loadProgress)
        self.load(QUrl(os.path.join(CONFIG,startPage)))                   
                   
        
        self.worker = ScreenThread(config)
        self.connect(self.worker, SIGNAL("loadScreen"), self.loadScreen)
        self.worker.start()
        
        if platform.system() == "Linux":  
            self.screenSaver = ScreenSaver()
            self.screenSaver.start()        
        
        
    def _loadProgress(self, progress):
        # logger.info("Loaded {}%".format(progress))
        pass
                    
    def loadScreen(self,item):        
#         if self.loading:
#             logger.info("Stop loading")
#             self.stop()             
#         
        if 'template' in item: 
            logger.info("Load template:{0}".format(item["template"]))
            ftemp = open( os.path.join(CONFIG,"{}Template.html".format(item['template'])))
            src = Template(ftemp.read())
            html = src.substitute(item)                       
            baseUrl = QUrl.fromLocalFile(item["basePath"] + "/");
            self.setHtml(html,baseUrl)                                    
        else:
            logger.info("Load url:{0}".format(item["url"]))        
            self.load(QUrl(item["url"]))             
                    
    def _loadStarted(self):
        # logger.info("Load started.")
        self.loading = True
    
    def _loadFinished(self, ok):
        logger.info("Load finished.")
        self.loaded = ok
        self.loading = False

class ScreenSaver(QThread):
    def __init__(self):
        QThread.__init__(self)
        os.system("xset s off")
        self._stopped = False 
        
    def __del__(self):
        self._stopped = True   
    
    def run(self):
        while not self._stopped:
            h = datetime.datetime.now().hour
            if h > 22 or h < 6:
                logger.info("Turn display off")
                os.system("xset dpms force standby")
            else:
                logger.info("Turn display on")
                os.system("xset dpms force on")
            time.sleep(60)
        
        
class ScreenThread(QThread): 
                
    def __init__(self, config):
        QThread.__init__(self)
        self._config = config
        self._stopped = False                
    def __del__(self):
        self._stopped = True                                    
    def run(self):  
        count = 0 
        time.sleep(5)     
        while not self._stopped:
            count += 1 
            if count%10 == 0:
                count = 0                
                self._config = readConfig("infoscreen.json")                             
            for item in self._config:
                self.emit(SIGNAL("loadScreen"),item)
                time.sleep(item["duration"])
                

def getConfig(url):
    get = urllib2.urlopen(url)
    data = get.read()
    get.close()
    return json.loads(data)

def readConfig(path):
    logger.info("readConfig")             
    f = open(os.path.join(CONFIG,path),'r')    
    data = f.read()
    f.close()
    return json.loads(data)          

def initLog(path):
    
    logger.setLevel(logging.INFO)
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)
    ch.setFormatter(formatter)
 
    fh = RotatingFileHandler(LOGPATH, maxBytes=2048, backupCount=10)
    fh.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)

        
def main(): 
       
    initLog(LOGPATH)
            
    app = QApplication(sys.argv)
    app.setOverrideCursor(QCursor(Qt.BlankCursor))                 
    
    web = WebView(startPage="startPage.html", config=readConfig("infoscreen.json"))
    web.showFullScreen()
    logger.info("Infoscreen started.")        
    sys.exit(app.exec_())
    logger.info("Infoscreen stopped.")

if __name__ == '__main__':
    main()
    
       
    
