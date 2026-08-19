from typing import Dict, List, Optional
from app.services.disaster_intelligence.base import DisasterProvider
from app.services.disaster_intelligence.mock_provider import MockDisasterProvider


class DisasterProviderRegistry:
    """Registry managing available disaster intelligence feed providers."""

    def __init__(self):
        self._providers: Dict[str, DisasterProvider] = {}
        # Auto-register default deterministic mock provider
        self.register(MockDisasterProvider())

    def register(self, provider: DisasterProvider) -> None:
        self._providers[provider.provider_name] = provider

    def get_provider(self, name: str) -> Optional[DisasterProvider]:
        return self._providers.get(name)

    def list_providers(self) -> List[str]:
        return list(self._providers.keys())

    def get_active_providers(self) -> List[DisasterProvider]:
        return list(self._providers.values())


provider_registry = DisasterProviderRegistry()
