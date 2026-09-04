from playwright.sync_api import sync_playwright

from scraper.base_scraper import BaseScraper
from scraper.config import ROUTE_AIRPORTS


class IndigoScraper(BaseScraper):

    def __init__(self, headless=True):
        self.headless = headless
        self.url = "https://www.goindigo.in/flight-booking.html"

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
            f"Searching IndiGo: "
            f"{origin} -> {destination} "
            f"on {departure_date}"
        )

        with sync_playwright() as p:

            browser = p.chromium.launch(
                headless=self.headless
            )

            page = browser.new_page()

            try:

                page.goto(
                    self.url,
                    wait_until="domcontentloaded",
                    timeout=60000
                )

                page.wait_for_timeout(5000)

                # Handle cookie banner
                try:
                    page.get_by_text(
                        "Accept Essential Only",
                        exact=True
                    ).click(timeout=3000)
                except Exception:
                    pass

                page.wait_for_timeout(2000)

                inputs = page.locator(
                    'input[placeholder="Start typing.."]'
                )

                print(
                    f"Booking fields found: {inputs.count()}"
                )

                # -------------------------
                # TEST ORIGIN
                # -------------------------

                print(
                    f"\nEntering origin: {origin}"
                )

                origin_input = inputs.nth(0)

                origin_input.click()

                origin_input.fill(origin)

                page.wait_for_timeout(2000)

                print("\n--- ORIGIN SUGGESTIONS ---")

                body_text = page.locator(
                    "body"
                ).inner_text()

                lines = body_text.splitlines()

                for line in lines:
                    line = line.strip()

                    if line:
                        print(line)

                raise RuntimeError(
                    "Origin airport inspection completed."
                )

            finally:

                browser.close()