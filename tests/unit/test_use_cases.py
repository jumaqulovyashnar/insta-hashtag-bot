import unittest
from unittest.mock import AsyncMock, MagicMock
from domain.entities.post import Post
from domain.entities.user import User
from domain.value_objects.hashtag import Hashtag
from application.use_cases.extract_hashtags_use_case import ExtractHashtagsUseCase
from application.interfaces.instagram_gateway import InstagramGateway
from application.interfaces.user_repository import UserRepository

class TestExtractHashtagsUseCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_gateway = MagicMock(spec=InstagramGateway)
        self.mock_repository = MagicMock(spec=UserRepository)
        self.use_case = ExtractHashtagsUseCase(self.mock_gateway, self.mock_repository)
        
        # Setup repository get_or_create mock
        self.mock_user = User(telegram_id=123, username="testuser")
        self.mock_repository.get_or_create_user = AsyncMock(return_value=self.mock_user)
        self.mock_repository.log_request = AsyncMock()

    async def test_extract_from_caption(self):
        post = Post(
            shortcode="ABC123",
            url="https://instagram.com/p/ABC123",
            caption="This is a post caption #world",
            comments=["comment one", "comment two #hello"]
        )
        self.mock_gateway.fetch_post = AsyncMock(return_value=post)

        result = await self.use_case.execute(user_telegram_id=123, url="https://instagram.com/p/ABC123")
        
        self.assertEqual(result.source, 'caption')
        self.assertEqual(len(result.hashtags), 1)
        self.assertEqual(result.hashtags[0], Hashtag("world"))
        self.mock_repository.log_request.assert_called_once_with(self.mock_user, "https://instagram.com/p/ABC123", ["world"])

    async def test_extract_from_comments_fallback(self):
        post = Post(
            shortcode="ABC123",
            url="https://instagram.com/p/ABC123",
            caption="No hashtags here",
            comments=["comment one", "comment two #fallback"]
        )
        self.mock_gateway.fetch_post = AsyncMock(return_value=post)

        result = await self.use_case.execute(user_telegram_id=123, url="https://instagram.com/p/ABC123")
        
        self.assertEqual(result.source, 'comments')
        self.assertEqual(len(result.hashtags), 1)
        self.assertEqual(result.hashtags[0], Hashtag("fallback"))
        self.mock_repository.log_request.assert_called_once_with(self.mock_user, "https://instagram.com/p/ABC123", ["fallback"])

    async def test_no_hashtags_found(self):
        post = Post(
            shortcode="ABC123",
            url="https://instagram.com/p/ABC123",
            caption="Plain caption text",
            comments=["plain comment", "another plain comment"]
        )
        self.mock_gateway.fetch_post = AsyncMock(return_value=post)

        result = await self.use_case.execute(user_telegram_id=123, url="https://instagram.com/p/ABC123")
        
        self.assertEqual(result.source, 'none')
        self.assertEqual(len(result.hashtags), 0)
        self.mock_repository.log_request.assert_called_once_with(self.mock_user, "https://instagram.com/p/ABC123", [])


class TestGetReferralsUseCase(unittest.IsolatedAsyncioTestCase):
    async def test_get_referrals(self):
        from application.use_cases.get_referrals_use_case import GetReferralsUseCase
        mock_repo = MagicMock(spec=UserRepository)
        mock_repo.get_referral_count = AsyncMock(return_value=5)
        
        use_case = GetReferralsUseCase(mock_repo)
        result = await use_case.execute(telegram_id=98765, bot_username="my_bot")
        
        self.assertEqual(result.count, 5)
        self.assertEqual(result.referral_link, "https://t.me/my_bot?start=98765")
        mock_repo.get_referral_count.assert_called_once_with(98765)

