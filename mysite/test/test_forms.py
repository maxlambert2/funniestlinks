import unittest

from google.appengine.ext import db
from google.appengine.api import memcache
import unittest
from datetime import datetime  
import models
from models import *
import forms

class TestForms(unittest.TestCase):
    
    def setUp(self):
        formpost = {}
        formpost['username'] = 'maxl'
        formpost['password'] = 'hellow'
        formpost['reconfirm_pass'] = 'hellow'
        formpost['email'] = 'joe@ccc.com'
        self.form = forms.CreateAccountForm(formpost,'asdf')
    
    def test_form(self):
        self.failUnless(self.form.isValid(), self.form.getErrorMsg())