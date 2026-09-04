import random

from scraper.base_scraper import BaseScraper


class MockScraper(BaseScraper):

    def fetch_fares(
        self,
        route,
        airline,
        lead_time,
        departure_date
    ):
        base_prices = {
            "DEL-BOM": 5000,
            "DEL-BLR": 6000,
            "BOM-BLR": 4500,
            "DEL-HYD": 4800
        }

        base_price = base_prices.get(
            route,
            5000
        )

        if lead_time == 1:
            multiplier = 1.8
        elif lead_time == 7:
            multiplier = 1.2
        else:
            multiplier = 1.0

        airline_variation = {
            "IndiGo": 1.0,
            "Air India": 1.1
        }

        random_variation = random.uniform(
            0.9,
            1.1
        )

        fare = (
            base_price
            * multiplier
            * airline_variation.get(
                airline,
                1.0
            )
            * random_variation
        )

        total_fare = round(fare, 2)

        return {
            "base_fare": None,
            "taxes": None,
            "fees": None,
            "total_fare": total_fare,
            "availability": "available"
        }