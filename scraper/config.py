ROUTES = [
    "DEL-BOM",
    "DEL-BLR",
    "BOM-BLR",
    "DEL-HYD"
]

AIRLINES = [
    "IndiGo",
    "Air India",
    "SpiceJet",
    "Akasa Air"
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

# "mock" -> synthetic data (MockScraper)
# "google_flights" -> real data via fast-flights, filtered to AIRLINES above
ACTIVE_SOURCE = "mock"