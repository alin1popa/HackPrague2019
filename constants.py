import os

ID = "iEOppYpqhHJIcwGpYdIg"
CODE = "lTK5u3Uu7uEtUr9d2FE8zA"
DEFAULT_PLACES_RADIUS = 500
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
PLACES_GRID_CSV = os.path.join(ROOT_DIR, 'clusters.csv')

POI_CATEGORIES = list({
    "car-dealer-repair",
    "snacks-fast-food",
    "electronics-shop",
    "hardware-house-garden-shop",
    "kiosk-convenience-store",
    "petrol-station",
    "atm-bank-exchange",
    "restaurant",
    "ev-charging-station",
    "theatre-music-culture",
    "shop",
    "sports-facility-venue",
    "business-services",
    "wine-and-liquor",
    "coffee-tea",
    "parking-facility",
    "mall",
    "going-out",
    "museum",
    "recreation",
    "sport-outdoor-shop",
    "hotel",
    "food-drink",
    "service",
    "business-industry",
    "eat-drink",
    "restaurant",
    "coffee-tea",
    "snacks-fast-food",
    "going-out",
    "sights-museums",
    "transport",
    "airport",
    "accommodation",
    "shopping",
    "leisure-outdoor",
    "administrative-areas-buildings",
    "natural-geographical",
    "petrol-station",
    "atm-bank-exchange",
    "toilet-rest-area",
    "hospital-health-care-facility"
})