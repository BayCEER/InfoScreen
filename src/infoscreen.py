'''
Created on 09.11.2015

@author: oliver
'''
import sys
import platform
import logging
import os
import datetime
import time

from PyQt4.QtGui import QApplication
from PyQt4.Qt import  QWebView, QUrl
from PyQt4.QtCore import QThread
from PyQt4.QtWebKit import QWebSettings

from logging.handlers import RotatingFileHandler


logger = logging.getLogger("Infocscreen")

logger.setLevel(logging.INFO) 
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

if platform.system() == "Linux":
    fh = RotatingFileHandler("/var/log/infoscreen.log", maxBytes=2048, backupCount=10)
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
else:
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

def readConfig(path):
    logger.info("readConfig")             
    f = open(path,'r')    
    data = f.read()
    f.close()
    return json.loads(data)         
    

class MainView(QWebView):
    def __init__(self, page, parent=None):
        super(MainView, self).__init__(parent)
        self.settings().setAttribute(QWebSettings.PluginsEnabled, True)
        self.settings().setAttribute(QWebSettings.PrivateBrowsingEnabled, True)
        self.settings().setAttribute(QWebSettings.LocalContentCanAccessRemoteUrls, True)
        self.load(QUrl(page))
        self.loadFinished.connect(self._loadFinished)
        self.loadStarted.connect(self._loadStarted)               
        
        if platform.system() == "Linux":
            self.screenSaver = ScreenSaver()
            self.screenSaver.start()        
    
    def _loadStarted(self):      
        self.loading = True
    
    def _loadFinished(self, ok):        
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


if __name__ == '__main__':   
    app = QApplication(sys.argv)
    
    if (len(sys.argv)<2):
        if platform.system() == "Linux":
            startPage = readConfig("/etc/infoscreen/infoscreen.json")["startPage"]
        else:
            print("Usage: infoscreen <url>")
            sys.exit(-1)        
    else:
        startPage = sys.argv[1]
    
    main = MainView(startPage)            
    main.showFullScreen();    
    sys.exit(app.exec_())
    