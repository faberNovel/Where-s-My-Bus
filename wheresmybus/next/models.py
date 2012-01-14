import urllib
import xml.etree.cElementTree as ET
import logging

from django.db import models
from djangotoolbox.fields import EmbeddedModelField
from django_mongodb_engine.contrib import MongoDBManager
from django.contrib import admin

from settings import RTT_DATA_URL, NEXT_DEPARTURES_ENDPOINT
from secrets import API_TOKEN

NUMBER_OF_NEXT_BUSES = 2

GOOGLE_CHART_API_URL = "https://chart.googleapis.com/chart?"
ABSOLUTE_URL = "http://m.test.com/s/"

# Get an instance of a logger
logger = logging.getLogger("wheresmybus")

class Line(object):
    """docstring for StopDB"""
    def __init__(self, number, title, next_buses=[]):
        super(Line, self).__init__()
        self.number = number
        self.title = title
        self.next_buses = next_buses
    
    def get_next_bus(self):
        if not self.next_buses:
            return None
        else:
            return self.next_buses[0]

class Direction(object):
    """docstring for Direction"""
    def __init__(self, name):
        super(Direction, self).__init__()
        self.name = name

class NextBus(object):
    """docstring for NextBus"""
    def __init__(self, minutes, direction):
        super(NextBus, self).__init__()
        self.minutes = minutes
        self.direction = direction
        
    def __str__(self):
        return "<NextBus in %s seconds>" % self.seconds
        
# DATABASE MODELS

class Point(models.Model):
    lat = models.FloatField()
    lon = models.FloatField()

class Stop(models.Model):
    stop_id = models.IntegerField()
    name = models.CharField(max_length=255)
    loc = EmbeddedModelField(Point)
    
    objects = MongoDBManager()
    
    def __init__(self, *args, **kwargs):
        super(Stop, self).__init__(*args, **kwargs)
        self.lines = []
    
    def __unicode__(self):
        return "Stop #%d" % stop_id
        
    def _get_data_from_webservice(self):
        """Return data a file object from webservices.
        """
        # Calling the API
        params = urllib.urlencode({'token': API_TOKEN, 'stopcode': self.stop_id})
        url = RTT_DATA_URL + NEXT_DEPARTURES_ENDPOINT + params
        logger.info("Calling %s" % url)
        f = urllib.urlopen(url)
        
        return f
        
    def update_predictions(self):
        # It's in fact line + direction
        
        tree = ET.parse(self._get_data_from_webservice())
        
        # print ET.dump(tree)
        
        for l in tree.iter("Route"):
            # l for line
            next_buses = []
            for d in l.iter("RouteDirection"):
                # d for direction
                direction = Direction(d.attrib.get("Code", None))
                for b in list(d.iter("DepartureTime"))[:NUMBER_OF_NEXT_BUSES]:
                    # b for bus
                    next_buses.append(NextBus(b.text,
                                            direction))
                                            
            # print map(str, next_buses)
                    
            if next_buses:
                # Create and populate a line
                line_number = l.attrib.get("Code", None)
                line_title = l.attrib.get("Name", None)
                next_buses.sort(key=lambda b: int(b.minutes))
                
                self.lines.append(Line(line_number, line_title, next_buses))
            
                # logger.info("Created new busline %s, with first next bus in %s seconds." % (line_number, 
                #                 next_buses[0].seconds))

    def get_url(self):
        return ABSOLUTE_URL+str(self.stop_id)
        
    def qrcode_image_url(self):
        url_encoded = urllib.quote(self.get_url())

        # More information here: http://code.google.com/apis/chart/image/docs/gallery/qr_codes.html
        # Current options: type (QR code), size, data to encode, error correction level (high)
        options = {"cht": "qr", "chs":"350x350", "chl": url_encoded, "chld": "H|4"}

        qrcode_url = GOOGLE_CHART_API_URL + "&".join([k + "=" + v for k,v in options.iteritems()])

        return qrcode_url
        
    def get_next_bus(self):
        # find minimum
        buses_eta = []
        for l in self.lines:
            buses_eta.append(int(l.get_next_bus().seconds))
        minimum = min(buses_eta)
        
        next_bus = None
        for l in self.lines:
            if minimum == int(l.get_next_bus().seconds):
                next_bus = l.get_next_bus()
                next_bus.line_number = l.number
                break
        
        return next_bus
