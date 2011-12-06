#import os
##import sys
##nn for that
#import mechanize

import re
import threading
import urllib2
import subprocess

class LinkAdder:
    def __init__(self, path, pattern):
        self.__idmpath = path
        self.__pattern = pattern
        self.__lock = threading.Lock()
        
    def addLink(self, tehlink, path, whereidm):
        try:
            content = urllib2.urlopen(tehlink).read()
            match  = re.search(self.__pattern,content)
            if match is None:
                raise
            else:
                link = match.group(1)
                self.__lock.acquire()
                print 'Added', link[link.rfind('/')+1::]
                self.__lock.release()
                command = '"%s" /n /a /p "%s" /d "%s"' % (whereidm, path, link.replace(":81", ""))
                subprocess.call(command)
        except:
            pass
        
    def start(self, itere):
        for links,path in itere:
            for link in links:
                threading.Thread(target=self.addLink, args=(link,path,self.__idmpath)).start()
 
        for thread in threading.enumerate():
            if thread is not threading.currentThread():
                thread.join()

        print 'All links have been added'
        command = '"%s" /s' % self.__path
        subprocess.call(command)
        print 'Queue started'
        return 0
