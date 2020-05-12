from google.appengine.api import memcache

import feedparser
import settings
import time
import models
import re
import socket

def getLatestLinkNotSub(submitter_name):
    entry=None
    url = settings.RSS_SOURCES_URL[submitter_name]
    p = feedparser.parse(url)
    if len(p.entries) > 0:
        entry = p.entries[0]
    else: 
        return None
    last_10_memkey = 'rss_lastid:'+submitter_name
    last_10_sub = memcache.get(last_10_memkey)
    if last_10_sub is None:
        last_10_sub = []
    if submitter_name == 'theonion' and entry.title.strip().lower().endswith("in review"):
        return None
    if hasattr(entry,'guid'):
        unique_id = entry.guid
    elif hasattr(entry,'feedburner_origlink'):
        unique_id = entry.feedburner_origlink
    else:
        unique_id = entry.link
    if submitter_name in ( 'stephencolbert', 'thedailyshow','comedycentral'):
        num_ent = len(p.entries)
        i=num_ent-1
        while ('/' in entry.title or 
        len(entry.title.split()) <=2  or  #interviews title tend to be names (2 words); we don't want them
        entry.guid in last_10_sub or
        re.search(settings.CC_RSS_EXCLUDE,entry.title.lower()) != None):
            i-=1
            if i < 0:
                return None
            else:
                entry=p.entries[i]
    elif unique_id in last_10_sub:
        return None  
    if len(last_10_sub) >10:
        last_10_sub.pop()
    last_10_sub.insert(0,unique_id)
    memcache.set(key=last_10_memkey,value=last_10_sub)
    return entry

def import_feeds(freq_type='daily'):
    sources = settings.RSS_SOURCES[freq_type]
    num_links = 0
    for submitter_name in sources:
        link = getLatestLinkNotSub(submitter_name)
        if link is not None:
            submitter = models.user.getUserByName(submitter_name)
            if submitter is None:
                submitter = models.usermanager.createUser(username=submitter_name,
                                      password=settings.SECRET_KEY)
            try:
                if submitter_name == 'theonion':
                    url = link.guid.strip()
                elif hasattr(link,'feedburner_origlink'):
                    url = link.feedburner_origlink.strip()
                else:
                    url = link.link.strip()
                if submitter =='dilbert':
                    title = "Dilbert: "+link.title
                else:
                    title = link.title
                link = models.link.createLink(url,title=link.title,submitter=submitter)
                num_links +=1
            except:
                if settings.DEV_SERVER:
                    raise
                else:
                    pass
                
    return num_links
                    
                    
                    