import logging
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from application.interfaces.vip_notifier import VipNotifier

logger = logging.getLogger(__name__)

class TelegramVipNotifier(VipNotifier):
    def __init__(self, bot: Bot):
        self.bot = bot

    async def send_vip_unlock_message(self, telegram_id: int, invite_link: str) -> None:
        """
        Send VIP unlock notification message with the invite link to the user on Telegram.
        """
        try:
            markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🎖️ VIP Kanal", url=invite_link)]
            ])
            await self.bot.send_message(
                chat_id=telegram_id,
                text=(
                    "🎖️ <b>Tabriklaymiz! VIP Kanalga kirish huquqini qo'lga kiritdingiz!</b>\n\n"
                    "Siz to'plagan tangalar soni VIP darajaga yetdi. Quyidagi tugma orqali kanalga qo'shilishingiz mumkin:"
                ),
                parse_mode="HTML",
                reply_markup=markup
            )
            logger.info("Sent VIP unlock invite link to user %d", telegram_id)
        except Exception as e:
            logger.error("Failed to send VIP unlock to user %d: %s", telegram_id, str(e))

    async def notify_new_referral(
        self, 
        referrer_telegram_id: int, 
        referred_username: str | None, 
        coins_earned: int, 
        total_coins: int,
        vip_threshold: int = 5,
        is_vip_unlocked: bool = False
    ) -> None:
        """
        Notify the referrer that someone joined via their link and they earned coins.
        Includes VIP progress information.
        """
        username_str = f" (@{referred_username})" if referred_username else ""
        
        # Calculate remaining coins needed for VIP
        coins_remaining = max(0, vip_threshold - total_coins)
        
        # Build progress message
        if is_vip_unlocked:
            vip_status = "🔓 <b>VIP kanal ochilgan!</b>"
        else:
            vip_status = f"🔓 <b>VIP kanal uchun yana {coins_remaining} tanga kerak</b> ({total_coins}/{vip_threshold})"
        
        try:
            await self.bot.send_message(
                chat_id=referrer_telegram_id,
                text=(
                    f"🎉 <b>Yangi taklif!</b>\n"
                    f"Sizning havolangiz orqali yangi do'stingiz{username_str} botga qo'shildi!\n\n"
                    f"🪙 <b>+{coins_earned} tanga</b> balansingizga qo'shildi.\n"
                    f"💰 <b>Jami:</b> {total_coins} tanga.\n\n"
                    f"{vip_status}"
                ),
                parse_mode="HTML"
            )
            logger.info("Notified referrer %d of new referral", referrer_telegram_id)
        except Exception as e:
            logger.error("Failed to notify referrer %d: %s", referrer_telegram_id, str(e))
