from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns('',
    # Api
    url(r'^features.geojson$', views.features_geojson, name='features_geojson'),
    url(r'^stop_routes.json$', views.stop_routes_json, name='stop_routes_json'),

    # We use front-end html5 location api to handle router, so all the other
    # url just need return a same static html page.
    url(r'', views.index, name='index'),
)
