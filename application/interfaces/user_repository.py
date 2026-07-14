from abc import ABC, abstractmethod
from domain.entities.user import User

class UserRepository(ABC):
    @abstractmethod
    async def get_or_create_user(self, telegram_id: int, username: str | None = None, referred_by_id: int | None = None) -> User:
        """Get or create user record."""
        pass

    @abstractmethod
    async def get_referral_count(self, telegram_id: int) -> int:
        """Get the count of users invited by this user."""
        pass

    @abstractmethod
    async def update_subscription_status(self, telegram_id: int, is_subscribed: bool) -> None:
        """Update user subscription status."""
        pass

    @abstractmethod
    async def log_request(self, user: User, url: str, hashtags: list[str]) -> None:
        """Log a hashtag extraction request."""
        pass

    @abstractmethod
    async def get_active_mandatory_channels(self) -> list[dict]:
        """Get list of active mandatory channels (dict representation)."""
        pass
