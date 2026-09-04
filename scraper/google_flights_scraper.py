from datetime import datetime
from pathlib import Path

from fast_flights import FlightQuery, create_query, get_flights
from fast_flights.exceptions import FlightsNotFound


DEBUG_DIR = Path("data/debug")

# A single Google Flights query returns every airline operating a route,
# not just one. This maps the airline names we track (scraper/config.py
# AIRLINES) to the substring Google Flights uses in `flight.airlines`.
# If a tracked airline never shows up in results, this is the first
# place to check — dump a raw result's `.airlines` list and compare.
AIRLINE_NAME_MAP = {
    "IndiGo": "indigo",
    "Air India": "air india",
    "SpiceJet": "spicejet",
    "Akasa Air": "akasa",
}


def fetch_route_fares(origin, destination, departure_date, debug=True):
    """
    Runs ONE Google Flights query for this route/date and returns the
    cheapest fare found per tracked airline, e.g.:

        {"IndiGo": 5985.0, "Air India": 7210.0, "SpiceJet": 6100.0}

    An airline with no matching flights on this route/date is simply
    absent from the dict — callers should treat a missing key as
    "no data", not as an error.
    """
    if debug:
        DEBUG_DIR.mkdir(parents=True, exist_ok=True)

    query = create_query(
        flights=[
            FlightQuery(
                date=departure_date,
                from_airport=origin,
                to_airport=destination,
            )
        ],
        trip="one-way",
        seat="economy",
        currency="INR",
        language="en-US",
    )

    try:
        results = get_flights(query)
    except FlightsNotFound:
        return {}
    except Exception as error:
        if debug:
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            (
                DEBUG_DIR
                / f"gf_fetch_failed_{origin}_{destination}_{stamp}.txt"
            ).write_text(
                f"{type(error).__name__}: {error}",
                encoding="utf-8"
            )
        raise RuntimeError(
            f"Google Flights query failed for "
            f"{origin}->{destination} on {departure_date}: {error}"
        )

    cheapest_by_airline = {}

    for flight in results:
        for raw_name in flight.airlines:
            for tracked_name, needle in AIRLINE_NAME_MAP.items():
                if needle in raw_name.lower():
                    current_best = cheapest_by_airline.get(tracked_name)

                    if current_best is None or flight.price < current_best:
                        cheapest_by_airline[tracked_name] = flight.price

    return cheapest_by_airline