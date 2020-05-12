
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from utils.http import urlquote

from google.appengine.ext import db
from google.appengine.api import memcache

import models
import settings
import session

from datetime import datetime

#def sessionize(method):
#    @functools.wraps(method)
#    def wrap(*args, **kwds):
#        request = args[0]
#        session.startSession(request)
#        return session.processResponse(request,method(request, *args, **kwds))
#    return wrap

def _checkLoggedIn(request):
    request.logged_in = False
    request.user = None
    request.session_id = None
    session_id = request.COOKIES.get(settings.SESSION_COOKIE_NAME, None)
    if session_id is not None:
        usession = session.getSession(session_id)
        if usession is not None:
            request.session = usession
            request.session_id = usession.id
            if session.USERNAME_KEY in request.session.keys():
                username = request.session[session.USERNAME_KEY]
                if username is not None:
                    user = models.getUserByName(username)
                    if user is not None:
                        request.logged_in = True
                        request.user = user
    return request


class get_user(object):
    """decorator for view function, which must have request as its first argument. 
    checks if user is logged in, and updates request object. """
    def __init__(self, func):
        self.func = func
        
    def __call__(self, *args,**kwargs):
        request = args[0]
        request = _checkLoggedIn(request)
        response = self.func(*args,**kwargs)
        if request.logged_in and request.session._dirty:
            request.session.save()
        return response
 
class require_login(object):
    """decorator for view function, which must have request as its first argument. 
    checks if user is logged in, and if not redirects to login page """
    def __init__(self, func):
        self.func = func
        
    def __call__(self, *args,**kwargs):
        request = args[0]
        request = _checkLoggedIn(request)
        if not request.logged_in:
            path = urlquote(request.get_full_path())
            tup = settings.LOGIN_PATH, settings.REDIRECT_FIELD_NAME, path
            return HttpResponseRedirect('%s?reason=login_required&%s=%s' % tup)
        response = self.func(*args,**kwargs)
        if request.logged_in and request.session._dirty:
            request.session.save()
        return response

def login(request,user,remember):
    request.session = session.createSession()
    request.session[session.USERID_KEY] = user.id
    request.session[session.USERNAME_KEY] = user.name
    request.session.remember = remember
    request.session._dirty = True
    if 'redirect' in request.POST and request.POST['redirect'] != '':
        redirect_path = request.POST['redirect']
        response = HttpResponseRedirect(redirect_path)
    else:
        response = HttpResponseRedirect(reverse(settings.LOGIN_REDIRECT_VIEW)) 
    return session.processResponse(request,response)
      
def logout(request,response):
    if request.method == 'POST':
        session.startSession(request)
        session_id = request.session.id
        response.delete_cookie(key=settings.SESSION_COOKIE_NAME,domain=session.getCookieDomain())
        if 'logout_key' in request.POST.keys():
            logout_key = request.POST['logout_key']
            if logout_key == session_id:
                db.delete(request.session)
                memcache.delete(session_id)
    return response

#def get_user(method,login_required=False):
#    @functools.wraps(method)
#    def wrap(*args, **kwds):
#        request = args[0]
#        request = _checkLoggedIn(request)
#        if request.logged_in and request.session._dirty:
#            request.session.save()
#        if login_required and not request.logged_in:
#            path = urlquote(request.get_full_path())
#            tup = settings.LOGIN_PATH, settings.REDIRECT_FIELD_NAME, path
#            return HttpResponseRedirect('%s?%s=%s' % tup)
#            response = method(request, *args, **kwds)
#        return response
#    return wrap

    
            
def authenticate(username,password):
    return models.authenticate(username,password)

    
    
    