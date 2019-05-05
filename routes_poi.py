import csv
import json

import math
import requests as req
from math import sqrt

from constants import ID, CODE, DEFAULT_PLACES_RADIUS, POI_CATEGORIES, \
    PLACES_GRID_CSV
from util import init_logging

LOG = init_logging(__name__)

def _get(url):
    param_connector = "&" if "?" in url else "?"
    creds = "{}app_id={}&app_code={}".format(param_connector, ID, CODE)
    url = url + creds
    LOG.debug(url)
    r = req.get(url)
    r.raise_for_status()
    return r.content


def _get_flow(params):
    url = 'https://traffic.api.here.com/traffic/6.2/flow{}'.format(params)
    return _get(url)


def _get_places(params):
    url = 'https://places.cit.api.here.com/places/v1/browse?{}'.format(params)
    return _get(url)


def _get_route(params):
    url = ('https://route.api.here.com/routing/7.2/calculateroute.json'
           '?mode=fastest;pedestrian;traffic:disabled{}'.format(params))
    return _get(url)


def pp(jsn):
    if isinstance(jsn, str) or isinstance(jsn, bytes):
        print(json.dumps(json.loads(jsn), indent=2, sort_keys=True))
    else:
        print(json.dumps(jsn, indent=2, sort_keys=True))


class PlacesCell:

    def __init__(self, x, y, city, radius=DEFAULT_PLACES_RADIUS):
        self.scraper=None
        self.x = x
        self.y = y
        self.city = city
        self.radius = radius
        self.score = 1
        self.places = []

    def __repr__(self):
        return "Cell ({x}, {y})".format(x=self.x, y=self.y)

    def load_places(self):
        # Returns list of places, max 100
        jsn = _get_places('in={x},{y};r={r}&size=100'
                          .format(x=self.x, y=self.y, r=self.radius))
        places = json.loads(jsn)['results']['items']
        LOG.debug("Got {} results.".format(len(places)))
        self.places = places

    def calculate_score(self):
        # max score can be 10 * number of places
        if not self.places:
            self.load_places()
        raw_score = len(self.places)
        cat_score = {place: 0 for place in POI_CATEGORIES}
        for index, place in enumerate(self.places):
            cat = place['category']['id']
            if cat in cat_score:
                cat_score[cat] += 1
            else:
                continue
        LOG.debug("Raw score for ({x}, {y}) cell: {score}"
                  .format(x=self.x, y=self.y, score=raw_score))
        LOG.debug("Category score for ({x}, {y}) cell: {score}"
                  .format(x=self.x, y=self.y, score=cat_score))
        self.score = raw_score

class Route:

    def __init__(self, points_list):
        self.points_list = points_list
        self.score = None
        self.grid = None

    def __repr__(self):
        return "Points: {}\nScore: {}\n".format(self.points_list, self.score)

