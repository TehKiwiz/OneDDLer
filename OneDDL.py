from sys import *
from LinkAdder import *
from xml.dom.minidom import parse, parseString

import os
import re
import httplib2
import ConfigParser
import _winreg

def shouldDownload(title):
    #NotImplementedYet
    return true

def findIDM():
    try:
        key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Internet Download Manager\\")
        path = _winreg.QueryValueEx(key, "DisplayIcon")[0]
        key.Close()
        return path
    except WindowsError:
        return None

config = ConfigParser.SafeConfigParser()
config.read('OneDDL.ini')
if not config.has_section('General'):
    config.add_section('General')

#Find IDM and add to config
try:
    value = config.get('General', 'IDMPath')
except ConfigParser.NoOptionError:
    value = ''
if value.strip()s == '' or not os.path.isfile(value):
    print 'lol'
    pathi = findIDM()
    if pathi is None:
        print 'Couldn\' find IDM'
        exit(-1)
    config.set('General', 'IDMPath', pathi)

#Get default download path, root folder for downloads
try:
    value = config.get('General', 'DefDownloadPath')
except ConfigParser.NoOptionError:
    value = ''
if value.strip() == '':
    print 'hai'
    print 'Please enter the default download path (eg: D:/Lol/Crap/)'
    pathd = raw_input('--> ')
    config.set('General', 'DefDownloadPath', pathd) 

#Parse TV Shows
#NotJustYet
    
with open('OneDDL.ini', 'wb') as fp:
    config.write(fp)

#exit(0)

h = httplib2.Http(".cache")
resp, content = h.request("http://www.oneddl.com/feed/rss/", "GET")
newcontent = parseString(content)
reggi = re.compile("Multiupload\s*(?P<urls>(<a href=\".*?\".*?>.*?</a>\s*)+)", re.IGNORECASE)
dict_r = {}

print 'Fetching links from OneDDL.com'
for release in newcontent.getElementsByTagName("item"):
        for node in release.childNodes:
            if node.nodeName == "title":
                title = node.firstChild.wholeText
            if node.nodeName == "description":
                links = []
                linksContent = node.firstChild.wholeText
                match = reggi.search(linksContent) 
                if match == None:
                    break
                matches = re.finditer("href=\"(.*?)\"", match.group("urls"))
                for match in matches:
                    links.append(match.group(1))
                dict_r[title] = links

print '%s downloads found.' % len(dict_r)
multipattern = "<div id=\"downloadbutton_\" style=\"\"><a href=\"(.*?)\" onclick=\"launchpopunder\(\)\;\">"
LinkAdder(pathi, multipattern).start(dict_r.itervalues())

