#!/usr/bin/python
import sys
import json
import urllib2
import time
import os
import platform
import datetime

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
else:
    CONFIG  = "../win"     

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
        
        self.screenSaver = ScreenSaver()
        self.screenSaver.start()
        
    def _loadProgress(self, progress):
        # print("Loaded {}%".format(progress))
        pass
                    
    def loadScreen(self,item):        
        if self.loading:
            print("Stop loading")
            self.stop()             
        
        if 'template' in item: 
            print("Load template:{0}".format(item["template"]))
            ftemp = open( os.path.join(CONFIG,"{}Template.html".format(item['template'])))
            src = Template(ftemp.read())
            html = src.substitute(item)                       
            baseUrl = QUrl.fromLocalFile(item["basePath"] + "/");
            self.setHtml(html,baseUrl)                                    
        else:
            print("Load url:{0}".format(item["url"]))        
            self.load(QUrl(item["url"]))             
                    
    def _loadStarted(self):
        # print("Load started.")
        self.loading = True
    
    def _loadFinished(self, ok):
        print("Load finished.")
        self.loaded = ok
        self.loading = False

class ScreenSaver(QThread):
    def __init__(self):
        QThread.__init__(self)
    def run(self):
        h = datetime.datetime.now().hour
        if h > 22 or h < 6:
            print("Turn display off")
            os.system("xset dpms force standby")
        else:
            print("Turn display on")
            os.system("xset dpms force on")
        time.sleep(600)
        
        
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
    print("readConfig")             
    f = open(os.path.join(CONFIG,path),'r')    
    data = f.read()
    f.close()
    return json.loads(data)                    
        
def main(): 
    app = QApplication(sys.argv)
    app.setOverrideCursor(QCursor(Qt.BlankCursor))                 
    
    web = WebView(startPage="startPage.html", config=readConfig("infoscreen.json"))
    web.showFullScreen()        
    sys.exit(app.exec_())
    

if __name__ == '__main__':
    main()
    
       
    
