# -*- coding: utf-8 -*-

"""

The following call will return a list of all support channels, there IDs and categories.

http://common-app-st.sim-technik.de/applications/mega-app/mega.json

This call will show the highlights of a geiven channel.
CHANNAL : [pro7|sat1|kabel1|sixx]
DEVICE: [phone|tablet] - tablet is preferred because of the bigger images

http://contentapi.sim-technik.de/mega-app/v1/[CHANNEL]/[DEVICE]/homepage

This call returns a list the library (Mediathek). Shows are divided into archived and currently running shows.

http://contentapi.sim-technik.de/mega-app/v1/[CHANNEL/[DEVICE]/format

all other requests are originating from the following url:
http://contentapi.sim-technik.de/[PATH] 

"""

import xbmcplugin
import xbmcgui
import xbmcaddon

import os
import re
import urllib
import urllib2
import json
import datetime

from bromixbmc import Bromixbmc
from SevenTv import SevenTv

#import pydevd
#pydevd.settrace('localhost', stdoutToServer=True, stderrToServer=True)

ACTION_SHOW_CHANNEL_HIGHLIGHTS = "showChannelHighlights"
ACTION_SHOW_CHANNEL_CONTENT = "showChannelContent"
ACTION_SHOW_SHOW_CONTENT = "showShowContent"
ACTION_PLAY = "play"
ACTION_SEARCH = "search"
ACTION_ADD_SHOW_TO_FAVS = "addShowToFavs"
ACTION_REMOVE_SHOW_FROM_FAVS = "removeShowFromFavs"
ACTION_SHOW_FAVORITE_SHOWS = "showFavoriteShows"
ACTION_SHOW_NEW_VIDEOS = "showNewVideos"

bromixbmc = Bromixbmc("plugin.video.7tv", sys.argv)

__addon_data_path__ = bromixbmc.Addon.DataPath
if not os.path.isdir(__addon_data_path__):
    os.mkdir(__addon_data_path__)

sevenTv = SevenTv(os.path.join(__addon_data_path__, 'favs.dat'))

SETTING_SHOW_FANART = bromixbmc.Addon.getSetting('showFanart')=="true"
SETTING_SHOW_PUCLICATION_DATE = bromixbmc.Addon.getSetting('showPublicationDate')=="true"

__CHANNELS__ = {'pro7': {'name': 'ProSieben',
                         'logo': os.path.join(bromixbmc.Addon.Path, "resources/media/logo_pro7.png")
                         },
                'sat1': {'name': 'SAT.1',
                         'logo': os.path.join(bromixbmc.Addon.Path, "resources/media/logo_sat1.png")
                         },
                'kabel1': {'name': 'kabel eins',
                           'logo': os.path.join(bromixbmc.Addon.Path, "resources/media/logo_kabel1.png")
                           },
                'sixx': {'name': 'sixx',
                         'logo': os.path.join(bromixbmc.Addon.Path, "resources/media/logo_sixx.png")
                         },
                'prosiebenmaxx': {'name': 'ProSieben MAXX',
                                  'logo': os.path.join(bromixbmc.Addon.Path, "resources/media/logo_pro7maxx.png")
                                  },
                'sat1gold': {'name': 'SAT.1 Gold',
                             'logo': os.path.join(bromixbmc.Addon.Path, "resources/media/logo_sat1gold.png")
                             }
                }

__ICON_SEARCH__ = os.path.join(bromixbmc.Addon.Path, "resources/media/search.png")
__ICON_HIGHLIGHTS__ = os.path.join(bromixbmc.Addon.Path, "resources/media/highlight.png")
__ICON_FAVORITES__ = os.path.join(bromixbmc.Addon.Path, "resources/media/pin.png")

def play(channelId, episodeId):
    videoUrl = sevenTv.getVideoUrl(episodeId)
    if videoUrl!=None:
        listitem = xbmcgui.ListItem(path=videoUrl)
        xbmcplugin.setResolvedUrl(bromixbmc.Addon.Handle, True, listitem)

