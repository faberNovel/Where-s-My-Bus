import os, sys

# the parent directory of the directory which contains the 'settings.py' 
# created by 'django-admin.py startproject'.
sys.path.append('FOLDER')

os.environ['DJANGO_SETTINGS_MODULE'] = 'wheresmybus.settings'

import django.core.handlers.wsgi

application = django.core.handlers.wsgi.WSGIHandler()
