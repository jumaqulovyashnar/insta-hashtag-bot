import os
import django
import asyncio

# Bootstrap Django settings for tests
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import TransactionTestCase
from botapp.models import BotUser, MandatoryChannel, RequestLog
from domain.entities.post import Post
from domain.value_objects.hashtag import Hashtag

from infrastructure.persistence.django_user_repository import DjangoUserRepository
from application.use_cases.register_user_use_case import RegisterUserUseCase
from application.use_cases.check_subscription_use_case import CheckSubscriptionUseCase
from application.use_cases.extract_hashtags_use_case import ExtractHashtagsUseCase
from application.interfaces.instagram_gateway import InstagramGateway
from unittest.mock import AsyncMock, MagicMock

class TestBotFlowIntegration(TransactionTestCase):
    def setUp(self):
        # Instantiate repository
        self.repository = DjangoUserRepository()
        
        # Instantiate use cases
        self.register_use_case = RegisterUserUseCase(self.repository)
        self.check_sub_use_case = CheckSubscriptionUseCase(self.repository)
        
        # Create mock gateway
        self.mock_gateway = MagicMock(spec=InstagramGateway)
        self.extract_use_case = ExtractHashtagsUseCase(self.mock_gateway, self.repository)
        
        # Clear existing test data
        BotUser.objects.all().delete()
        MandatoryChannel.objects.all().delete()
        RequestLog.objects.all().delete()
        
        # Event loop to run async methods inside sync tests
        self.loop = asyncio.get_event_loop()

    def test_full_bot_flow_with_subscription(self):
        # 1. Setup a mandatory channel in DB (Sync context works perfectly here)
        MandatoryChannel.objects.create(
            channel_id="@shox_luxe",
            channel_link="https://t.me/shox_luxe",
            is_active=True
        )

        # 2. Simulate User /start registration (run async method inside loop)
        user = self.loop.run_until_complete(
            self.register_use_case.execute(telegram_id=5555, username="yashnar")
        )
        self.assertEqual(user.username, "yashnar")
        self.assertEqual(user.telegram_id, 5555)
        self.assertFalse(user.is_subscribed)

        # 3. Simulate subscription check (unsubscribed first)
        mock_bot = MagicMock()
        mock_chat_member = MagicMock()
        mock_chat_member.status = "left"
        mock_bot.get_chat_member = AsyncMock(return_value=mock_chat_member)

        is_subbed, unsubbed_channels = self.loop.run_until_complete(
            self.check_sub_use_case.execute(mock_bot, 5555)
        )
        self.assertFalse(is_subbed)
        self.assertEqual(len(unsubbed_channels), 1)
        self.assertEqual(unsubbed_channels[0]['channel_id'], "@shox_luxe")
        
        # Verify status in DB updated to False
        db_user = BotUser.objects.get(telegram_id=5555)
        self.assertFalse(db_user.is_subscribed)

        # 4. Simulate user subscribes and re-checks
        mock_chat_member.status = "member"
        mock_bot.get_chat_member = AsyncMock(return_value=mock_chat_member)
        
        is_subbed, unsubbed_channels = self.loop.run_until_complete(
            self.check_sub_use_case.execute(mock_bot, 5555)
        )
        self.assertTrue(is_subbed)
        self.assertEqual(len(unsubbed_channels), 0)
        
        # Verify status in DB updated to True
        db_user = BotUser.objects.get(telegram_id=5555)
        self.assertTrue(db_user.is_subscribed)

        # 5. Simulate sending Instagram link for parsing
        post = Post(
            shortcode="DasBKDHC_XA",
            url="https://instagram.com/reel/DasBKDHC_XA",
            caption="Plain caption text",
            comments=["First comment #motivation", "Second comment"]
        )
        self.mock_gateway.fetch_post = AsyncMock(return_value=post)

        result = self.loop.run_until_complete(
            self.extract_use_case.execute(user_telegram_id=5555, url="https://instagram.com/reel/DasBKDHC_XA")
        )
        
        # Verification of fallback (caption was empty of tags, comments should hold it)
        self.assertEqual(result.source, 'comments')
        self.assertEqual(len(result.hashtags), 1)
        self.assertEqual(result.hashtags[0], Hashtag("motivation"))
        self.assertIn("First comment", result.preview_text)

        # Verify request log is saved in DB
        logs = RequestLog.objects.filter(user=db_user)
        self.assertEqual(logs.count(), 1)
        self.assertEqual(logs[0].instagram_url, "https://instagram.com/reel/DasBKDHC_XA")
        self.assertEqual(logs[0].hashtags_found, "motivation")
