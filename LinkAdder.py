#import os
##import sys
##nn for that
#import mechanize
import logging
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
                command = '"%s" /n /a /p "%s" /d "%s"' % (whereidm, path, link.replace(":81", ""))
                code = subprocess.call(command)
                
                self.__lock.acquire()
                logging.debug('Added %s. IDM Add call result: %d' % (link[link.rfind('/')+1::], code))
                self.__lock.release()
        except:
            self.__lock.acquire()
            logging.debug('Couldn\'t add link for some reason.')
            self.__lock.release()
        
    def start(self, itere):
        threads = []
        
        for title,info in itere:
            for link in info[1]:
                tempt = threading.Thread(target=self.addLink, args=(link,info[0],self.__idmpath))
                threads.append(tempt)
                tempt.start()
    
        for thread in threads:
                thread.join()
        
        print 'Valid links have been added'
        command = '"%s" /s' % self.__idmpath
        logging.debug('IDM Start call result: %d' % subprocess.call(command))
        print 'Queue started'
        return 0
