from abc import ABC, abstractmethod
from typing import List
from app.services.disaster_intelligence.normalization import NormalizedDisasterEvent


class DisasterProvider(ABC):
    """Abstract interface for disaster event feed providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Unique identifier for this disaster intelligence provider."""
        pass

    @abstractmethod
    async def fetch_events(self) -> List[NormalizedDisasterEvent]:
        """Asynchronously fetch, parse, and normalize disaster events from feed source."""
        pass
