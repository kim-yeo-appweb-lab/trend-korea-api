from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(slots=True)
class SocialUser:
    provider: str
    provider_user_id: str
    email: str | None
    nickname: str | None


class SocialAuthProvider(ABC):
    provider_name: str

    @abstractmethod
    def exchange_code(self, code: str) -> SocialUser:
        raise NotImplementedError
