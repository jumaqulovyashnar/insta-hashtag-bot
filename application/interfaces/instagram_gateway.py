from abc import ABC, abstractmethod
from domain.entities.post import Post

class InstagramGateway(ABC):
    @abstractmethod
    async def fetch_post(self, url: str, correlation_id: str | None = None) -> Post:
        """
        Fetch post details including caption and comments.
        Raises specific exceptions for unavailability or rate-limiting.
        """
        pass
