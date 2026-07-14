import logging
from aiogram import Bot
from aiogram.enums import ChatMemberStatus
from application.interfaces.user_repository import UserRepository

logger = logging.getLogger(__name__)

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
        Check subscription status live on Telegram API.
        Returns:
            (is_subscribed, list_of_unsubscribed_channels)
        """
        channels = await self.user_repository.get_active_mandatory_channels()
        if not channels:
            return True, []

        unsubscribed = []

        for channel in channels:
            channel_id = channel['channel_id']
            try:
                member = await bot.get_chat_member(
                    chat_id=channel_id,
                    user_id=user_telegram_id,
                )
                if member.status not in MEMBER_STATUSES:
                    logger.warning(
                        "User %d is blocked: status is '%s' in channel %s (missing subscription).",
                        user_telegram_id, member.status, channel_id
                    )
                    unsubscribed.append(channel)
            except Exception as e:
                # Log the exact exception to diagnose issues like missing admin rights or bad channel ID format
                logger.error(
                    "Error checking subscription for user %d in channel %s: %s. Treating as NOT subscribed (fail closed).",
                    user_telegram_id, channel_id, str(e)
                )
                unsubscribed.append(channel)

        is_subscribed = len(unsubscribed) == 0
        
        # Update user's is_subscribed status in repository for display/analytics
        await self.user_repository.update_subscription_status(user_telegram_id, is_subscribed)
        
        return is_subscribed, unsubscribed
