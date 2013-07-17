from django.views.generic.simple import direct_to_template, redirect_to
from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('dashboard.views',
    url(r'gmov/(?P<object_id>\d+)/$', 'move_gadget',
        name='gadget-move'),
    url(r'gsav/(?P<object_id>\d+)/$', 'save_gadget_config',
        name='gadget-save'),
    url(r'ph/(?P<object_id>[-\w]+)/$', 'show_placeholder',
        name='placeholder'),
    url(r'w/(?P<object_id>[-\w]+)/$', 'show_widget',
        name='gadget'),
    url(r'rg/(?P<object_id>[-\w]+)/$', 'remove_gadget',
        name='gadget-remove'),
    url(r'ga/$', 'add_gadget',
        name='gadget-create'),
    url(r'sv/(?P<placeholder>[-\w]+)/$', 'update_placeholder',
        name='dashboard-placeholder-update'),
    url(r'$', 'dashboard', name='index'),
)
