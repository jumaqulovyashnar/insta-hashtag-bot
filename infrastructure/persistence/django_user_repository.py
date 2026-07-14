import uuid
from datetime import datetime
from asgiref.sync import sync_to_async
from django.db.models import F
from django.utils import timezone
from domain.entities.user import User
from application.interfaces.user_repository import UserRepository
from botapp.models import BotUser, MandatoryChannel, RequestLog, VipChannel

class DjangoUserRepository(UserRepository):
    async def get_or_create_user(
        self, 
        telegram_id: int, 
        username: str | None = None, 
        referred_by_id: int | None = None
    ) -> User:
        """
        Get or create a BotUser. Automatically generates a unique referral_code for new users.
        """
        @sync_to_async
        def _get_or_create():
            # Try to get existing user
            try:
                user = BotUser.objects.get(telegram_id=telegram_id)
                created = False
            except BotUser.DoesNotExist:
                # If creating, generate a unique referral code
                unique_ref = False
                ref_code = ""
                while not unique_ref:
                    ref_code = f"REF{uuid.uuid4().hex[:6].upper()}"
                    if not BotUser.objects.filter(referral_code=ref_code).exists():
                        unique_ref = True
                
                # Check for referrer
                referrer_obj = None
                if referred_by_id and referred_by_id != telegram_id:
                    try:
                        referrer_obj = BotUser.objects.get(telegram_id=referred_by_id)
                    except BotUser.DoesNotExist:
                        pass
                
                user = BotUser.objects.create(
                    telegram_id=telegram_id,
                    username=username,
                    referred_by=referrer_obj,
                    referral_code=ref_code
                )
                created = True

                # Safely increment referrer's count of total_referrals using F()
                if referrer_obj:
                    BotUser.objects.filter(telegram_id=referred_by_id).update(
                        total_referrals=F('total_referrals') + 1
                    )
            
            # If user already existed, update username if it changed
            if not created and user.username != username:
                user.username = username
                user.save(update_fields=['username'])
                
            # If the user has no referral code (e.g. legacy user created before migration), generate one
            if not user.referral_code:
                unique_ref = False
                ref_code = ""
                while not unique_ref:
                    ref_code = f"REF{uuid.uuid4().hex[:6].upper()}"
                    if not BotUser.objects.filter(referral_code=ref_code).exists():
                        unique_ref = True
                user.referral_code = ref_code
                user.save(update_fields=['referral_code'])

            ref_id = user.referred_by.telegram_id if user.referred_by else None
            return self._to_domain(user, ref_id)

        return await _get_or_create()

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        """
        Fetch a user by their Telegram ID.
        """
        @sync_to_async
        def _get():
            try:
                user = BotUser.objects.get(telegram_id=telegram_id)
                ref_id = user.referred_by.telegram_id if user.referred_by else None
                return self._to_domain(user, ref_id)
            except BotUser.DoesNotExist:
                return None

        return await _get()

    async def get_by_referral_code(self, referral_code: str) -> User | None:
        """
        Fetch a user by their referral code.
        """
        @sync_to_async
        def _get():
            try:
                user = BotUser.objects.get(referral_code=referral_code)
                ref_id = user.referred_by.telegram_id if user.referred_by else None
                return self._to_domain(user, ref_id)
            except BotUser.DoesNotExist:
                return None

        return await _get()

    async def get_referral_count(self, telegram_id: int) -> int:
        """
        Get the count of users referred by this user.
        """
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

    async def grant_vip_access(self, telegram_id: int) -> None:
        """
        Grant VIP status and set the unlock timestamp.
        """
        @sync_to_async
        def _grant():
            BotUser.objects.filter(telegram_id=telegram_id).update(
                has_vip_access=True,
                vip_unlocked_at=timezone.now()
            )

        await _grant()

    async def get_active_vip_invite_link(self) -> str | None:
        """
        Fetch the active VIP channel invite link.
        """
        @sync_to_async
        def _get_link():
            try:
                channel = VipChannel.objects.filter(is_active=True).first()
                return channel.invite_link if channel else None
            except Exception:
                return None

        return await _get_link()

    def _to_domain(self, db_user: BotUser, referred_by_id: int | None) -> User:
        """Helper to convert BotUser Django model to domain User entity."""
        return User(
            telegram_id=db_user.telegram_id,
            username=db_user.username,
            is_subscribed=db_user.is_subscribed,
            referred_by_id=referred_by_id,
            referral_code=db_user.referral_code,
            total_referrals=db_user.total_referrals,
            total_coins=db_user.total_coins,
            has_vip_access=db_user.has_vip_access,
            vip_unlocked_at=db_user.vip_unlocked_at,
            created_at=db_user.created_at
        )
