#
# Copyright 2009 Max Lambert
#
#models.py
#contains all models for the funniestlinks site
#

import base64
import cPickle as pickle
from datetime import datetime
import settings
import hashlib
import random
import time
import re

from google.appengine.ext import db
from google.appengine.api import memcache

from random import randrange


MAX_SESSION_KEY = 18446744073709551616L     # 2 << 63


"""
Custom Exceptions

"""

class Error(Exception):
	pass

class SuspiciousOperation(Error):
    def __init__(self):
		self.message = "dude, seriously."
   
class InvalidPasswordError(Error):
	def __init__(self):
		self.message = ("Invalid Password. Password must be between " +
						str(settings.MIN_PASS_LEN)  + " and " +
						str(settings.MAX_PASS_LEN)  + " characters long.")

class InvalidEmailError(Error):
	def __init__(self):
		self.message = "Email address invalid"

class InvalidUsernameError(Error):
	def __init__(self):
		self.message = ("Username Invalid. It needs to be less than " +
					    str(settings.MAX_USERNAME_LEN) + " characters long" +
					    " and can only contain letters, numbers and _ (underscore)")

class InvalidLinkError(Error):
	def __init__(self):
		self.message = "url given is too long. url needs to be less than 250 characters."

class InvalidUserPassComb(Error):
	def __init__(self):
		self.message = "Username/Password combination is invalid."

class UsernameUsedError(Error):
	def __init__(self):
		self.message = "Username address already in use. Please choose another one."

class EmailUsedError(Error):
	def __init__(self):
		self.message = "Email address already in use. Please choose another one."

"""
static methods

"""


def encodeSessionDict(session_dict):
    pickled ='3'
    pickled = pickle.dumps(session_dict, pickle.HIGHEST_PROTOCOL)
    pickled_md5 = hashlib.md5(pickled + settings.SECRET_KEY).hexdigest()
    return base64.encodestring(pickled + pickled_md5)

def _getNewSessionKey():
        "Returns session key that isn't being used."
        # The random module is seeded when this Apache child is created.
        # Use settings.SECRET_KEY as added salt.
        while 1:
            h = hashlib.new(settings.DEFAULT_HASH_ALG)
            h.update("%s%s%s" % (randrange(0, settings.MAX_SESSION_KEY), 
                                 time.time(), settings.SECRET_KEY))
            session_key = h.hexdigest()
            if Session.get_by_key_name(session_key) == None:
                break
        return session_key 

def getSession(session_key):
    session = Session.get_by_key_name(session_key)
    return session
    
def getNewSession():   
    new_session_key = _get_new_session_key()
    session = Session(session_key = new_session_key, key_name=new_session_key,
                      expire_date=settings.SESSION_EXPIRE_TIME)
    db.put(session)
    return session
    
def createStringId(num):
	res = ""
	x=num
	while x > 0:
		digit = x % len(settings.SHORT_URL_CHARS)
		res = settings.SHORT_URL_CHARS[digit] + res
		x = int(x / len(settings.SHORT_URL_CHARS))
	return res

def getCounter(ckey_name):
	counter = DisCounter.get_by_key_name(ckey_name)
	if counter is None:
		counter = DisCounter(key_name = ckey_name, 
							 num_shards = settings.DEFAULT_NUM_SHARDS)
		db.put(counter)
		counter.start()
	return counter

def getHash(raw_password,algorithm=settings.DEFAULT_HASH_ALG):
	h = hashlib.new(settings.DEFAULT_HASH_ALG)
	h.update(raw_password)
	h.update(settings.SECRET_KEY)
	return h.hexdigest()

def createLink(url,submitter):
	if len(url) > settings.MAX_STRINGLEN: 
		raise InvalidLinkError( ("url given too long. " + str(settings.MAX_STRINGLEN)
								   + " character limit." ))
	link_counter = getCounter(settings.GLOBAL_LINK_COUNTER_NAME)
	link_counter.increment()
	link_id = link_counter.getCount()
	string_id = createStringId(link_id)
	view_counter = getCounter('view_counter_'+string_id)
	upvote_counter = getCounter('upvote_counter_'+string_id)
	link = Link(num_id=link_id, string_id=string_id, url=url,
			    submitter=submitter, view_counter=view_counter,
			    upvote_counter=upvote_counter
			    )
	db.put(link)
	return link

