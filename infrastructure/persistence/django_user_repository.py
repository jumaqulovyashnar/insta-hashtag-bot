from asgiref.sync import sync_to_async
from domain.entities.user import User
from application.interfaces.user_repository import UserRepository
from botapp.models import BotUser, MandatoryChannel, RequestLog

class DjangoUserRepository(UserRepository):
    async def get_or_create_user(self, telegram_id: int, username: str | None = None, referred_by_id: int | None = None) -> User:
        @sync_to_async
        def _get_or_create():
            user, created = BotUser.objects.get_or_create(
                telegram_id=telegram_id,
                defaults={'username': username}
            )
            
            # If the user was just created and there is a referrer_id
            if created and referred_by_id and referred_by_id != telegram_id:
                try:
                    referrer = BotUser.objects.get(telegram_id=referred_by_id)
                    user.referred_by = referrer
                    user.save(update_fields=['referred_by'])
                except BotUser.DoesNotExist:
                    pass # Referrer doesn't exist yet, ignore
            
            if not created and user.username != username:
                user.username = username
                user.save(update_fields=['username'])
            
            ref_id = user.referred_by.telegram_id if user.referred_by else None
            return User(
                telegram_id=user.telegram_id,
                username=user.username,
                is_subscribed=user.is_subscribed,
                referred_by_id=ref_id,
                created_at=user.created_at
            )

        return await _get_or_create()

    async def get_referral_count(self, telegram_id: int) -> int:
        @sync_to_async
        def _get_count():
            return BotUser.objects.filter(referred_by__telegram_id=telegram_id).count()

        return await _get_count()

    async def update_subscription_status(self, telegram_id: int, is_subscribed: bool) -> None:
        @sync_to_async
        def _update():
            BotUser.objects.filter(telegram_id=telegram_id).update(is_subscribed=is_subscribed)

        await _update()

    async def log_request(self, user: User, url: str, hashtags: list[str]) -> None:
        @sync_to_async
        def _log():
            try:
                db_user = BotUser.objects.get(telegram_id=user.telegram_id)
                RequestLog.objects.create(
                    user=db_user,
                    instagram_url=url,
                    hashtags_found=', '.join(hashtags) if hashtags else ''
                )
            except BotUser.DoesNotExist:
                pass

        await _log()

    async def get_active_mandatory_channels(self) -> list[dict]:
        @sync_to_async
        def _get_channels():
            qs = MandatoryChannel.objects.filter(is_active=True)
            return [
                {
                    'channel_id': c.channel_id,
                    'channel_link': c.channel_link,
                    'is_active': c.is_active
                }
                for c in qs
            ]

        return await _get_channels()
