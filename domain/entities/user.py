from dataclasses import dataclass
from datetime import datetime

@dataclass
class User:
    telegram_id: int
    username: str | None = None
    is_subscribed: bool = False
    referred_by_id: int | None = None
    created_at: datetime | None = None