def search():
    result = False
    keyboard = xbmc.Keyboard('', bromixbmc.Addon.localize(30000))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        result = True
        
        search_string = keyboard.getText().replace(" ", "+")
        screen_objects = sevenTv.search(search_string)
        
        # first list the shows
        for screen_object in screen_objects:
            title = screen_object.get('title', '')
            if title=='Sendungen':
                screen_objects2 = sevenTv.getSortedScreenObjects(screen_object)
                for screen_object2 in screen_objects2:
                    id = screen_object2.get('id', '')
                    parts = id.split(':')
                    if len(parts)>=2:
                        channel = parts[0]
                        addScreenObject(channel, screen_object2)
                break
            
        # list the rest
        for screen_object in screen_objects:
            title = screen_object.get('title', '')
            if title!='Sendungen':
                screen_objects2 = sevenTv.getSortedScreenObjects(screen_object)
                for screen_object2 in screen_objects2:
                    id = screen_object2.get('format_id', '')
                    parts = id.split(':')
                    if len(parts)>=2:
                        channel = parts[0]
                        addScreenObject(channel, screen_object2)
                    
    xbmcplugin.endOfDirectory(bromixbmc.Addon.Handle, succeeded=result)
    return True

def showIndex():
    # try to load favorites
    favs = bromixbmc.Addon.getFavorites()
    if len(favs)>0:
        params = {'action': ACTION_SHOW_FAVORITE_SHOWS}
        bromixbmc.addDir("[B]"+bromixbmc.Addon.localize(30005)+"[/B]", params=params, thumbnailImage=__ICON_FAVORITES__)
        
        params = {'action': ACTION_SHOW_NEW_VIDEOS}
        bromixbmc.addDir("[B]"+bromixbmc.Addon.localize(30012)+"[/B]", params=params, thumbnailImage=__ICON_HIGHLIGHTS__)
        pass
    
    for key in __CHANNELS__:
        channel = __CHANNELS__[key]
        name = channel.get('name', None)
        thumbnailIamge = channel.get('logo', None)
        if name!=None and thumbnailIamge!=None:
            params = {'channel': key,
                      'action': ACTION_SHOW_CHANNEL_CONTENT}
            bromixbmc.addDir(name, params=params, thumbnailImage=thumbnailIamge)
            pass
        pass
    
    params = {'action': ACTION_SEARCH}
    bromixbmc.addDir('[B]'+bromixbmc.Addon.localize(30000)+'[/B]', params=params, thumbnailImage=__ICON_SEARCH__)
    
    xbmcplugin.endOfDirectory(bromixbmc.Addon.Handle)

def localizeString(text):
    if text=='Aktuell':
        return bromixbmc.Addon.localize(30001)
    elif text=='Highlight':
        return bromixbmc.Addon.localize(30002)
    elif text=='Archiv':
        return bromixbmc.Addon.localize(30007)
    elif text=='Beliebte Sendungen':
        return bromixbmc.Addon.localize(30010)
    elif text=='Aktuelle ganze Folgen':
        return bromixbmc.Addon.localize(30011)
    elif text=='Neueste Videos':
        return bromixbmc.Addon.localize(30012)
    return text

def showChannelContent(channelId):
    channel = __CHANNELS__.get(channelId, None)
    if channel!=None:
        thumbnailImage = channel.get('logo', '')
        
        # first try to show the highlights
        highlights = sevenTv.getChannelHighlights(channelId)
        if len(highlights)>0:
            params = {'channel': channelId,
                      'action': ACTION_SHOW_CHANNEL_HIGHLIGHTS}
            
            bromixbmc.addDir(bromixbmc.Addon.localize(30002), params=params, thumbnailImage=thumbnailImage)
        
        # show the library
        library = sevenTv.getChannelLibrary(channelId)
        for lib in library:
            title = lib.get('title', '')
            # ignore favs.
            if title!='Favoriten':
                params = {'channel': channelId,
                          'action': ACTION_SHOW_CHANNEL_CONTENT,
                          'category': title}
                
                bromixbmc.addDir(localizeString(title), params=params, thumbnailImage=thumbnailImage)
        pass
    
    xbmcplugin.endOfDirectory(bromixbmc.Addon.Handle)

