# encoding: utf-8

import logging
import urllib2

from lxml import etree 

from django.contrib import admin
from django.shortcuts import render_to_response
from django.conf.urls.defaults import patterns
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from wheresmybus.next.models import Point, Stop

# Get an instance of a logger
logger = logging.getLogger("wheresmybus")

NUMBER_OF_QR_PER_PAGE = 100

class StopAdmin(admin.ModelAdmin):
    list_display = ("stop_id", "name")
        
    def generate_qrcodes(self, request):
        c = {"page_range": None}
        stops_list = Stop.objects.all()
        paginator = Paginator(stops_list, NUMBER_OF_QR_PER_PAGE)

        page = request.GET.get('page')
        try:
            stops = paginator.page(page)
        except (PageNotAnInteger, TypeError):
            # If page is not an integer, deliver first page.
            stops = None
            c["page_range"] = paginator.page_range
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            stops = paginator.page(paginator.num_pages)
            
        c["stops"] = stops
        
        return render_to_response('admin/next/generate_qrcode.html', c)
    
    def get_urls(self):
        urls = super(StopAdmin, self).get_urls()
        my_urls = patterns('',
            (r'^generate_qrcodes/$', self.admin_site.admin_view(self.generate_qrcodes)),
        )
        return my_urls + urls

admin.site.register(Point)
admin.site.register(Stop, StopAdmin)
