from scraper.indigo_scraper import IndigoScraper


scraper = IndigoScraper(headless=False)

result = scraper.fetch_fares(
    route="DEL-BOM",
    airline="IndiGo",
    lead_time=7,
    departure_date="2026-09-10"
)

print(result)