#import os
##import sys
##nn for that
#import mechanize
import logging
import re
import threading
import requests
import subprocess

class NoMatchError(Exception):
    pass

class LinkAdder:
    def __init__(self, path, pattern):
        self.__idmpath = path
        self.__pattern = pattern
        
    def addLink(self, tehlink, path, whereidm):
        try:
            #resp, content = self.__httpinstance.request(tehlink, "GET")
            content = requests.get(tehlink).content
            match  = re.search(self.__pattern,content)
            if match is None:
                raise NoMatchError
            else:
                link = match.group(1)
                command = '"%s" /n /a /p "%s" /d "%s"' % (whereidm, path, link.replace(":81", ""))
                code = subprocess.call(command)
                logging.debug('Added %s. IDM Add call result: %d' % (link[link.rfind('/')+1::], code))
        except NoMatchError:
            logging.debug('Couldn\'t add link \'%s\' because there was no match.' % tehlink)
        except requests.RequestException:
            logging.debug('Couldn\'t add link \'%s\' because requests module had a problem.' % tehlink)
        
    def start(self, itere):
        threads = []
        for title,info in itere:
            for link in info[1]:
                tempt = threading.Thread(target=self.addLink, args=(link,info[0],self.__idmpath))
                threads.append(tempt)
                tempt.start()

        for thread in threads:
                thread.join()

        logging.debug('Added %d out of %d links.' % (len([x for x in threads if not x.isAlive()]),len(threads)))
        command = '"%s" /s' % self.__idmpath
        logging.debug('IDM Start call result: %d' % subprocess.call(command))
        print 'Queue started'
        return 0
