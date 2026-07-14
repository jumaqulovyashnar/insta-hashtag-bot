from dataclasses import dataclass
from application.interfaces.user_repository import UserRepository
from application.interfaces.settings_repository import SettingsRepository
from domain.services.referral_rules import coins_remaining_for_vip

@dataclass
class ReferralInfo:
    referral_code: str
    referral_link: str
    count: int
    total_coins: int
    has_vip_access: bool
    coins_remaining: int

class GetReferralsUseCase:
    def __init__(self, user_repository: UserRepository, settings_repository: SettingsRepository):
        self.user_repository = user_repository
        self.settings_repository = settings_repository

    async def execute(self, telegram_id: int, bot_username: str) -> ReferralInfo:
        # Fetch user
        user = await self.user_repository.get_by_telegram_id(telegram_id)
        if not user:
            # Fallback/create if user doesn't exist yet
            user = await self.user_repository.get_or_create_user(telegram_id)
        
        # Build invite link using the user's personal referral code
        referral_link = f"https://t.me/{bot_username}?start={user.referral_code}"
        
        # Get threshold setting
        vip_threshold = await self.settings_repository.get_setting_int("VIP_UNLOCK_THRESHOLD", 5)
        
        remaining = coins_remaining_for_vip(user.total_coins, vip_threshold)
        
        return ReferralInfo(
            referral_code=user.referral_code,
            referral_link=referral_link,
            count=user.total_referrals,
            total_coins=user.total_coins,
            has_vip_access=user.has_vip_access,
            coins_remaining=remaining
        )
