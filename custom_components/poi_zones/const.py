"""Constants for POI Zones integration."""
from typing import Final

DOMAIN: Final = "poi_zones"

# Configuration keys
CONF_CITY: Final = "city"
CONF_POI_TYPE: Final = "poi_type"
CONF_SEARCH_RADIUS: Final = "search_radius"
CONF_ZONE_RADIUS: Final = "zone_radius"

# Defaults
DEFAULT_SEARCH_RADIUS: Final = 25  # km from city center
DEFAULT_ZONE_RADIUS: Final = 150  # meters for each zone

# API
OVERPASS_URL: Final = "https://overpass-api.de/api/interpreter"
NOMINATIM_URL: Final = "https://nominatim.openstreetmap.org/search"

# Update interval (POIs don't move often, check weekly)
UPDATE_INTERVAL: Final = 7 * 24 * 60 * 60  # 7 days in seconds

# POI Types - individual types only
POI_TYPES: Final = {
    "hospital": {
        "name": "Hospitals",
        "icon": "mdi:hospital-building",
        "radius": 200,
        "filters": [
            {"amenity": "hospital"},
            {"healthcare": "hospital"},
        ],
    },
    "clinic": {
        "name": "Clinics",
        "icon": "mdi:medical-bag",
        "radius": 150,
        "filters": [
            {"amenity": "clinic"},
            {"healthcare": "clinic"},
        ],
    },
    "urgent_care": {
        "name": "Urgent Care",
        "icon": "mdi:ambulance",
        "radius": 150,
        "filters": [
            {"healthcare": "urgent_care"},
            {"amenity": "clinic", "urgent_care": "yes"},
            {"amenity": "clinic", "healthcare:speciality": "urgent_care"},
        ],
    },
    "pharmacy": {
        "name": "Pharmacies",
        "icon": "mdi:pharmacy",
        "radius": 100,
        "filters": [
            {"amenity": "pharmacy"},
            {"healthcare": "pharmacy"},
        ],
    },
    "doctor": {
        "name": "Doctors Offices",
        "icon": "mdi:stethoscope",
        "radius": 100,
        "filters": [
            {"amenity": "doctors"},
            {"healthcare": "doctor"},
        ],
    },
    "school": {
        "name": "Schools (K-12)",
        "icon": "mdi:school",
        "radius": 200,
        "filters": [
            {"amenity": "school"},
        ],
    },
    "university": {
        "name": "Universities & Colleges",
        "icon": "mdi:school-outline",
        "radius": 300,
        "filters": [
            {"amenity": "university"},
            {"amenity": "college"},
        ],
    },
    "childcare": {
        "name": "Childcare & Daycares",
        "icon": "mdi:baby-carriage",
        "radius": 100,
        "filters": [
            {"amenity": "childcare"},
            {"amenity": "kindergarten"},
        ],
    },
    "grocery": {
        "name": "Grocery Stores",
        "icon": "mdi:cart",
        "radius": 150,
        "filters": [
            {"shop": "supermarket"},
            {"shop": "grocery"},
        ],
    },
    "gas_station": {
        "name": "Gas Stations",
        "icon": "mdi:gas-station",
        "radius": 100,
        "filters": [
            {"amenity": "fuel"},
        ],
    },
    "gym": {
        "name": "Gyms & Fitness Centers",
        "icon": "mdi:dumbbell",
        "radius": 150,
        "filters": [
            {"leisure": "fitness_centre"},
            {"leisure": "sports_centre"},
        ],
    },
    "restaurant": {
        "name": "Restaurants",
        "icon": "mdi:silverware-fork-knife",
        "radius": 75,
        "filters": [
            {"amenity": "restaurant"},
        ],
    },
    "fast_food": {
        "name": "Fast Food",
        "icon": "mdi:hamburger",
        "radius": 75,
        "filters": [
            {"amenity": "fast_food"},
        ],
    },
    "cafe": {
        "name": "Cafes & Coffee Shops",
        "icon": "mdi:coffee",
        "radius": 75,
        "filters": [
            {"amenity": "cafe"},
        ],
    },
    "bar": {
        "name": "Bars & Pubs",
        "icon": "mdi:glass-mug-variant",
        "radius": 75,
        "filters": [
            {"amenity": "bar"},
            {"amenity": "pub"},
        ],
    },
    "bank": {
        "name": "Banks",
        "icon": "mdi:bank",
        "radius": 100,
        "filters": [
            {"amenity": "bank"},
        ],
    },
    "police": {
        "name": "Police Stations",
        "icon": "mdi:police-badge",
        "radius": 150,
        "filters": [
            {"amenity": "police"},
        ],
    },
    "fire_station": {
        "name": "Fire Stations",
        "icon": "mdi:fire-truck",
        "radius": 150,
        "filters": [
            {"amenity": "fire_station"},
        ],
    },
    "library": {
        "name": "Libraries",
        "icon": "mdi:library",
        "radius": 150,
        "filters": [
            {"amenity": "library"},
        ],
    },
    "post_office": {
        "name": "Post Offices",
        "icon": "mdi:mailbox",
        "radius": 100,
        "filters": [
            {"amenity": "post_office"},
        ],
    },
    "place_of_worship": {
        "name": "Places of Worship",
        "icon": "mdi:church",
        "radius": 150,
        "filters": [
            {"amenity": "place_of_worship"},
        ],
    },
    "park": {
        "name": "Parks",
        "icon": "mdi:tree",
        "radius": 200,
        "filters": [
            {"leisure": "park"},
        ],
    },
    "airport": {
        "name": "Airports",
        "icon": "mdi:airplane",
        "radius": 500,
        "filters": [
            {"aeroway": "aerodrome"},
        ],
    },
    "train_station": {
        "name": "Train Stations",
        "icon": "mdi:train",
        "radius": 200,
        "filters": [
            {"railway": "station"},
        ],
    },
    "ev_charging": {
        "name": "EV Charging Stations",
        "icon": "mdi:ev-station",
        "radius": 100,
        "filters": [
            {"amenity": "charging_station"},
        ],
    },
    "car_wash": {
        "name": "Car Washes",
        "icon": "mdi:car-wash",
        "radius": 100,
        "filters": [
            {"amenity": "car_wash"},
        ],
    },
    "car_repair": {
        "name": "Auto Repair Shops",
        "icon": "mdi:car-wrench",
        "radius": 100,
        "filters": [
            {"shop": "car_repair"},
        ],
    },
    "hotel": {
        "name": "Hotels",
        "icon": "mdi:bed",
        "radius": 150,
        "filters": [
            {"tourism": "hotel"},
            {"tourism": "motel"},
        ],
    },
    "cinema": {
        "name": "Movie Theaters",
        "icon": "mdi:movie-open",
        "radius": 150,
        "filters": [
            {"amenity": "cinema"},
        ],
    },
    "veterinary": {
        "name": "Veterinary Clinics",
        "icon": "mdi:paw",
        "radius": 100,
        "filters": [
            {"amenity": "veterinary"},
        ],
    },
    "dentist": {
        "name": "Dentists",
        "icon": "mdi:tooth",
        "radius": 100,
        "filters": [
            {"amenity": "dentist"},
            {"healthcare": "dentist"},
        ],
    },
    "nursing_home": {
        "name": "Nursing Homes",
        "icon": "mdi:home-heart",
        "radius": 150,
        "filters": [
            {"amenity": "nursing_home"},
            {"healthcare": "nursing_home"},
        ],
    },
}

# For easy dropdown selection
POI_TYPE_OPTIONS: Final = {k: v["name"] for k, v in POI_TYPES.items()}
