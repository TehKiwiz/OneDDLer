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

    try:
        value = config.get('General', 'DefQuality')
    except ConfigParser.NoOptionError:
        value = ''
    if value.strip() == '':
        print 'Please enter the default quality of the episodes: (Currently only accepts 720p/web/hdtv)'
        qual = raw_input('--> ')
        config.set('General', 'DefQuality', qual)

    try:
        value = config.get('General', 'ne_rss')
    except ConfigParser.NoOptionError:
        value = ''
        
    if value.strip() == '':
        print 'Would you like to import your next-episode watchlist?'
        shouldImport = raw_input('y/n: ')
        if shouldImport == 'y':
            print 'Enter your watchlist rss feed url (You can find it at http://next-episode.net/sitefeeds/)'
            url = raw_input('--> ')
        else:
            url = 'false'
        config.set('General', 'ne_rss', url)

def parseShowsConfig(xConfig):
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
            pathtd = '/'.join([xConfig.get('General', 'DefDownloadPath'), show, ''])
            
        xConfig.set(show, 'PathToDownload', pathtd)    
        showDic[show] = {'Season' : season, 'Episode': episode, 'Quality' : quality, 'Path' : pathtd.replace('\\', '/')}

    return showDic

def parseShowsRss(xConfig, rss_feed):
    dict_r = {}
    reg = re.compile('(\\d+)x(\\d+)')
    
    for item in rss_feed.getElementsByTagName('item'):
        for node in item.childNodes:
            if node.nodeName == 'title':
                index = node.firstChild.wholeText.find('-')
                if index != -1:
                    title = node.firstChild.wholeText[:index].strip().capitalize()
                else:
                    break
                if xConfig.has_section(title):
                    break
                xConfig.add_section(title)
                
            if node.nodeName == 'description':
                match = reg.search(node.firstChild.wholeText)
                if match == None:
                    break
                
                season = int(match.group(1))
                episode = int(match.group(2))

                xConfig.set(title, 'Season', str(season))
                xConfig.set(title, 'Episode', str(episode-1))
                xConfig.set(title, 'Quality', xConfig.get('General', 'defquality'))
                break
    
            
def fetchLinks(content):
    reggi = re.compile("Multiupload\s*(?P<urls>(<a href=\".*?\".*?>.*?</a>\s*)+)", re.IGNORECASE)
    dict_r = {}

    print 'Fetching links from OneDDL.com'
    for release in content.getElementsByTagName("item"):
            for node in release.childNodes:
                if node.nodeName == "title":
                    releases = node.firstChild.wholeText
                if node.nodeName == "description":
                    titles = releases.split('&')
                    linksContent = node.firstChild.wholeText
                    
                    for title in titles:
                        links = []
                        
                        matchi = reggi.search(linksContent)
                        if matchi == None:
                            break
                        
                        matchers = re.finditer("href=\"(.*?)\"", matchi.group("urls"))
                        for match in matchers:
                            links.append(match.group(1))
                            
                        dict_r[title.strip()] = links
                        linksContent = linksContent[matchi.end():]
    return dict_r

def parseTitle(title):
    tvregex = re.compile('(?P<show>.*)S(?P<season>[0-9]{2})E(?P<episode>[0-9]{2}).(?P<quality>.*)[\.-]',re.IGNORECASE)
    matobj = tvregex.match(title)
    if matobj is None:
        return None
    (name, season, episode, quality) = matobj.groups()
    name = name.replace('.', ' ').replace('repack', '').replace('proper', '').strip().lower()
    quality = quality.lower()
    return (name, season, episode, quality)
    
def shouldDownload(config, allowedDic, title):
    try:
        (showName, seasonn, episoden, quality) = parseTitle(title)
    except TypeError:
        return None, None
    for showTitle, showDict in allowedDic.iteritems():
        if showTitle.lower() != showName:
            continue
        if int(seasonn) < showDict['Season']:
            continue
        if int(episoden) < showDict['Episode'] and int(seasonn) == showDict['Season']:
            continue
        
        if showDict['Quality'].lower() == 'hdtv':
            if quality.find('hdtv') == -1 or quality.find('web') != -1 or quality.find('720p') != -1 or quality.find('x264') != -1:
                continue
        else:
            if quality.find(showDict['Quality'].lower()) == -1:
                continue
        print allowedDic[showTitle]['Path']
        
        config.set(showTitle, 'Season', seasonn)
        config.set(showTitle, 'Episode', str(int(episoden)+1))
        
        return showTitle, allowedDic[showTitle]['Path']
    return None, None

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
    h = httplib2.Http()

    #check for next-episode rss in cfg
    try:
        neRss = config.get('General', 'ne_rss')
        if neRss == 'false':
            raise
        resp, content = h.request(neRss, 'GET')
        content = parseString(content)
        parseShowsRss(config, content)
    except:  
        pass
    
    #Parse TV Shows
    showDic = parseShowsConfig(config)
    #print showDic
    #exit(-1)
    #NotJustYet
    resp, content = h.request("http://www.oneddl.com/feed/rss/", "GET")
    newcontent = parseString(content)
    linksdict = fetchLinks(newcontent)
    #print linksdict

    print '%d downloads found.' % len(linksdict)

    #Match 'em
    print 'Finding matching downloads...'
    updatedDict = {}
    for title, links in linksdict.iteritems():
        show, path = shouldDownload(config, showDic, title)
        if path != None and show != None:
            updatedDict[show] = (path, links)
    
    print '%d matching downloads have been found.' % len(updatedDict)

    with open('OneDDL.ini', 'wb') as fp:
        config.write(fp)

    if len(updatedDict) != 0:
        multipattern = "<div id=\"downloadbutton_\" style=\"\"><a href=\"(.*?)\" onclick=\"launchpopunder\(\)\;\">"
        LinkAdder(config.get('General', 'IDMPath'), multipattern).start(updatedDict.iteritems())
