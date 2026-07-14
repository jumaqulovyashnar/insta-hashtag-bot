import logging

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart, CommandObject, Command
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from collections import defaultdict

from infrastructure.instagram.yt_dlp_gateway import (
    INSTAGRAM_URL_PATTERN,
    InstagramError,
    InvalidURLError,
    PostUnavailableError,
    RateLimitError,
)
from application.use_cases.register_user_use_case import RegisterUserUseCase
from application.use_cases.check_subscription_use_case import CheckSubscriptionUseCase
from application.use_cases.extract_hashtags_use_case import ExtractHashtagsUseCase
from application.use_cases.get_referrals_use_case import GetReferralsUseCase
from application.use_cases.process_referral_use_case import ProcessReferralUseCase
from .keyboards import (
    get_subscribe_keyboard, 
    get_main_menu_keyboard,
    BTN_SEND_LINK,
    BTN_REFERRAL,
    BTN_GUIDE,
    BTN_SUPPORT,
)

logger = logging.getLogger(__name__)

router = Router()

# Temporary storage for hashtag data (keyed by correlation_id)
_hashtags_cache = defaultdict(dict)

# ──────────────────────────────────────────────
# /start command
# ──────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(
    message: Message, 
    bot: Bot,
    command: CommandObject,
    register_user_use_case: RegisterUserUseCase,
    check_subscription_use_case: CheckSubscriptionUseCase,
    process_referral_use_case: ProcessReferralUseCase,
) -> None:
    # Check if there is a referral payload
    if command.args:
        ref_arg = command.args.strip()
        if ref_arg.startswith("REF"):
            # Execute referral mapping usecase
            await process_referral_use_case.execute(
                new_user_telegram_id=message.from_user.id,
                referral_code=ref_arg,
                new_user_username=message.from_user.username
            )
        else:
            # Fallback for legacy numerical referral ID
            referred_by_id = None
            if ref_arg.isdigit():
                referred_by_id = int(ref_arg)
            await register_user_use_case.execute(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                referred_by_id=referred_by_id
            )
    else:
        # Normal registration without referrer
        await register_user_use_case.execute(
            telegram_id=message.from_user.id,
            username=message.from_user.username
        )

    # Check subscription status
    is_subscribed, unsubscribed_channels = await check_subscription_use_case.execute(
        bot=bot,
        user_telegram_id=message.from_user.id
    )

    logger.info(
        "/start for user %d: is_subscribed=%s, unsubscribed_channels=%s",
        message.from_user.id, is_subscribed, len(unsubscribed_channels)
    )

    if is_subscribed:
        await message.answer(
            "👋 <b>Xush kelibsiz!</b>\n\n"
            "Menga Instagram Reels/Post havolasini yuboring, "
            "men sizga undagi barcha hashtaglarni topib beraman! 🔍\n\n"
            "📎 Misol: <code>https://www.instagram.com/p/ABC123/</code>",
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard(),
        )
    else:
        # Hide the bottom reply keyboard menu so they cannot access other options
        try:
            temp_msg = await message.answer("Tekshirilmoqda...", reply_markup=ReplyKeyboardRemove())
            await temp_msg.delete()
        except Exception:
            pass

        await message.answer(
            "👋 <b>Assalomu alaykum!</b>\n\n"
            "Botdan foydalanish uchun avval quyidagi kanalga obuna bo'ling:\n",
            parse_mode="HTML",
            reply_markup=get_subscribe_keyboard(unsubscribed_channels),
        )


# ──────────────────────────────────────────────
# "✅ Obuna bo'ldim" callback
# ──────────────────────────────────────────────