def addScreenObject(channel, screen_object, fanart=None, addToFavs=True, showFormatTitle=False):
    type = screen_object.get('type', '')
    
    if type=='format_item' or type=='format_item_home':
        title = screen_object.get('title', None)
        show = screen_object.get('id', None)
        thumbnailImage = screen_object.get('image_url', None)
        if title!=None and show!=None:
            params = {'channel': channel,
                      'action': ACTION_SHOW_SHOW_CONTENT,
                      'show': show}
            
            contextMenu = None
            if addToFavs:
                urlParams = {'channel': channel,
                             'show': show,
                             'action': ACTION_ADD_SHOW_TO_FAVS}
                
                contextRun = 'RunPlugin('+bromixbmc.createUrl(urlParams)+')'
                contextMenu = [("[B]"+bromixbmc.Addon.localize(30014)+"[/B]", contextRun)]
            else:
                urlParams = {'channel': channel,
                             'show': show,
                             'action': ACTION_REMOVE_SHOW_FROM_FAVS}
                
                contextRun = 'RunPlugin('+bromixbmc.createUrl(urlParams)+')'
                contextMenu = [("[B]"+bromixbmc.Addon.localize(30015)+"[/B]", contextRun)]
            
            bromixbmc.addDir(title, params=params, thumbnailImage=thumbnailImage, contextMenu=contextMenu)
    elif type=='video_item_date_no_label' or type=='video_item_format' or type=='video_item_format_no_label' or type=='video_item_date':
        title = screen_object.get('video_title', '')
        thumbnailIamge = screen_object.get('image_url', '')
        
        #try to get a better image quality
        thumbnailIamge = thumbnailIamge.replace('mega_app_420x236', 'mega_app_566x318')
        
        format_title = screen_object.get('format_title', '')
        duration = screen_object.get('duration', '0')
        duration = int(duration/60)
        if duration==0:
            duration=1
            
        id= screen_object.get('id', '')
        
        aired = ""
        year = ""
        if SETTING_SHOW_PUCLICATION_DATE:
            match = re.compile('(\d*)\.(\d*)\.(\d*)', re.DOTALL).findall(screen_object['publishing_date'])
            if match!=None and len(match[0])>=3:
                date_format = xbmc.getRegion('dateshort')
                
                date_format = date_format.replace('%d', match[0][0])
                date_format = date_format.replace('%m', match[0][1])
                date_format = date_format.replace('%Y', match[0][2])
                year = match[0][2]
                
                aired = date_format+" - "
        
        name = title
        if showFormatTitle or type=='video_item_format_no_label' or type=='video_item_format':
            name = format_title+" - "+title
            
        name = aired + name
        params = {'channel': channel,
                  'episode': id,
                  'action': ACTION_PLAY
                  }
        additionalInfoLabels = {'year': year,
                                'duration': duration}
        bromixbmc.addVideoLink(name, params=params, thumbnailImage=thumbnailIamge, fanart=fanart, additionalInfoLabels=additionalInfoLabels)
        pass

def showChannelLibrary(channelId, formatFilter):
    formats = sevenTv.getChannelLibrary(channelId)
    for format in formats:
        if format.get('title','')==formatFilter:
            screen_objects = sevenTv.getShowsFromScreenObject(format)
            for screen_object in screen_objects:
                addScreenObject(channelId, screen_object)
                
    xbmcplugin.endOfDirectory(bromixbmc.Addon.Handle)

def showShowContent(channelId, show, category=''):
    xbmcplugin.setContent(bromixbmc.Addon.Handle, 'episodes')
    
    # default: show full episodes
    if category=='':
        category='Ganze Folgen'
    
    screen_objects = sevenTv.getShowContent(channelId, show)
    
    fanart = sevenTv.getFanartFromShowContent(screen_objects)
    
    channel = __CHANNELS__.get(channelId, None)
    if channel!=None:
        thumbnailImage = channel.get('logo', '')
        
        videoList = None
        # list all objects except 'Ganze Folgen' = full episodes
        for screen_object in screen_objects:
            title = screen_object.get('title', '')
            if title==category:
                videoList = screen_object
                
            if title!='Ganze Folgen' and category=='Ganze Folgen' and title!='Favoriten':
                if len(screen_object.get('screen_objects', {}))>0:
                    params = {'channel': channelId,
                              'show': show,
                              'action': ACTION_SHOW_SHOW_CONTENT,
                              'category': title.encode('utf-8')}
                    bromixbmc.addDir("[B]"+localizeString(title)+"[/B]", params=params, thumbnailImage=thumbnailImage, fanart=fanart)
                    
        if videoList!=None:
            sorted_videos = sevenTv.getSortedScreenObjects(videoList)
            for screen_object in sorted_videos: 
                addScreenObject(channelId, screen_object, fanart)
        pass
    
    xbmcplugin.endOfDirectory(bromixbmc.Addon.Handle)

