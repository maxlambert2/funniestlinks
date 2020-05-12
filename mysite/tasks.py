from django.http import HttpResponse
from django.http import HttpResponseRedirect  

import models
import settings


import rss_mod

def execute_tasks(request,freq_type):
    try:
        num_links_created = rss_mod.import_feeds(freq_type)
    except:
        raise
    else:
        response = "success:"+str(num_links_created)
    return HttpResponse(response)
     
            