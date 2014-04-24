from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns('',
    # Api
    url(r'^api/features.geojson$', views.features_geojson),
    url(r'^api/stop_routes.json$', views.stop_routes_json),
    url(r'^api/search.json', views.search),

    # We use front-end html5 location api to handle router, so all the other
    # url just need return a same static html page.
    url(r'', views.index, name='index'),
)
