from django.conf.urls.defaults import patterns, include, url

from django.conf import settings

STOP_ID_REGEX = r"\b1\d{4,5}\b"

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'wheresmybus.views.home', name='home'),
    # url(r'^wheresmybus/', include('wheresmybus.foo.urls')),

    url(r'^api/location/$', "wheresmybus.next.views.api_for_location"),
    url(r'^api/stop_id/(' + STOP_ID_REGEX + r')$', "wheresmybus.next.views.api_for_stop_id"),
    url(r'^sms$', "wheresmybus.next.views.sms")
)

if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^debug/$', 'wheresmybus.next.views.debug'),
    )