def isEmailUsed(email):
	query = db.GqlQuery("SELECT * FROM User WHERE email = :1",email)
	existing_email = query.fetch(1)
	return len(existing_email) > 0

def _commitNewUser(username,email,password):
	if isUsernameUsed(username):
		raise UsernameUsedError()
	else:
		user = User(username=username, email=email, key_name = username)
		user.setPassword(password)
		db.put(user)
		return user
						
def createUser(username,email,password):
	if not validateUsername(username):
		raise InvalidUsernameError()
	elif isUsernameUsed(username):
		raise UsernameUsedError()
	elif not validateEmail(email):
		raise InvalidEmailError()
	elif not validatePassword(password):
		raise InvalidPasswordError()
	elif isEmailUsed(email):
		raise EmailUsedError()
	else:
		user = db.run_in_transaction(_commitNewUser,username,email,password)	
		if user is not None:
			usercounter = getCounter(settings.GLOBAL_USER_COUNTER_NAME)
			usercounter.increment()
		return user

def deleteUser(username):
	user = User.get_by_key_name(username)
	if user is not None:
		user.delete()
		usercounter = getCounter(settings.GLOBAL_USER_COUNTER_NAME)
		usercounter.decrement()
		return True
	return False
			
def authenticate(given_username,given_pass):
	if validatePassword(given_pass) and validateUsername(given_username):
		user = User.get_by_key_name(given_username)
		if user is not None:
			hash_given_pass = getHash(given_pass)
			if user.hash_pass == hash_given_pass:
				return user
	return None

def getUser(username):
	return User.get_by_key_name(username)

def isUsernameUsed(username):
	user = getUser(username)
	return user is not None

def validateEmail(email_str):
    if len(email_str) < settings.MAX_STRINGLEN and len(email_str) > 6:
        if re.match("(\w+@[a-zA-Z_]+?\.[a-zA-Z]{2,6})$", email_str) != None:
            return True
    return False
   
def validateUsername(username):
    if len(username) <= settings.MAX_USERNAME_LEN:
	    if re.match("[A-Za-z0-9_]+$", username) != None:
	        return True
    return False	

def validatePassword(password):
    return len(password) >= settings.MIN_PASS_LEN and len(password) <= settings.MAX_PASS_LEN	



""" 

Model Classes

"""

class Session(db.Model):
    session_key = db.StringProperty(required=True,indexed=True)
    session_data = db.TextProperty()
    expire_date = db.DateTimeProperty()
    accessed = db.BooleanProperty(default=False)
    modified = db.BooleanProperty(default=False)
           
    def decode(self):
        encoded_data = base64.decodestring(self.session_data)
        pickled, tamper_check = encoded_data[:-32], encoded_data[-32:]
        if hashlib.md5(pickled + settings.SECRET_KEY).hexdigest() != tamper_check:
            raise SuspiciousOperation()
        try:
            return pickle.loads(pickled)
        # Unpickling can cause a variety of exceptions. If something happens,
        # just return an empty dictionary (an empty session).
        except:
            return {}

    def getSessionKey(self):
        return self.session_key
        
    def getExpiryAge(self):
        """get expiry age in seconds"""
        delta = self.expire_date - datetime.now()
        return delta.days * 86400 + delta.seconds   

    def setExpiry(self, seconds_from_now):
        d = datetime.timedelta(seconds=seconds_from_now)
        value = datetime.now() + d
        self.expire_date = value
        self.put()
    
    def update(self,_dict):
        if _dict:
            session.session_data = _encodeSessionDict(_dict)
            self.put()



