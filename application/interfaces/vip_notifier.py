from abc import ABC, abstractmethod

class VipNotifier(ABC):
    @abstractmethod
    async def send_vip_unlock_message(self, telegram_id: int, invite_link: str) -> None:
        """
        Send VIP unlock notification message with invite link to user on Telegram.
        """
        pass

    @abstractmethod
    async def notify_new_referral(
        self, 
        referrer_telegram_id: int, 
        referred_username: str | None, 
        coins_earned: int, 
        total_coins: int
    ) -> None:
        """
        Notify the referrer that someone joined via their link and they earned coins.
        """
        pass
