import json
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest
from django.contrib.gis.geos import Polygon

from .models import Stop, Route
from . import utils


def index(request):
    """Do nothing but return a static html.

    I use front-end html5 location api to handle router, so all the other
    url just need return a same static html page.
    """
    return render(request, 'index.html')


def features_geojson(request):
    """View used by the map javascript to fetch two types of geojson, `stops` and
    `route`.

    This view receives a common parameter `type` via GET request and calls
    the sub function of each `type`.
    """
    type = request.GET.get('type', None)

    if type == 'stops':
        return stops_geojson(request)
    elif type == 'route':
        return route_geojson(request)
    else:
        return HttpResponseBadRequest(json.dumps({'error': 'Invalid query'}),
                                      content_type="application/json")


def stops_geojson(request):
    """View used by the map javascript to fetch geojson data only contains stops
    for each map tile.

    This view receives some parameters via GET request and returns a geojson
    response.

    Params:
        bounds: string of the form "lat_lo,lng_lo,lat_hi,lng_hi", where "lo"
            corresponds to the southwest corner of the bounding box,
            while "hi" corresponds to the northeast corner of that box.
        zoom: the map zoom level.
    """
    bounds = request.GET.get('bounds', None)
    zoom = int(request.GET.get('zoom', 13))

    if not bounds:
        return HttpResponseBadRequest(json.dumps({'error': 'Invalid query'}),
                                      content_type="application/json")

    if bounds and zoom > 14:
        x1, y1, x2, y2 = [float(i) for i in bounds.split(',')]
        polygon = Polygon(((y1, x1), (y1, x2), (y2, x2), (y2, x1), (y1, x1)))

        intersects_polygon = Stop.objects.filter(point__intersects=polygon)
    else:
        intersects_polygon = []

    geojson = utils.create_stops_geojson(intersects_polygon)
    return HttpResponse(json.dumps(geojson),
                        content_type="application/json")


def stop_routes_json(request):
    """View used by the map javascript to fetch routes data for one stop.

    This view receives one parameter via GET request and returns a normal
    json (not geojson) response. It's just for popup and not a `geo`
    object indeed, so it's no necessary to return a geojson in this api.

    Param:
        stop_code: string of the stop_code.

    Return:
        {
            "stop_id": 827,
            "code": "7179",
            "name": "69 Beach Rd",
            "point": [174.77325, -36.847187],
            "routes": [
                {
                    "color": "00F0FF",
                    "long_name": "Glen Innes To Britomart Via Grand Dr ...",
                    "short_name": "635",
                    "text_color": "000000"
                },
                ...
            ]
        }
    """
    stop_code = request.GET.get('stop_code', None)

    if not stop_code:
        return HttpResponseBadRequest(json.dumps({'error': 'Invalid query'}),
                                      content_type="application/json")

    stop = Stop.objects.filter(code=stop_code).first()

    if not stop:
        return HttpResponseBadRequest(json.dumps({'error': 'Invalid query'}),
                                      content_type="application/json")

    routes = [
        {
            "short_name": route.short_name,
            "long_name": route.long_name,
            "color": route.color,
            "text_color": route.text_color,
        }
        for route in stop.routes.all()
    ]

    data = {
        "stop_id": stop.id,
        "code": stop.code,
        "name": stop.name,
        "point": list(stop.point),
        "routes": routes,
    }

    return HttpResponse(json.dumps(data),
                        content_type="application/json")


def route_geojson(request):
    """View used by the map javascript to fetch geojson data contains
    one route and stops on the route.

    This view receives some parameters via GET request and returns a geojson
    response.

    Params:
        route_short_name: short name of a route, like 974, AIR, etc.

    Return:
        geojson contains a route and several stops.
    """
    short_name = request.GET.get('route_short_name', None)

    if not short_name:
        return HttpResponseBadRequest(json.dumps({'error': 'Invalid query'}),
                                      content_type="application/json")

    route = Route.objects.get(short_name=short_name)
    stops = route.stops.all()

    geojson = utils.create_route_geojson(route, stops)
    return HttpResponse(json.dumps(geojson),
                        content_type="application/json")
