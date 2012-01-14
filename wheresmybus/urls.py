from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin

from wheresmybus.next.urls import STOP_ID_REGEX
from wheresmybus.settings import ENV

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'wheresmybus.next.views.home'),
    url(r'^s/(' + STOP_ID_REGEX + r')$', 'wheresmybus.next.views.for_stop_id'),
    url(r'^next/', include('wheresmybus.next.urls')),
    url(r'^admin/', include(admin.site.urls)),
)

# Only for the dev version (static files)
if ENV == "testing":
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()
