import unittest

from google.appengine.ext import db

from session import *
    
class testSessions(unittest.TestCase):
    def setUp(self):
        session = createSession()
        session.save()
        self.sessionid = session.id
        
    
    def testsession(self):
        session = getSession(self.sessionid)
        session['userid']='maxl'
        session._dirty = False
        session.save()
        session2 = getSession(self.sessionid)
        if 'userid' in session2.keys():
            u = session2['userid']
