from abc import ABC, abstractmethod
class BaseScraper(ABC):

    @abstractmethod
    def fetch_fares(
        self,
        route,
        airline,
        lead_time,
        departure_date
    ):
        pass