from aiogram import Bot
from aiogram.enums import ChatMemberStatus
from application.interfaces.user_repository import UserRepository

MEMBER_STATUSES = {
    ChatMemberStatus.MEMBER,
    ChatMemberStatus.ADMINISTRATOR,
    ChatMemberStatus.CREATOR,
}

class CheckSubscriptionUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, bot: Bot, user_telegram_id: int) -> tuple[bool, list[dict]]:
        """
        Check subscription status.
        Returns:
            (is_subscribed, list_of_unsubscribed_channels)
        """
        channels = await self.user_repository.get_active_mandatory_channels()
        if not channels:
            return True, []

        unsubscribed = []

        for channel in channels:
            try:
                member = await bot.get_chat_member(
                    chat_id=channel['channel_id'],
                    user_id=user_telegram_id,
                )
                if member.status not in MEMBER_STATUSES:
                    unsubscribed.append(channel)
            except Exception:
                # Safe assumption: if we can't fetch, user is not subscribed
                unsubscribed.append(channel)

        is_subscribed = len(unsubscribed) == 0
        
        # Update user's is_subscribed status in repository
        await self.user_repository.update_subscription_status(user_telegram_id, is_subscribed)
        
        return is_subscribed, unsubscribed
