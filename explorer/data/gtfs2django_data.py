#!/usr/bin/env python

import json
import sys
import csv
from os import path
from collections import defaultdict


class Parser:
    """GTFS is a little bit complicated, routes, trips, calendar, etc.
    This tools do not provide a tools with full feature, it's just a
    demo I wrote walking through GTFS. So this method just take the
    FIRST route of routes with the same short name, and no calendar
    information at all."""

    _models = []

    def __init__(self, base_dir):
        self.base_dir = base_dir

    def _parse_stops(self):
        """export stop model to self.models
        var stop_id_pk: for relations between routes with stops"""

        self._stop_id_pk = {}

        with open(path.join(self.base_dir, 'stops.txt')) as f:
            reader = csv.reader(f)
            next(reader)

            for i, (stop_id, code, name, lat, lon) in enumerate(reader, 1):
                self._stop_id_pk[stop_id] = i

                # stop model finished
                self._models.append(
                    {'model': 'explorer.stop', 'pk': i,
                     'fields': {'code': code, 'name': name,
                                'point': "POINT(%s %s)" % (lon, lat)}}
                )

    def __parse_shapes(self):
        """generate wkt format for shapes for trips"""
        # 1. read shapes
        shapes = defaultdict(list)
        with open(path.join(self.base_dir, 'shapes.txt')) as f:
            reader = csv.reader(f)
            next(reader)
            for shape_id, lat, lon, _ in reader:
                shapes[shape_id].append(' '.join([lon, lat]))

        for shape_id, v in shapes.items():
            shapes[shape_id] = "LINESTRING (%s)" % ', '.join(v)

        # 2. read shapes of trips
        route_shapes = {}
        # trip_route_id: save route <=> trip for read stops for route
        trip_route_id = {}
        with open(path.join(self.base_dir, 'trips.txt')) as f:
            reader = csv.reader(f)
            next(reader)
            for route_id, _, trip_id, _, _, shape_id in reader:
                if route_id in route_shapes:
                    continue
                route_shapes[route_id] = shapes[shape_id]
                trip_route_id[trip_id] = route_id

        self._route_shapes = route_shapes
        self._trip_route_id = trip_route_id

    def __parse_route_stops(self):
        """read stops of each route"""

        route_stops = defaultdict(list)

        with open(path.join(self.base_dir, 'stop_times.txt')) as f:
            reader = csv.reader(f)
            next(reader)
            for trip_id, _, _, stop_id, _, _, _ in reader:
                if trip_id not in self._trip_route_id:
                    continue
                route_id = self._trip_route_id[trip_id]
                stop_pk = self._stop_id_pk[stop_id]
                route_stops[route_id].append(stop_pk)

        self._route_stops = route_stops

    def _parse_routes(self):
        """export route to self._models"""
        self.__parse_shapes()
        self.__parse_route_stops()

        short_names = set()
        with open(path.join(self.base_dir, 'routes.txt')) as f:
            reader = csv.reader(f)
            next(reader)
            for i, (route_id, _, short_name, long_name, _, color,
                    text_color) in enumerate(reader, 1):
                # just first route of routes with the same short name
                if short_name in short_names:
                    continue
                short_names.add(short_name)
                self._models.append(
                    {'model': 'explorer.route', 'pk': i,
                     'fields': {'short_name': short_name,
                                'long_name': long_name,
                                'color': color, 'text_color': text_color,
                                'points': self._route_shapes[route_id],
                                'stops': self._route_stops[route_id]}}
                )

    def parse(self):
        """Parse all model and dump. Cost more memory but less coupling."""
        self._parse_stops()
        self._parse_routes()
        return json.dumps(self._models, indent=2)


if __name__ == '__main__':
    if len(sys.argv) > 1 and path.isdir(sys.argv[1]):
        print(Parser(sys.argv[1]).parse())
    else:
        print("""Usage: %s GTFS_DIR

Load GTFS data into django's init data type.""" % sys.argv[0])
