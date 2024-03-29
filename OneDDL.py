from sys import *
from LinkAdder import *
from FolderManagment import *
from xml.dom.minidom import parse, parseString

import logging
import os
import re
#import httplib2
import requests
import ConfigParser
import _winreg
import codecs

def initialize(config):
    logging.debug('Initializing config')

    #config.readfp(codecs.open('OneDDL.ini', 'rb', 'utf8'))
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
            logging.debug('IDM was not found')
            exit(-1)
        config.set('General', 'IDMPath', pathi)

#Get default download path, root folder for downloads
##    try:
##        pathd = config.get('General', 'DefDownloadPath')
##    except ConfigParser.NoOptionError:
##        pathd = ''
##    if pathd.strip() == '':
##        print 'Please enter the default download path (eg: D:/Lol/Crap/)'
##        pathd = raw_input('--> ')
##        logging.debug('Received default download path => %s' % pathd)
##        
##    while pathd.rfind('/') == len(pathd)-1 or pathd.rfind('\\') == len(pathd)-1:
##        pathd = pathd[:len(pathd)-1]
##    config.set('General', 'DefDownloadPath', pathd)

    try:
        value = config.get('General', 'DefQuality')
    except ConfigParser.NoOptionError:
        value = ''
    if value.strip() == '':
        print 'Please enter the default quality of the episodes: (Currently only accepts 720p/web/hdtv)'
        qual = raw_input('--> ')
        logging.debug('Received default quality => %s' % qual)
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
            logging.debug('User chose to use next_episode with url: %s' % url)
        else:
            logging.debug('User chose not to use next_episode')
            url = 'false'
        config.set('General', 'ne_rss', url)

    try:
        main_folder = config.get('General', 'main_folder')
    except ConfigParser.NoOptionError:
        main_folder = ''
    if main_folder.strip() == '':
        print 'Enter your main folder where you store or would like to store your TV Shows:'
        main_folder = raw_input(' >> ')
        logging.debug('User chose a main_folder path.')

    while main_folder.rfind('/') == len(main_folder)-1 or main_folder.rfind('\\') == len(main_folder)-1:
        main_folder = main_folder[:len(main_folder)-1]
        config.set('General', 'main_folder', main_folder)
        
    logging.debug('Done initializing')

def parseShowsConfig(xConfig):
    logging.debug('Parsing shows...')
    showDic = {}
    shows = [x for x in xConfig.sections() if x != 'General']
    for show in shows:
        try:
            season = xConfig.getint(show, 'Season')
            episode = xConfig.getint(show, 'Episode')
            quality = xConfig.get(show, 'Quality')
            logging.debug('Parsing show %s. Season:%d, Episode:%d, Quality:%s' % (show, season, episode, quality))
            
        except ConfigParser.NoOptionError:
            logging.warning('Invalid Show: %s, skipping...' % show)
            continue

        try:
            pathtd = xConfig.get(show, 'PathToDownload')
        except ConfigParser.NoOptionError:
            pathtd = '/'.join([xConfig.get('General', 'main_folder'), show, ''])

        logging.debug('Download path for %s is %s' % (show, pathtd))
        xConfig.set(show, 'PathToDownload', pathtd)    
        showDic[show] = {'Season' : season, 'Episode': episode, 'Quality' : quality, 'Path' : pathtd.replace('\\', '/')}

    logging.debug('Parsing shows: completed')
    return showDic

def parseShowsRss(xConfig, rss_feed):
    logging.debug('Parsing Next-Episode\'s RSS Feed...')
    dict_r = {}
    reg = re.compile('(\\d+)x(\\d+)')
    dirManager = FolderManagment(xConfig.get('General', 'main_folder'))
    
    for item in rss_feed.getElementsByTagName('item'):
        for node in item.childNodes:
            if node.nodeName == 'title':
                #Needs to be rfind since find won't work for 'Hawaii Five-0 - Today'
                index = node.firstChild.wholeText.rfind('-')
                if index != -1:
                    title = node.firstChild.wholeText[:index].replace('\'', '').replace(':', '').replace('(','').replace(')','').strip()
                    title = ' '.join([x.capitalize() for x in title.split(' ')]).strip()
                    logging.debug('Found show in watchlist: %s' % title)
                else:
                    break
                if xConfig.has_section(title):
                    logging.debug('Show already exists in config: %s, skipping...' % title)
                    break
                
                #logging.debug('Adding show from watchlist to config : %s' % title)
                xConfig.add_section(title)
                
            if node.nodeName == 'description':
                match = reg.search(node.firstChild.wholeText)
                if match == None:
                    logging.debug('Could not find episode/season for show %s in watchlist' % title)
                    break
                
                season = int(match.group(1))
                episode = int(match.group(2))

                #logging.debug('Parsed show "%s" from RSS: Episode %d, Season %d' % (title, episode, season))
                xConfig.set(title, 'Season', str(season))
                xConfig.set(title, 'Episode', str(episode-1))
                xConfig.set(title, 'Quality', xConfig.get('General', 'defquality'))
                xConfig.set(title, 'pathtodownload', dirManager.get_folder(title))
                break
    logging.debug('Parsing NE RSS: completed')
            