class DisCounter(db.Model):
	"""
	Distributed counter
	"""
	num_shards = db.IntegerProperty(required=True)
			
	def getCount(self):
		total = memcache.get(str(self.key()))
		if total is None:
			total=0
			for counter in self._subcounter_set:
				total+=counter.count
			memcache.set(key=str(self.key()),value=total,time=settings.COUNTER_CACHE_TIME)
		return total
	
	def _crement(self,delta=1):
		counter_id = self.getCount() % self.num_shards
		ckey = self._getSubCounterKeyName(counter_id)
		def trans():
			counter = _SubCounter.get_by_key_name(ckey)
			counter.count += delta
			counter.put()	
		db.run_in_transaction(trans)
		
	def decrement(self):
		self._crement(delta=-1)
		memcache.decr(str(self.key()),1)
		
	def increment(self):
		self._crement(delta=1)
		memcache.incr(str(self.key()),1)
	
	def start(self):
		"""
		This method creates the subcounters and must be called after creating
		an instance of DisCounter and saving it by calling put(). 
		"""
		memcache.set(key=str(self.key()),value=0,time=settings.COUNTER_CACHE_TIME)
		for i in range(0,self.num_shards):
			subcounter_key = self._getSubCounterKeyName(i)
			newcounter = _SubCounter(par_counter=self.key(), key_name=subcounter_key)
			newcounter.put()
			
	def _getSubCounterKeyName(self,counter_id):
		return str(self.key().id_or_name())+str(counter_id)

class _SubCounter(db.Model):
	""" 
	Represents 'subcount' used by the Counter to distribute count	
	"""	
	count = db.IntegerProperty(default=0)
	par_counter = db.ReferenceProperty(DisCounter)
	
class User(db.Model):
	email = db.StringProperty(indexed=True)
	username = db.StringProperty(required=True,indexed=True)
	points = db.IntegerProperty(default=0)
	create_date = db.DateTimeProperty(auto_now_add=True)
	last_login = db.DateTimeProperty()
	hash_pass = db.StringProperty()
	
	def setPassword(self, password):	
		if validatePassword(password):
			self.hash_pass = getHash(raw_password=password)
		else: 
			raise InvalidPasswordError()
			 		 
		 
class Link(db.Model):
	url = db.StringProperty(required=True, indexed=True)
	num_id = db.IntegerProperty(required=True)
	string_id = db.StringProperty(required=True,indexed=True)
	submitter = db.ReferenceProperty(User,required=True)
	submitted_date = db.DateTimeProperty(auto_now_add=True)
	view_counter = db.ReferenceProperty(reference_class = DisCounter, collection_name = "view_counter", required=True)
	upvote_counter = db.ReferenceProperty(reference_class = DisCounter, collection_name = "upvote_counter",required=True)

	def _commitView(self,user,userviewkey,view_date):	
		userview = UserView.get_by_key_name(userviewkey)
		if userview is None:
			userview = UserView(user=user.key(), link=self.key(),view_date = view_date, key_name = userviewkey)
			db.put(userview)
			return True
		return False
	
	def viewed(self,user):
		userviewkey = UserView.getUserViewKey(self, user)
		view_date = datetime.now()
		if db.run_in_transaction(self._commitView,user,userviewkey,view_date):
			self.view_counter.increment()
	
	def upvote(self,user):
		uservotekey = UserVote.getUserVoteKey(self, user)
		vote_date = datetime.now()
		if db.run_in_transaction(self._commitUpvote,user,uservotekey,vote_date):
			self.upvote_counter.increment()

	def _commitUpvote(self,user,uservotekey,vote_date):
		uservote = UserVote.get_by_key_name(uservotekey)
		if uservote is None:
			uservote = UserVote(user=user.key(), link=self.key(),vote_date = vote_date,key_name = uservotekey)
			db.put(uservote)
			return True
		return False
		
	def getUpvotes(self):
		return self.upvote_counter.getCount()

	def getViews(self):
		return self.view_counter.getCount()
	 
	def getStringId(self):
		return self.string_id
		
class UserVote(db.Model):
	user = db.ReferenceProperty(User, required=True)
	link = db.ReferenceProperty(Link,required=True)
	vote_date = db.DateTimeProperty(required=True)
	
	@staticmethod
	def getUserVoteKey(link,user):
		return user.username + '_' + str(link.num_id)
	
class UserView(db.Model):
	user = db.ReferenceProperty(User, required=True)
	link = db.ReferenceProperty(Link,required=True)
	view_date = db.DateTimeProperty(required=True)
	
	@staticmethod
	def getUserViewKey(link,user):
		return user.username + '_' + str(link.num_id)
	
	
	
	
	
	 
	 