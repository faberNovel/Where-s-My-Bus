from django.conf.urls.defaults import patterns, include, url

from django.conf import settings

STOP_ID_REGEX = r"\b1\d{4,5}\b"

urlpatterns = patterns('',
    url(r'^api/location/$', "wheresmybus.next.views.api_for_location"),
    url(r'^api/stop_id/(' + STOP_ID_REGEX + r')$', "wheresmybus.next.views.api_for_stop_id"),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^debug/$', 'wheresmybus.next.views.debug'),
    )
