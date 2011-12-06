from sys import *
from LinkAdder import *
from xml.dom.minidom import parse, parseString

import os
import re
import httplib2
import ConfigParser
import _winreg

def initialize(config):
    config.read('OneDDL.ini')
    if not config.has_section('General'):
        config.add_section('General')

    #Find IDM and add to config
    try:
        value = config.get('General', 'IDMPath')
    except ConfigParser.NoOptionError:
        value = ''
    if value.strip() == '' or not os.path.isfile(value):
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
        print 'Please enter the default download path (eg: D:/Lol/Crap/)'
        pathd = raw_input('--> ')
        config.set('General', 'DefDownloadPath', pathd)

def parseShows(xConfig):
    showDic = {}
    shows = [x for x in xConfig.sections() if x != 'General']
    for show in shows:
        try:
            season = xConfig.getint(show, 'Season')
            episode = xConfig.getint(show, 'Episode')
            quality = xConfig.get(show, 'Quality')
        except ConfigParser.NoOptionError:
            print 'Invalid Show: ', shows
            continue

        try:
            pathtd = xConfig.get(show, 'PathToDownload')
        except ConfigParser.NoOptionError:
            pathtd = '/'.join([xConfig.get('General', 'DefDownloadPath'), show, str(season), str(episode), ''])
        showDic[show] = {'Season' : season, 'Episode': episode, 'Quality' : quality, 'Path' : pathtd.replace('\\', '/')}

    return showDic

def fetchLinks(content):
    reggi = re.compile("Multiupload\s*(?P<urls>(<a href=\".*?\".*?>.*?</a>\s*)+)", re.IGNORECASE)
    dict_r = {}

    print 'Fetching links from OneDDL.com'
    for release in content.getElementsByTagName("item"):
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

    return dict_r
    
def shouldDownload(config, allowedDic, title):
    (showName, seasonn, episoden, quality) = parseTitle(title)
    for showTitle, showDict in allowedDic.iteritems():
        if showTitle != showName:
            continue
        if showDict['Season'] < int(seasonn):
            continue
        if showDict['Episode'] < int(episoden):
            continue
        if showDict['Quality'].lower() == 'hdtv':
            if quality.lower() != 'hdtv':
                continue
        else:
            if not quality.lower().contains(showDict['Quality'].lower()):
                continue
        config.set(showTitle, 'Season', seasonn)
        config.set(showTitle, 'Episode', episoden)
        return True
    return False

def findIDM():
    try:
        key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Internet Download Manager\\")
        path = _winreg.QueryValueEx(key, "DisplayIcon")[0]
        key.Close()
        return path
    except WindowsError:
        return None

if __name__ == '__main__':
    config = ConfigParser.SafeConfigParser()

    #Set ini file to its initial state
    initialize(config)

    #Parse TV Shows
    showDic = parseShows(config)
    print showDic
    exit(-1)
    #NotJustYet
    h = httplib2.Http(".cache")
    resp, content = h.request("http://www.oneddl.com/feed/rss/", "GET")
    newcontent = parseString(content)
    linksdict = fetchLinks(newcontent)

    print '%d downloads found.' % len(linksdict)

    #Match 'em
    print 'Finding matching downloads...'
    updatedDict = dict([(links,showDic[title]['Path']) for title,links in linksdict.iteritems() if shouldDownload(config, showDic, title)])
    print '%d matching downloads have been found.' % len(updatedLinks)

    with open('OneDDL.ini', 'wb') as fp:
        config.write(fp)
        
    multipattern = "<div id=\"downloadbutton_\" style=\"\"><a href=\"(.*?)\" onclick=\"launchpopunder\(\)\;\">"
    LinkAdder(config.get('General', 'IDMPath'), multipattern).start(updatedDict.iteritems())
