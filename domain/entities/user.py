from dataclasses import dataclass
from datetime import datetime

@dataclass
class User:
    telegram_id: int
    username: str | None = None
    is_subscribed: bool = False
    referred_by_id: int | None = None
    referral_code: str | None = None
    total_referrals: int = 0
    total_coins: int = 0
    has_vip_access: bool = False
    vip_unlocked_at: datetime | None = None
    created_at: datetime | None = None
