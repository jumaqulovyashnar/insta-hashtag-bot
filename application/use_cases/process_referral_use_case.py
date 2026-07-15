import logging
from application.interfaces.user_repository import UserRepository
from application.interfaces.coin_repository import CoinRepository
from application.interfaces.settings_repository import SettingsRepository
from application.interfaces.vip_notifier import VipNotifier
from domain.services.referral_rules import has_unlocked_vip

logger = logging.getLogger(__name__)

class ProcessReferralUseCase:
    def __init__(
        self,
        user_repo: UserRepository,
        coin_repo: CoinRepository,
        settings_repo: SettingsRepository,
        vip_notifier: VipNotifier
    ):
        self.user_repo = user_repo
        self.coin_repo = coin_repo
        self.settings_repo = settings_repo
        self.vip_notifier = vip_notifier

    async def execute(
        self, 
        new_user_telegram_id: int, 
        referral_code: str, 
        new_user_username: str | None = None
    ) -> dict:
        logger.info(
            "Processing referral code '%s' for new user Telegram ID: %d", 
            referral_code, new_user_telegram_id
        )

        # 1. Fetch referrer
        referrer = await self.user_repo.get_by_referral_code(referral_code)
        if not referrer:
            logger.warning("Referral code '%s' is invalid or not found.", referral_code)
            return {"success": False, "reason": "invalid_code"}

        # 2. Fraud prevention: Self-referral
        if referrer.telegram_id == new_user_telegram_id:
            logger.warning("Fraud alert: user %d tried to self-refer.", new_user_telegram_id)
            return {"success": False, "reason": "self_referral"}

        # 3. Fraud prevention: Check if user already exists (not a genuinely new user)
        existing_user = await self.user_repo.get_by_telegram_id(new_user_telegram_id)
        if existing_user:
            logger.warning(
                "Fraud alert: user %d is already registered, cannot count as referral.", 
                new_user_telegram_id
            )
            return {"success": False, "reason": "already_registered"}

        # 4. Fetch settings
        coins_per_referral = await self.settings_repo.get_setting_int("COINS_PER_REFERRAL", 5)
        vip_threshold = await self.settings_repo.get_setting_int("VIP_UNLOCK_THRESHOLD", 60)

        # 5. Register the new user with referrer attribution
        # This will create user, setting referred_by_id to referrer.telegram_id
        new_user = await self.user_repo.get_or_create_user(
            telegram_id=new_user_telegram_id,
            username=new_user_username,
            referred_by_id=referrer.telegram_id
        )

        # 6. Add coins to the referrer and log the transaction
        await self.coin_repo.add_coins(
            telegram_id=referrer.telegram_id,
            amount=coins_per_referral,
            reason="referral_bonus"
        )

        # 7. Get updated referrer state (to see new coins count)
        updated_referrer = await self.user_repo.get_by_telegram_id(referrer.telegram_id)
        if not updated_referrer:
            # Fallback if somehow not found
            return {"success": True, "referrer_id": referrer.telegram_id, "coins_earned": coins_per_referral, "vip_just_unlocked": False}

        # Log coin addition and VIP unlock check
        new_total = updated_referrer.total_coins
        is_unlocked = has_unlocked_vip(new_total, vip_threshold)
        logger.info(
            f"user={referrer.telegram_id} coins={new_total} threshold={vip_threshold} unlocked={is_unlocked}"
        )

        # 8. Check VIP eligibility
        vip_just_unlocked = False
        was_vip_before = referrer.has_vip_access
        
        if not was_vip_before and is_unlocked:
            logger.info("User %d has reached VIP threshold. Granting access...", referrer.telegram_id)
            await self.user_repo.grant_vip_access(referrer.telegram_id)
            
            # Fetch invite link and notify
            invite_link = await self.user_repo.get_active_vip_invite_link()
            if invite_link:
                try:
                    await self.vip_notifier.send_vip_unlock_message(referrer.telegram_id, invite_link)
                    vip_just_unlocked = True
                except Exception as e:
                    logger.error("Failed to notify VIP unlock to user %d: %s", referrer.telegram_id, str(e))
            else:
                logger.error("No active VIP invite link configured in settings.")

        # 9. Notify referrer about coins earned (with VIP progress)
        try:
            await self.vip_notifier.notify_new_referral(
                referrer_telegram_id=referrer.telegram_id,
                referred_username=new_user_username,
                coins_earned=coins_per_referral,
                total_coins=updated_referrer.total_coins,
                vip_threshold=vip_threshold,
                is_vip_unlocked=vip_just_unlocked
            )
        except Exception as e:
            logger.error("Failed to notify referral reward to user %d: %s", referrer.telegram_id, str(e))

        return {
            "success": True,
            "referrer_id": referrer.telegram_id,
            "coins_earned": coins_per_referral,
            "total_coins": updated_referrer.total_coins,
            "vip_just_unlocked": vip_just_unlocked
        }
