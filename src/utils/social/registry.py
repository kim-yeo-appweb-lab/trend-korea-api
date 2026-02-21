from src.utils.social.base import SocialAuthProvider


class SocialProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, SocialAuthProvider] = {}

    def register(self, provider: SocialAuthProvider) -> None:
        self._providers[provider.provider_name] = provider

    def get(self, provider_name: str) -> SocialAuthProvider | None:
        return self._providers.get(provider_name)

    def available_providers(self) -> list[str]:
        return sorted(self._providers.keys())
