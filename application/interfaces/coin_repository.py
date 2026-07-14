from abc import ABC, abstractmethod

class CoinRepository(ABC):
    @abstractmethod
    async def add_coins(self, telegram_id: int, amount: int, reason: str) -> None:
        """
        Add (or deduct) coins for a user and record a CoinTransaction.
        """
        pass
