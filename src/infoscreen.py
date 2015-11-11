#!/usr/bin/python

import sys
import platform
import logging
import os
import datetime
import time
import json

from PyQt4.QtWebKit import QWebView
from PyQt4.QtGui import QApplication
from PyQt4.QtCore import QUrl
from PyQt4.QtCore import QThread
from PyQt4.QtWebKit import QWebSettings
from PyQt4.QtGui import QCursor
from PyQt4.QtCore import Qt
from PyQt4.QtCore import SIGNAL

from logging.handlers import RotatingFileHandler


logger = logging.getLogger("Infocscreen")

logger.setLevel(logging.INFO) 
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

if platform.system() == "Linux":
    fh = RotatingFileHandler("/var/log/infoscreen.log", maxBytes=4096, backupCount=10)
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
    def __init__(self, page, secs, parent=None):
        super(MainView, self).__init__(parent)
        self.settings().setAttribute(QWebSettings.PluginsEnabled, True)
        # self.settings().setAttribute(QWebSettings.PrivateBrowsingEnabled, True)
        # self.settings().setAttribute(QWebSettings.LocalContentCanAccessRemoteUrls, True)
        # self.settings().setAttribute(QWebSettings.DeveloperExtrasEnabled, True)        
        self.loadFinished.connect(self._loadFinished)
        self.loadStarted.connect(self._loadStarted)
        self.load(QUrl(page))               
        
        if platform.system() == "Linux":
            self.screenSaver = ScreenSaver()
            self.screenSaver.start()
        
        self.worker = ReloadThread(secs)
        self.connect(self.worker, SIGNAL("reload"), self.reloadPage)
        self.worker.start()        
    
    def _loadStarted(self):      
        self.loading = True
    
    def _loadFinished(self, ok):        
        self.loaded = ok
        if self.loaded!=True:
            logger.warning("Failed to load page.")            
        self.loading = False
        
    def reloadPage(self):
        logger.info("Reload page")
        self.reload()
    
    

class ReloadThread(QThread):                 
    def __init__(self, secs):
        QThread.__init__(self)
        self._secs = secs
        self._stopped = False                
    def __del__(self):
        self._stopped = True                                    
    def run(self):
        while not self._stopped:
            time.sleep(self._secs)
            self.emit(SIGNAL("reload"))
               

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

def printUsage():
    print("Usage: infoscreen <url> <reloadIonterval>")
    sys.exit(-1)

if __name__ == '__main__':
    logger.info("Application started.")
    app = QApplication(sys.argv)
    
    if platform.system() == "Linux":
        app.setOverrideCursor(QCursor(Qt.BlankCursor)) 
    
    
    if (len(sys.argv)<3):
        if platform.system() == "Linux":
            config = readConfig("/etc/infoscreen/infoscreen.json")                            
            startPage = config["startPage"]
            reloadInterval = config["reloadInterval"]
        else:
            print("Usage: infoscreen <url> <reloadIonterval>")
            sys.exit(-1)        
    else:        
        startPage = sys.argv[1]
        reloadInterval = sys.argv[2]

    logger.info("Loading start page:{}".format(startPage))
    main = MainView(startPage,float(reloadInterval))  
    
    if platform.system() == "Linux":          
        main.showFullScreen();
    else:
        main.showMaximized()    
    
    sys.exit(app.exec_())
    
