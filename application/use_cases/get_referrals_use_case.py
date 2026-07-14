from dataclasses import dataclass
from application.interfaces.user_repository import UserRepository

@dataclass
class ReferralInfo:
    referral_link: str
    count: int

class GetReferralsUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, telegram_id: int, bot_username: str = "insta_hashtagbot") -> ReferralInfo:
        # Fetch the count from repository
        count = await self.user_repository.get_referral_count(telegram_id)
        
        # Build the invite link using start payload syntax
        referral_link = f"https://t.me/{bot_username}?start={telegram_id}"
        
        return ReferralInfo(
            referral_link=referral_link,
            count=count
        )
