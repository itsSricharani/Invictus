from datetime import datetime
from pathlib import Path

from fast_flights import FlightQuery, create_query, get_flights
from fast_flights.exceptions import FlightsNotFound

from scraper.base_scraper import BaseScraper
from scraper.config import ROUTE_AIRPORTS


DEBUG_DIR = Path("data/debug")

# fast-flights matches on the airline name string Google Flights itself
# displays. IndiGo is shown as "Indigo" (capital I, lowercase rest) on
# Google's results — this is the one thing most likely to need tweaking
# if matches ever come back empty; check a raw result's `.airlines` list
# (logged below) if that happens.
GOOGLE_FLIGHTS_AIRLINE_NAME = "Indigo"


class IndigoScraper(BaseScraper):
    """
    Despite the name, this no longer drives a browser against
    goindigo.in directly. It queries Google Flights (via the
    `fast-flights` library) for the route/date, then filters the
    results down to IndiGo-operated flights and returns the cheapest
    one. This sidesteps IndiGo's own anti-bot protections entirely,
    at the cost of the fare being "what Google Flights shows for
    IndiGo" rather than "what goindigo.in shows" — for a price *index*
    (relative movement over time) rather than exact absolute fares,
    that's a perfectly reasonable trade-off.
    """

    def __init__(self, headless=True, debug=True):
        # headless is accepted for backwards compatibility with existing
        # call sites (collector.py, test_indigo_scraper.py) but unused —
        # there's no browser here anymore.
        self.headless = headless
        self.debug = debug

        if self.debug:
            DEBUG_DIR.mkdir(parents=True, exist_ok=True)

    def _dump_debug(self, tag, content):
        if not self.debug:
            return

        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        try:
            (DEBUG_DIR / f"{tag}_{stamp}.txt").write_text(
                content,
                encoding="utf-8"
            )
        except Exception:
            pass

    def fetch_fares(
        self,
        route,
        airline,
        lead_time,
        departure_date
    ):
        if airline != "IndiGo":
            raise ValueError(
                "IndigoScraper only supports IndiGo."
            )

        airports = ROUTE_AIRPORTS[route]
        origin = airports["origin"]
        destination = airports["destination"]

        print(
            f"Searching Google Flights for IndiGo: "
            f"{origin} -> {destination} on {departure_date}"
        )

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
            raise RuntimeError(
                f"No flights found at all for {origin}->{destination} "
                f"on {departure_date} (Google Flights returned nothing "
                f"for this route/date, not just for IndiGo)."
            )
        except Exception as error:
            self._dump_debug(
                f"fetch_failed_{origin}_{destination}",
                f"{type(error).__name__}: {error}"
            )
            raise RuntimeError(
                f"Google Flights query failed for "
                f"{origin}->{destination} on {departure_date}: {error}"
            )

        indigo_flights = [
            flight for flight in results
            if any(
                GOOGLE_FLIGHTS_AIRLINE_NAME.lower() in a.lower()
                for a in flight.airlines
            )
        ]

        if not indigo_flights:
            all_airlines_seen = sorted(
                {a for flight in results for a in flight.airlines}
            )

            self._dump_debug(
                f"no_indigo_match_{origin}_{destination}",
                "Airlines seen in results: "
                + ", ".join(all_airlines_seen)
            )

            raise RuntimeError(
                f"Flights were found for {origin}->{destination} on "
                f"{departure_date}, but none matched airline name "
                f"'{GOOGLE_FLIGHTS_AIRLINE_NAME}'. Airlines actually "
                f"seen: {all_airlines_seen}. If 'IndiGo' appears there "
                f"under a different casing/spelling, update "
                f"GOOGLE_FLIGHTS_AIRLINE_NAME at the top of this file."
            )

        cheapest = min(indigo_flights, key=lambda f: f.price)

        print(
            f"Found {len(indigo_flights)} IndiGo option(s), "
            f"cheapest: Rs.{cheapest.price}"
        )

        return {
            "base_fare": None,
            "taxes": None,
            "fees": None,
            "total_fare": float(cheapest.price),
            "availability": "available"
        }