@router.callback_query(F.data == "check_subscription")
async def callback_check_subscription(
    callback: CallbackQuery, 
    bot: Bot,
    check_subscription_use_case: CheckSubscriptionUseCase,
) -> None:
    await callback.answer()

    is_subscribed, unsubscribed_channels = await check_subscription_use_case.execute(
        bot=bot,
        user_telegram_id=callback.from_user.id
    )

    logger.info(
        "Subscription check callback for user %d: is_subscribed=%s, unsubscribed=%s",
        callback.from_user.id, is_subscribed, len(unsubscribed_channels)
    )

    try:
        if is_subscribed:
            # Edit the message text first
            await callback.message.edit_text(
                "✅ <b>Obuna tasdiqlandi!</b>\n\n"
                "Menga Instagram Reels/Post havolasini yuboring, "
                "men sizga undagi barcha hashtaglarni topib beraman! 🔍\n\n"
                "📎 Misol: <code>https://www.instagram.com/p/ABC123/</code>",
                parse_mode="HTML",
            )
            # Send a new message to apply the main menu reply keyboard
            await callback.message.answer(
                "Botdan to'liq foydalanishingiz mumkin. Quyidagi tugmalar orqali boshqarishingiz mumkin 👇",
                reply_markup=get_main_menu_keyboard()
            )
            logger.info("Main menu keyboard sent to user %d after subscription confirmation", callback.from_user.id)
        else:
            await callback.message.edit_text(
                "❌ <b>Siz hali obuna bo'lmagansiz!</b>\n\n"
                "Iltimos, avval quyidagi kanalga obuna bo'ling:",
                parse_mode="HTML",
                reply_markup=get_subscribe_keyboard(unsubscribed_channels),
            )
            logger.info("User %d still not subscribed, showing subscription prompt again", callback.from_user.id)
    except TelegramBadRequest as e:
        logger.error("TelegramBadRequest in subscription callback for user %d: %s", callback.from_user.id, str(e))
    except Exception as e:
        logger.exception("Unexpected error in subscription callback for user %d", callback.from_user.id)


# ──────────────────────────────────────────────
# Main Menu Button Handlers
# ──────────────────────────────────────────────

@router.message(lambda msg: msg.text and msg.text.strip() == "🔗 Havola yuborish")
async def btn_send_link(message: Message) -> None:
    await message.answer(
        "📥 <b>Menga Instagram Reels yoki Post havolasini yuboring.</b>\n\n"
        "Matnda havola (link) borligiga ishonch hosil qiling.\n"
        "📎 Misol: <code>https://www.instagram.com/reel/DasBKDHC_XA/</code>",
        parse_mode="HTML"
    )


async def handle_referral_info_request(
    message: Message,
    bot: Bot,
    get_referrals_use_case: GetReferralsUseCase
) -> None:
    # Dynamically fetch bot's current username
    me = await bot.get_me()
    
    # Get referral link, count, coins, and VIP remaining balance info
    ref_info = await get_referrals_use_case.execute(
        telegram_id=message.from_user.id,
        bot_username=me.username
    )

    reply_markup = None
    if ref_info.has_vip_access:
        vip_status = "✅ <b>VIP kanal ochilgan!</b>"
        invite_link = await get_referrals_use_case.user_repository.get_active_vip_invite_link()
        if invite_link:
            reply_markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🎖️ VIP Kanal", url=invite_link)]
            ])
    else:
        vip_status = f"🔒 <b>VIP kanal uchun yana:</b> {ref_info.coins_remaining} tanga kerak"

    await message.answer(
        "🔗 <b>Taklif Havolasi Tizimi</b>\n\n"
        "Botga do'stlaringizni taklif qiling va ularning so'rovlarini kuzatib boring!\n\n"
        f"🔗 <b>Sizning taklif havolangiz:</b>\n"
        f"{ref_info.referral_link}\n\n"
        f"👥 <b>Taklif etilgan do'stlar:</b> {ref_info.count} ta\n"
        f"🪙 <b>Jami to'plangan tangalar:</b> {ref_info.total_coins} ta\n\n"
        f"{vip_status}",
        parse_mode="HTML",
        reply_markup=reply_markup
    )


@router.message(lambda msg: msg.text and msg.text.strip() == "👥 Taklif havolasi")
async def btn_referral(
    message: Message,
    bot: Bot,
    get_referrals_use_case: GetReferralsUseCase,
) -> None:
    await handle_referral_info_request(message, bot, get_referrals_use_case)


@router.message(Command("referral"))
async def cmd_referral(
    message: Message,
    bot: Bot,
    get_referrals_use_case: GetReferralsUseCase,
) -> None:
    await handle_referral_info_request(message, bot, get_referrals_use_case)


