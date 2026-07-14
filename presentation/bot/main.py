"""
Composition Root of the Instagram Hashtag Bot.
Wires domain, application, and infrastructure layers.
Includes process singleton locking and graceful shutdown handles.
"""

import asyncio
import logging
import os
import signal
import sys
from pathlib import Path
from filelock import FileLock, Timeout

# 1. Bootstrapping Django ORM
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

# 2. Importing aiogram and interfaces
from aiogram import Bot, Dispatcher
from config.settings import BOT_TOKEN
from presentation.bot.handlers import router

# Concrete Adapters
from infrastructure.instagram.yt_dlp_gateway import YtdlpInstagramGateway
from infrastructure.persistence.django_user_repository import DjangoUserRepository

# Use Cases
from application.use_cases.register_user_use_case import RegisterUserUseCase
from application.use_cases.check_subscription_use_case import CheckSubscriptionUseCase
from application.use_cases.extract_hashtags_use_case import ExtractHashtagsUseCase
from application.use_cases.get_referrals_use_case import GetReferralsUseCase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# FileLock configuration
LOCK_FILE = PROJECT_ROOT / "bot.lock"
lock = FileLock(LOCK_FILE, timeout=0)

async def main() -> None:
    # Acquire filelock to ensure single instance
    try:
        lock.acquire()
        logger.info("Bot lock acquired successfully.")
    except Timeout:
        logger.error(
            "Conflict: Another instance of this bot is already running. "
            "Please stop the other instance and release bot.lock first."
        )
        sys.exit(1)

    if not BOT_TOKEN or BOT_TOKEN == 'your-bot-token-here':
        logger.error("BOT_TOKEN is not set in the environment variables.")
        lock.release()
        sys.exit(1)

    # Instantiate adapters
    instagram_gateway = YtdlpInstagramGateway()
    user_repository = DjangoUserRepository()

    # Instantiate use cases
    register_user_use_case = RegisterUserUseCase(user_repository)
    check_subscription_use_case = CheckSubscriptionUseCase(user_repository)
    extract_hashtags_use_case = ExtractHashtagsUseCase(instagram_gateway, user_repository)
    get_referrals_use_case = GetReferralsUseCase(user_repository)

    # aiogram setups
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Inject use cases as context kwargs into aiogram dispatch flow
    dp['register_user_use_case'] = register_user_use_case
    dp['check_subscription_use_case'] = check_subscription_use_case
    dp['extract_hashtags_use_case'] = extract_hashtags_use_case
    dp['get_referrals_use_case'] = get_referrals_use_case

    dp.include_router(router)

    # Graceful Shutdown Handlers
    loop = asyncio.get_running_loop()

    async def shutdown():
        logger.info("Graceful shutdown initiated...")
        # Release Telegram polling
        await dp.stop_polling()
        await bot.session.close()
        # Release process lock
        if lock.is_locked:
            lock.release()
        logger.info("Cleanup complete. Exiting.")
        sys.exit(0)

    # Register signals for clean termination
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown()))
        except NotImplementedError:
            # add_signal_handler is not implemented on Windows under asyncio in some cases,
            # we handle keyboard interrupts in general try-finally block below.
            pass

    logger.info("Bot starting...")
    await bot.delete_webhook(drop_pending_updates=True)

    try:
        await dp.start_polling(bot)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        # Final safety cleanup for lock release on windows
        if lock.is_locked:
            lock.release()
            logger.info("Bot lock released.")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        # Graceful exit on windows CLI interrupt
        if lock.is_locked:
            lock.release()
        sys.exit(0)