def showChannelHighlights(channelId, category=''):
    highlights = sevenTv.getChannelHighlights(channelId)
    
    channel = __CHANNELS__.get(channelId, None)
    if channel!=None:
        thumbnailImage = channel.get('logo', '')
    
        showHighlight = None
        for highlight in highlights:
            title = highlight.get('title', '')
            if category!='' and title==category:
                showHighlight = highlight
                break
            
            if category=='' and title!='' and title!='Favoriten' and title!='Live TV' and title!='Deine gemerkten Videos' and title!='Empfehlungen':
                params = {'channel': channelId,
                          'action': ACTION_SHOW_CHANNEL_HIGHLIGHTS,
                          'category': title.encode('utf-8')}
                bromixbmc.addDir(localizeString(title), params=params, thumbnailImage=thumbnailImage)
                pass
            
        if showHighlight!=None:
            screen_objects = sevenTv.getSortedScreenObjects(showHighlight)
            for screen_object in screen_objects:
                addScreenObject(channelId, screen_object)
        pass
    
    xbmcplugin.endOfDirectory(bromixbmc.Addon.Handle)

def showFavoriteShows():
    favs = bromixbmc.Addon.getFavorites()
    ids = []
    for fav in favs:
        ids.append(fav[0])
    
    favs = sevenTv.getFavoriteShows(ids)
    for fav in favs:
        id = fav.get('id', '')
        parts = id.split(':')
        if len(parts)>=2:
            channel = parts[0]
            addScreenObject(channel, fav, addToFavs=False)
    xbmcplugin.endOfDirectory(bromixbmc.Addon.Handle)
    return True

def showNewVideos():
    xbmcplugin.setContent(bromixbmc.Addon.Handle, 'episodes')
    
    favs = bromixbmc.Addon.getFavorites()
    ids = []
    for fav in favs:
        ids.append(fav[0])
        
    newVideos = sevenTv.getNewVideos(ids)
    
    for newVideo in newVideos:
        id = newVideo.get('format_id', '')
        parts = id.split(':')
        if len(parts)>=2:
            channel = parts[0]
            addScreenObject(channel, newVideo, addToFavs=False, showFormatTitle=True)
    xbmcplugin.endOfDirectory(bromixbmc.Addon.Handle)
    return True

def addShowToFav(channel, show):
    newFav = {'channel': channel,
              'show': show}
    bromixbmc.Addon.addFavorite(show, newFav)
    
def removeShowFromFav(channel, show):
    bromixbmc.Addon.removeFavorite(show)
    xbmc.executebuiltin("Container.Refresh")

action = bromixbmc.getParam('action')
channel = bromixbmc.getParam('channel')
show = bromixbmc.getParam('show')
category = bromixbmc.getParam('category', '').decode('utf-8')
episode = bromixbmc.getParam('episode')

if channel!=None and category=='' and action==ACTION_SHOW_CHANNEL_CONTENT:
    showChannelContent(channel)
elif channel!=None and category!='' and action==ACTION_SHOW_CHANNEL_CONTENT:
    showChannelLibrary(channel, category)
elif channel!=None and action==ACTION_SHOW_CHANNEL_HIGHLIGHTS:
    showChannelHighlights(channel, category)
elif channel!=None and show!=None and action==ACTION_SHOW_SHOW_CONTENT:
    showShowContent(channel, show, category)
elif channel!=None and episode!=None and action==ACTION_PLAY:
   play(channel, episode)
elif action==ACTION_SEARCH:
    search()
elif channel!=None and show!=None and action==ACTION_ADD_SHOW_TO_FAVS:
    addShowToFav(channel, show)
elif channel!=None and show!=None and action==ACTION_REMOVE_SHOW_FROM_FAVS:
    removeShowFromFav(channel, show)
elif action==ACTION_SHOW_FAVORITE_SHOWS:
    showFavoriteShows()
elif action==ACTION_SHOW_NEW_VIDEOS:
    showNewVideos()
else:
    showIndex()