@router.message(lambda msg: msg.text and msg.text.strip() == "📚 Qo'llanma")
async def btn_guide(message: Message) -> None:
    await message.answer(
        "📚 <b>Botdan foydalanish bo'yicha yo'riqnoma:</b>\n\n"
        "1. Instagram ilovasida kerakli post yoki Reels'ni oching.\n"
        "2. Havolani nusxalash (Copy Link) tugmasini bosing.\n"
        "3. Usbu botga kelib, havolani yuboring.\n"
        "4. Bot avtomatik ravishda caption va birinchi kommentlarni tekshirib, barcha hashtaglarni chiroyli ko'rinishda taqdim etadi.\n\n"
        "<b>Qo'llab-quvvatlanadigan formatlar:</b>\n"
        "• Postlar (`instagram.com/p/...`)\n"
        "• Reels (`instagram.com/reel/...`)\n"
        "• IGTV (`instagram.com/tv/...`)",
        parse_mode="HTML",
    )


@router.message(lambda msg: msg.text and msg.text.strip() == "☎️ Qo'llab-quvvatlash")
async def btn_support(message: Message) -> None:
    await message.answer(
        "☎️ <b>Qo'llab-quvvatlash markazi</b>\n\n"
        "Agar botda xatolik yuz bersa yoki takliflaringiz bo'lsa, "
        "quyidagi hamkor kanal orqali murojaat qilishingiz mumkin:\n\n"
        "📢 <b>Hamkor kanalimiz:</b> @shox_luxe\n"
        "🤖 <b>Bot dasturchisi:</b> @insta_hashtagbot",
        parse_mode="HTML"
    )


# ──────────────────────────────────────────────
# Instagram link handler
# ──────────────────────────────────────────────

@router.message(F.text.regexp(INSTAGRAM_URL_PATTERN))
async def handle_instagram_link(
    message: Message, 
    bot: Bot,
    check_subscription_use_case: CheckSubscriptionUseCase,
    extract_hashtags_use_case: ExtractHashtagsUseCase,
) -> None:
    import uuid
    # Generate unique request correlation ID
    correlation_id = uuid.uuid4().hex[:8]
    logger.info(
        "[%s] Incoming Instagram link from user %d (%s): %s",
        correlation_id, message.from_user.id, message.from_user.username, message.text
    )

    # Re-check subscription every time
    is_subscribed, unsubscribed_channels = await check_subscription_use_case.execute(
        bot=bot,
        user_telegram_id=message.from_user.id
    )

    if not is_subscribed:
        try:
            temp_msg = await message.answer("Tekshirilmoqda...", reply_markup=ReplyKeyboardRemove())
            await temp_msg.delete()
        except Exception:
            pass

        await message.answer(
            "⚠️ <b>Botdan foydalanish uchun kanalga obuna bo'lishingiz kerak!</b>\n\n"
            "Quyidagi kanalga obuna bo'ling:",
            parse_mode="HTML",
            reply_markup=get_subscribe_keyboard(unsubscribed_channels),
        )
        return

    processing_msg = await message.answer("⏳ Hashtaglar izlanmoqda...")
    url = message.text.strip()

    try:
        result = await extract_hashtags_use_case.execute(
            user_telegram_id=message.from_user.id,
            url=url,
            correlation_id=correlation_id
        )
    except InvalidURLError as e:
        await processing_msg.edit_text(f"❌ {e}")
        return
    except PostUnavailableError as e:
        await processing_msg.edit_text(f"❌ {e}")
        return
    except RateLimitError as e:
        await processing_msg.edit_text(f"⏱ {e}")
        return
    except InstagramError as e:
        await processing_msg.edit_text(f"❌ {e}")
        return
    except ValueError as e:
        logger.error("[%s] Validation error: %s", correlation_id, str(e))
        await processing_msg.edit_text("⚠️ Xatolik yuz berdi, qaytadan urinib ko'ring.")
        return
    except Exception as e:
        logger.exception("[%s] Unexpected extraction handler error", correlation_id)
        await processing_msg.edit_text(f"❌ Xatolik yuz berdi: {e}")
        return

    # Text preview formatting
    preview_block = f"📝 <b>Tahlil qilingan matn (tavsif/komment):</b>\n<i>\"{result.preview_text}\"</i>"

    if result.source != 'none':
        # Option A: Each hashtag rendered individually as inline code
        option_a_text = ' '.join([f"<code>{str(h)}</code>" for h in result.hashtags])
        
        # Option B: One combined monospace block with all hashtags space-separated
        raw_tags_str = ' '.join([str(h) for h in result.hashtags])
        option_b_text = f"<pre><code>{raw_tags_str}</code></pre>"

        header_text = (
            f"✅ <b>Topilgan hashtaglar ({len(result.hashtags)} ta):</b>"
            if result.source == 'caption'
            else f"✅ <b>Kommentariyadan topildi (caption'da yo'q edi) ({len(result.hashtags)} ta):</b>"
        )

        # Create copy buttons for hashtags and comments
        raw_tags_str = ' '.join([str(h) for h in result.hashtags])
        
        # Store hashtags and comments data in cache
        _hashtags_cache[correlation_id] = {
            'hashtags': raw_tags_str,
            'comments': result.preview_text
        }
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📋 Hashtaglarni nusxalash",
                    callback_data=f"copy_hashtags:{correlation_id}"
                ),
                InlineKeyboardButton(
                    text="📝 Kommentlarni nusxalash",
                    callback_data=f"copy_comments:{correlation_id}"
                )
            ]
        ])

        option_a_text = ' '.join([f"<code>{str(h)}</code>" for h in result.hashtags])
        option_b_text = f"<pre><code>{raw_tags_str}</code></pre>"

        await processing_msg.edit_text(
            f"{header_text}\n\n"
            f"<b>1️⃣ Alohida nusxalash (bitta bosish):</b>\n"
            f"{option_a_text}\n\n"
            f"<b>2️⃣ Hammasini birdan nusxalash (bitta bosish):</b>\n"
            f"{option_b_text}\n\n"
            f"{preview_block}",
            parse_mode="HTML",
            reply_markup=keyboard
        )
    else:
        # source == 'none'
        await processing_msg.edit_text(
            f"🔍 <b>Hashtaglar topilmadi</b>\n\n"
            f"❌ Caption yoki kommentariyalarda hashtag topilmadi.\n\n"
            f"{preview_block}",
            parse_mode="HTML"
        )


