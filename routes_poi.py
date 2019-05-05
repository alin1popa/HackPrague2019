import json

import requests as req

from constants import ID, CODE, DEFAULT_PLACES_RADIUS, POI_CATEGORIES
from sln import GScraper
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
        self.score = 0
        self.places = []

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
        self.score = cat_score

class PlacesGrid:

    def __init__(self, center_x, center_y):
        """Grid construct

        Should be made of 500x500m tiles. total 40 * 40 = 1600 tiles => 20x20km
        Each tile should have its corners coordinates + center
        """
        pass

    def get_route(self, cell_a, cell_b):
        start = 'geo!{x},{y}'.format(x=cell_a.x, y=cell_a.y)
        end = 'geo!{x},{y}'.format(x=cell_b.x, y=cell_b.y)
        params = '&waypoint0={}&waypoint1={}'.format(start, end)
        route = _get_route(params=params)
        route = json.loads(route)['response']['route'][0]['leg'][0]['maneuver']
        route_list = [maneuver['position'] for maneuver in route]
        LOG.debug("Route from Cell ({xa}, {ya}) to Cell ({xb}, {yb}): {route}"
                  .format(xa=cell_a.x, ya=cell_a.y, xb=cell_b.x, yb=cell_b.y,
                          route=route_list))
        return route_list

def main():
    x = 44.492419
    y = 26.125721

    cell = PlacesCell(x, y, 'bucuresti')
    cell.calculate_score()

    x = 44.434157
    y = 26.107667
    cell_b = PlacesCell(x, y, 'bucuresti')
    grid = PlacesGrid(None, None)
    grid.get_route(cell_a=cell, cell_b=cell_b)


if __name__ == '__main__':
    main()