import unittest
from unittest.mock import AsyncMock, MagicMock
from domain.entities.user import User
from domain.services import referral_rules
from application.interfaces.user_repository import UserRepository
from application.interfaces.coin_repository import CoinRepository
from application.interfaces.settings_repository import SettingsRepository
from application.interfaces.vip_notifier import VipNotifier
from application.use_cases.process_referral_use_case import ProcessReferralUseCase

class TestReferralRules(unittest.TestCase):
    def test_calculate_coins_earned(self):
        self.assertEqual(referral_rules.calculate_coins_earned(10, 5), 50)
        self.assertEqual(referral_rules.calculate_coins_earned(0, 5), 0)

    def test_has_unlocked_vip(self):
        self.assertFalse(referral_rules.has_unlocked_vip(95, 100))
        self.assertTrue(referral_rules.has_unlocked_vip(100, 100))
        self.assertTrue(referral_rules.has_unlocked_vip(105, 100))

    def test_coins_remaining_for_vip(self):
        self.assertEqual(referral_rules.coins_remaining_for_vip(80, 100), 20)
        self.assertEqual(referral_rules.coins_remaining_for_vip(120, 100), 0)


class TestProcessReferralUseCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_user_repo = MagicMock(spec=UserRepository)
        self.mock_coin_repo = MagicMock(spec=CoinRepository)
        self.mock_settings_repo = MagicMock(spec=SettingsRepository)
        self.mock_vip_notifier = MagicMock(spec=VipNotifier)
        
        self.use_case = ProcessReferralUseCase(
            user_repo=self.mock_user_repo,
            coin_repo=self.mock_coin_repo,
            settings_repo=self.mock_settings_repo,
            vip_notifier=self.mock_vip_notifier
        )
        
        # Default mock values
        self.mock_settings_repo.get_setting_int = AsyncMock(side_effect=lambda key, default: default)
        self.mock_coin_repo.add_coins = AsyncMock()

    async def test_successful_referral_logic(self):
        # Setup mock entities
        referrer = User(telegram_id=123, username="referrer_user", referral_code="REF123", total_coins=0, has_vip_access=False)
        new_user = User(telegram_id=456, username="new_user", referred_by_id=123, referral_code="REF456")
        updated_referrer = User(telegram_id=123, username="referrer_user", referral_code="REF123", total_coins=4, has_vip_access=False)

        self.mock_user_repo.get_by_referral_code = AsyncMock(return_value=referrer)
        self.mock_user_repo.get_by_telegram_id = AsyncMock(side_effect=lambda tid: None if tid == 456 else updated_referrer)
        self.mock_user_repo.get_or_create_user = AsyncMock(return_value=new_user)
        self.mock_vip_notifier.notify_new_referral = AsyncMock()

        result = await self.use_case.execute(new_user_telegram_id=456, referral_code="REF123", new_user_username="new_user")
        
        self.assertTrue(result["success"])
        self.assertEqual(result["coins_earned"], 5)
        self.assertEqual(result["total_coins"], 4)
        self.assertFalse(result["vip_just_unlocked"])
        
        self.mock_coin_repo.add_coins.assert_called_once_with(telegram_id=123, amount=5, reason="referral_bonus")
        self.mock_vip_notifier.notify_new_referral.assert_called_once()

    async def test_invalid_referral_code(self):
        self.mock_user_repo.get_by_referral_code = AsyncMock(return_value=None)

        result = await self.use_case.execute(new_user_telegram_id=456, referral_code="INVALID")
        
        self.assertFalse(result["success"])
        self.assertEqual(result["reason"], "invalid_code")
        self.mock_coin_repo.add_coins.assert_not_called()

    async def test_self_referral_prevented(self):
        referrer = User(telegram_id=123, username="test_user", referral_code="REF123")
        self.mock_user_repo.get_by_referral_code = AsyncMock(return_value=referrer)

        result = await self.use_case.execute(new_user_telegram_id=123, referral_code="REF123")
        
        self.assertFalse(result["success"])
        self.assertEqual(result["reason"], "self_referral")
        self.mock_coin_repo.add_coins.assert_not_called()

    async def test_already_registered_user_prevented(self):
        referrer = User(telegram_id=123, username="referrer_user", referral_code="REF123")
        already_registered_user = User(telegram_id=456, username="old_user")
        
        self.mock_user_repo.get_by_referral_code = AsyncMock(return_value=referrer)
        self.mock_user_repo.get_by_telegram_id = AsyncMock(return_value=already_registered_user)

        result = await self.use_case.execute(new_user_telegram_id=456, referral_code="REF123")
        
        self.assertFalse(result["success"])
        self.assertEqual(result["reason"], "already_registered")
        self.mock_coin_repo.add_coins.assert_not_called()

    async def test_vip_unlock_notification_triggered(self):
        referrer = User(telegram_id=123, username="referrer_user", referral_code="REF123", total_coins=0, has_vip_access=False)
        new_user = User(telegram_id=456, username="new_user", referred_by_id=123, referral_code="REF456")
        updated_referrer = User(telegram_id=123, username="referrer_user", referral_code="REF123", total_coins=5, has_vip_access=True)

        self.mock_user_repo.get_by_referral_code = AsyncMock(return_value=referrer)
        self.mock_user_repo.get_by_telegram_id = AsyncMock(side_effect=lambda tid: None if tid == 456 else updated_referrer)
        self.mock_user_repo.get_or_create_user = AsyncMock(return_value=new_user)
        self.mock_user_repo.grant_vip_access = AsyncMock()
        self.mock_user_repo.get_active_vip_invite_link = AsyncMock(return_value="https://t.me/joinchat/VIPLINK")
        self.mock_vip_notifier.send_vip_unlock_message = AsyncMock()
        self.mock_vip_notifier.notify_new_referral = AsyncMock()

        result = await self.use_case.execute(new_user_telegram_id=456, referral_code="REF123", new_user_username="new_user")
        
        self.assertTrue(result["success"])
        self.assertTrue(result["vip_just_unlocked"])
        self.mock_user_repo.grant_vip_access.assert_called_once_with(123)
        self.mock_vip_notifier.send_vip_unlock_message.assert_called_once_with(123, "https://t.me/joinchat/VIPLINK")
