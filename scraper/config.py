ROUTES = [
    "DEL-BOM",
    "DEL-BLR",
    "BOM-BLR",
    "DEL-HYD"
]

AIRLINES = [
    "IndiGo",
    "Air India"
]

LEAD_TIMES = [1, 7, 15, 30, 45]

ROUTE_AIRPORTS = {
    "DEL-BOM": {
        "origin": "DEL",
        "destination": "BOM"
    },
    "DEL-BLR": {
        "origin": "DEL",
        "destination": "BLR"
    },
    "BOM-BLR": {
        "origin": "BOM",
        "destination": "BLR"
    },
    "DEL-HYD": {
        "origin": "DEL",
        "destination": "HYD"
    }
}

DATA_FILE = "data/raw_fares.csv"

ACTIVE_SOURCE = "mock"