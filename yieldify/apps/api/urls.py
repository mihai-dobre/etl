from django.conf.urls import url

from .views import BrowserView, OpSysView, DeviceView

urlpatterns = [
    url(r'^browser/$', BrowserView.as_view(), name='browser-list'),
    url(r'^device/$', DeviceView.as_view(), name='device-list'),
    url(r'^os/$', OpSysView.as_view(), name='os-list'),
]