class PlacesGrid:

    def __init__(self):
        """Grid construct

        Should be made of 500x500m tiles. total 40 * 40 = 1600 tiles => 20x20km
        Each tile should have its corners coordinates + center
        """
        self.size = 0
        self.grid = None
        self.init_grid()

    def init_grid(self):
        with open(PLACES_GRID_CSV, 'r') as csv_file:
            data = csv.reader(csv_file, delimiter=',')
            data = list(data)
        size = int(sqrt(len(data)))

        grid = [[None for _ in range(size)] for _ in range(size)]
        for i in range(size):
            for j in range(size):
                arr_index = i * size + j
                x = data[arr_index][2]
                y = data[arr_index][1]
                grid[i][j] = PlacesCell(x=x, y=y, city='brno', radius=500)
                grid[i][j].calculate_score()
        self.size = size
        self.grid = grid
        self.all_routes_scores = [[0 for _ in range(self.size)]
                                  for _ in range(self.size)]

    def get_routes(self):
        routes = [None for _ in range(self.size * 2)]
        for i in range(self.size):
            cell_a = self.grid[i][0]
            cell_b = self.grid[i][self.size - 1]
            routes[i] = self.get_route(cell_a, cell_b)
            cell_a = self.grid[0][i]
            cell_b = self.grid[self.size - 1][i]
            routes[self.size + i] = self.get_route(cell_a, cell_b)
        self.routes = routes
        for r in self.routes:
            LOG.debug(r)
        self.save_routes()
        self.save_route_score_grid()

    def save_routes(self):
        routes = self.routes
        list_routes = []
        for route in routes:
            dict_route = {
                'points': route.points_list,
                'score': route.score
            }
            list_routes.append(dict_route)
        with open('output.py', 'w') as output:
            output.write(json.dumps(list_routes))

    def save_route_score_grid(self):
        with open('route_scores.py', 'w') as output_scores:
            output_scores.write(json.dumps(self.all_routes_scores))

    def get_route(self, cell_a, cell_b):
        start = 'geo!{x},{y}'.format(x=cell_a.x, y=cell_a.y)
        end = 'geo!{x},{y}'.format(x=cell_b.x, y=cell_b.y)
        params = '&waypoint0={}&waypoint1={}'.format(start, end)
        route = _get_route(params=params)
        route = json.loads(route)['response']['route'][0]['leg'][0]['maneuver']
        route_list = [maneuver['position'] for maneuver in route]
        route_list = [(point['latitude'], point['longitude'])
                      for point in route_list]
        LOG.debug("Route from Cell ({xa}, {ya}) to Cell ({xb}, {yb}): {route}"
                  .format(xa=cell_a.x, ya=cell_a.y, xb=cell_b.x, yb=cell_b.y,
                          route=route_list))
        route = Route(route_list)
        route = self.calculate_route_score(route)
        return route

    def calculate_route_score(self, route):
        # Calcualte score checking what cells does this route hit
        grid_route = self.addAllPoints(route.points_list)
        score = 0
        for i in range(self.size):
            for j in range(self.size):
                if grid_route[i][j]:
                    score += self.grid[i][j].score
        route.score = score
        route.grid = grid_route

        for i in range(self.size):
            for j in range(self.size):
                if grid_route[i][j]:
                    self.all_routes_scores[i][j] += route.score
        return route

    def addAllPoints(self, points):
        grid_route = [[0 for _ in range(self.size)] for _ in range(self.size)]
        for point in points:
            i, j = self.pointToCell(point)
            try:
                grid_route[i][j] = 1
            except:
                continue

        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i + 1]

            x1, y1 = self.pointToCell(p1)
            x2, y2 = self.pointToCell(p2)

            steps = max(x2 - x1, y2 - y1) * 20

            tx, ty = x1, y1
            for j in range(steps):
                tx = tx + (x2 - x1) / steps
                ty = ty + (y2 - y1) / steps
                try:
                    grid_route[int(tx)][int(ty)] = 1
                except:
                    continue
        return grid_route

    def pointToCell(self, point):
        # point = tuple
        # returns i, j indices in grid
        lat, lng = point
        GRID_RESOLUTION = 10 ** 4  # higher res means smaller cells
        CLUSTERED_DIAMETER = 100  # ZxZ clusters
        MIN_LAT_IN_DATASET = 49.112730179544
        MIN_LNG_IN_DATASET = 16.4078522359116
        GRID_CORNER_PADDING = 100
        CORNER_LAT_POS = math.floor(
            MIN_LAT_IN_DATASET * GRID_RESOLUTION) - GRID_CORNER_PADDING
        CORNER_LNG_POS = math.floor(
            MIN_LNG_IN_DATASET * GRID_RESOLUTION) - GRID_CORNER_PADDING
        GRID_SIZE = 3500
        NOCLUSTERS = int(GRID_SIZE / CLUSTERED_DIAMETER)
        PERCENT_ITEMS = 0.25
        i = int(math.floor((math.floor(
            lat * GRID_RESOLUTION) - CORNER_LAT_POS) / CLUSTERED_DIAMETER))
        j = int(math.floor((math.floor(
            lng * GRID_RESOLUTION) - CORNER_LNG_POS) / CLUSTERED_DIAMETER))
        return i, j



def main():
    grid = PlacesGrid()
    routes = grid.get_routes()

if __name__ == '__main__':
    main()