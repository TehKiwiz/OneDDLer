#import httplib2
#import urllib
import httplib2
from LinkAdder import *
import re
import ConfigParser
import _winreg
from xml.dom.minidom import parse, parseString

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

pathi = findIDM()
if pathi is None:
    print 'Couldn\' find IDM'
    system.exit(-1)
    
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

