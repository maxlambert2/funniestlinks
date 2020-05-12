
import unittest

from google.appengine.ext import db
from google.appengine.api import memcache
import models
from datetime import datetime

from models import *

class testCounters(unittest.TestCase):

    def setUp(self):
        counter1 = models.getCounter("TC0")
        counter1.increment()
        counter1.increment()
        counter2 = models.getDisCounter("TC12")
        

     
    def test_3(self):      

        c = models.getCounter("TC0")
        firstcount = c.getCount()
        c.increment()
        c.increment()
        c.increment()
        c.increment()
        c.increment()
        c.increment()
        c.increment()
        c.increment()
        c.put()
        seccount = c.getCount()
        diff = seccount - firstcount
        
        self.failUnless(diff ==8, 'count incorrect: '+ str(firstcount)+' ' + str(seccount))


        
if __name__ == "__main__":
    unittest.main()
    
    
    
    