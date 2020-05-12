
import unittest

from google.appengine.ext import db
from google.appengine.api import memcache
import unittest
from datetime import datetime  
import models
from models import *
    
class testUsers(unittest.TestCase):
    def setUp(self):
        self.passw = 'hello55'
        self.usern = 'john_testy1'
        self.email = 'johnt1@test.com'
        testurl = 'test.com'
        self.user = createUser(self.usern,self.passw,self.email)
    
    def test_1_create_user(self):
        isvalid = models.authenticate(self.usern,self.passw)
        self.failUnless(isvalid.username == self.user.name, 'user save did not work')
      
    def test_2_create_badusername(self): 
        self.assertRaises(InvalidUsernameError, models.createUser,username = 'sdf&sss', email = 'john2@test.com', password = 'ddddddd')
                       
    def test_3_create_bademail(self): 
        try:
            models.createUser(username = 'steven', email = 'john@@test.com', password = 'ddddddd')
            self.fail("exception not raised")
        except(InvalidEmailError):
            pass
        
    def test_4_create_duplicate_username(self): 
        try:
            models.createUser(username = self.usern,  password = 'ddddddd')
            self.fail("exception not raised")
        except(UsernameUsedError):
            pass

    def test_5_create_duplicate_email(self): 
        try:
            models.createUser(username = 'john3', email = 'johnt1@test.com', password = 'ddddddd')
            self.fail("exception not raised")
        except(EmailUsedError):
            pass
    
    def test_6_create_toolong_username(self): 
        self.assertRaises(InvalidUsernameError, models.createUser,username = 'john3looooasdfooooooooong', email = 'john6@test.com', password = 'ddddddd')

    def test_7_create_toolong_pass(self): 
        self.assertRaises(InvalidPasswordError, models.createUser,username = 'john3log', email = 'john6@test.com', password = 'dddddddaaaaaaaaaaaaaaasdfaaaa')
        
        