def fetchLinks(content):
    reggi = re.compile("Multiupload\s*(?P<urls>(<a href=\".*?\".*?>.*?</a>\s*)+)", re.IGNORECASE)
    dict_r = {}

    logging.debug('Fetching links from OneDDL.com')
    
    for release in content.getElementsByTagName("item"):
            for node in release.childNodes:
                if node.nodeName == "title":
                    releases = node.firstChild.wholeText
                if node.nodeName == "description":
                    titles = releases.split('&')
                    linksContent = node.firstChild.wholeText
                    
                    for title in titles:
                        links = []
                        #logging.debug('OneDDL.com release: %s' % title)
                        
                        matchi = reggi.search(linksContent)
                        if matchi == None:
                            break
                        
                        matchers = re.finditer("href=\"(.*?)\"", matchi.group("urls"))
                        for match in matchers:
                            links.append(match.group(1))

                        #logging.debug('Links for %s: %s' % (title, links))
                        dict_r[title.strip()] = links
                        linksContent = linksContent[matchi.end():]

    logging.debug('Fetched links from OneDDL.com!')
    return dict_r

def parseTitle(title):
    #logging.debug('Parsing release %s fetched from OneDDL' % title)
    tvregex = re.compile('(?P<show>.*)S(?P<season>[0-9]{2})E(?P<episode>[0-9]{2}).(?P<quality>.*)[\.-]',re.IGNORECASE)
    matobj = tvregex.match(title)
    if matobj is None:
        logging.debug("Couldn't parse OneDDL release: %s" % title)
        return None
    (name, season, episode, quality) = matobj.groups()
    name = name.replace('.', ' ').replace('repack', '').replace('proper', '').strip().lower()
    #Need to remove the '2010' from 'Hawaii Five-0 2010'
    name = re.sub('\s?\d{4}\s?', '', name).strip()
    quality = quality.lower()
    logging.debug('Parsed OneDDL release %s: Name "%s", Season "%s", Episode "%s", Quality "%s"' % (title, name, season, episode, quality))
    return (name, season, episode, quality)
    
def shouldDownload(config, allowedDic, title):
    logging.debug('Checking release %s against show dictionary' % title)
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
        #print allowedDic[showTitle]['Path']

        logging.debug('Match found for release %s' % title)
        
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
    #Start logging to file
    logging.basicConfig(filename='OneDDL.log',level=logging.DEBUG)

    logging.info('Started Job')
    
    config = ConfigParser.SafeConfigParser()
    #Set ini file to its initial state
    initialize(config)

    #check for next-episode rss in cfg
    try:
        neRss = config.get('General', 'ne_rss')
        if neRss == 'false':
            raise
        content = requests.get(neRss).content
        content = parseString(content)
        parseShowsRss(config, content)
    except:
        logging.debug('exception at %s: %s' % (__name__, exc_info()))
    
    #Parse TV Shows
    showDic = parseShowsConfig(config)

    try:
        url = "http://www.oneddl.com/feed/rss/"
        if len(argv) == 3:
            custom = argv[1].strip()
            if custom == '-f' or custom == '--feed':
                url = argv[2].strip()
                logging.debug('User chose a custom feed URL: %s' % url)
        content = requests.get(url).content
        newcontent = parseString(content.encode( "utf-8" ))
        linksdict = fetchLinks(newcontent)
    except requests.RequestException:
        logging.exception('Something went wrong fetching a page')

    print '%d downloads found.' % len(linksdict)

    #Match 'em
    print 'Finding matching downloads...'
    updatedDict = {}
    for title, links in linksdict.iteritems():
        show, path = shouldDownload(config, showDic, title)
        if path != None and show != None:
            if updatedDict.has_key(show):
                logging.debug('Show already in queue dictionary. Appending links:\n%s', links)
                [updatedDict[show][1].append(link) for link in links]
            else:
                updatedDict[show] = (path, links)
            
    with open('OneDDL.ini', 'wb') as fp:
        config.write(fp)

    if len(updatedDict) != 0:
        multipattern = "<div id=\"downloadbutton_\" style=\"\"><a href=\"(.*?)\" onclick=\"launchpopunder\(\)\;\">"
        logging.debug('Sending links to LinkAdder')
        LinkAdder(config.get('General', 'IDMPath'), multipattern).start(updatedDict.iteritems())
    logging.info('Finished job')
