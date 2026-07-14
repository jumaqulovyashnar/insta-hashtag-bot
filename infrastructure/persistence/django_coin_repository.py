from asgiref.sync import sync_to_async
from django.db import transaction
from application.interfaces.coin_repository import CoinRepository
from botapp.models import BotUser, CoinTransaction

class DjangoCoinRepository(CoinRepository):
    async def add_coins(self, telegram_id: int, amount: int, reason: str) -> None:
        """
        Atomically add (or deduct) coins for a user and log a CoinTransaction.
        Uses select_for_update() to prevent race conditions.
        """
        @sync_to_async
        def _add():
            with transaction.atomic():
                try:
                    user = BotUser.objects.select_for_update().get(telegram_id=telegram_id)
                    user.total_coins += amount
                    user.save(update_fields=['total_coins'])
                    
                    CoinTransaction.objects.create(
                        user=user,
                        amount=amount,
                        reason=reason
                    )
                except BotUser.DoesNotExist:
                    pass

        await _add()