# ──────────────────────────────────────────────
# Copy hashtags callback handlers
# ──────────────────────────────────────────────

@router.callback_query(F.data.startswith("copy_hashtags:"))
async def callback_copy_hashtags(callback: CallbackQuery) -> None:
    """Send all hashtags in copyable code format"""
    await callback.answer()
    correlation_id = callback.data.split(":")[1]
    
    if correlation_id in _hashtags_cache:
        hashtags_text = _hashtags_cache[correlation_id]['hashtags']
        
        await callback.message.answer(
            f"📋 <b>Topilgan hashtaglar (copy qiling):</b>\n\n"
            f"<code>{hashtags_text}</code>",
            parse_mode="HTML"
        )
        logger.info("[%s] User %d copied hashtags", correlation_id, callback.from_user.id)
    else:
        await callback.answer("⚠️ Ma'lumot topilmadi, qaytadan urinib ko'ring.", show_alert=True)


@router.callback_query(F.data.startswith("copy_comments:"))
async def callback_copy_comments(callback: CallbackQuery) -> None:
    """Send found comments in copyable code format"""
    await callback.answer()
    correlation_id = callback.data.split(":")[1]
    
    if correlation_id in _hashtags_cache:
        comments_text = _hashtags_cache[correlation_id]['comments']
        
        await callback.message.answer(
            f"📝 <b>Tahlil qilingan matn (copy qiling):</b>\n\n"
            f"<code>{comments_text}</code>",
            parse_mode="HTML"
        )
        logger.info("[%s] User %d copied comments", correlation_id, callback.from_user.id)
    else:
        await callback.answer("⚠️ Ma'lumot topilmadi, qaytadan urinib ko'ring.", show_alert=True)


# ──────────────────────────────────────────────
# Unknown messages
# ──────────────────────────────────────────────

@router.message()
async def handle_unknown(message: Message) -> None:
    await message.answer(
        "🤔 Men faqat Instagram post/reel havolalarini qabul qilaman.\n\n"
        "📎 Misol: <code>https://www.instagram.com/p/ABC123/</code>\n\n"
        "Yordam uchun /start buyrug'ini yuboring.",
        parse_mode="HTML",
    )
