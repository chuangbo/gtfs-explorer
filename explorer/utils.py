
def create_stops_geojson(objects):
    """Create a geojson representation from a list of stops.

    Params:
        objects: a iterable of stops to be included in the geojson.

    Return:
    {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [174.79218, -36.90222]
                },
                "properties": {
                    "stop_id": "100"
                    "code": "8244",
                    "name": "1 HOROTUTU RD",
                    "feed_id": 5
                }
            }
        ]
    }
    """

    geojson = {
        'type': 'FeatureCollection',
        'features': []
    }

    for obj in objects:
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": list(obj.point)
            },
            "properties": {
                "stop_id": obj.id,
                "code": obj.code,
                "name": obj.name,
            }
        }

        geojson['features'].append(feature)

    return geojson


def create_route_geojson(route, stops):
    """Create a geojson representation from a list of stops.

    Params:
        objects: a iterable of stops to be included in the geojson.

    Return:
    {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[174.79218, -36.90222], ...]
                },
                "properties": {
                    "color": "FFFFFF",
                    "route_id": 1257,
                    "text_color": "000000",
                    "short_name": "S202",
                    "long_name": "Auckland Girls Grammar To New Windsor"
                }
            },
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [174.72294, -36.894813]
                },
                "properties": {
                    "code": "8810",
                    "name": "52 Owairaka Ave",
                    "stop_id": 1249
                }
            },
            ...
        ]
    }
    """

    geojson = {
        'type': 'FeatureCollection',
        'features': []
    }

    geojson['features'].append({
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": list(route.points),
        },
        "properties": {
            "route_id": route.id,
            "short_name": route.short_name,
            "long_name": route.long_name,
            "color": route.color,
            "text_color": route.text_color,
        }
    })

    stops_geojson = create_stops_geojson(stops)
    geojson['features'].extend(stops_geojson['features'])

    return geojson
