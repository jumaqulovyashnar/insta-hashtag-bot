from domain.entities.user import User
from application.interfaces.user_repository import UserRepository

class RegisterUserUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, telegram_id: int, username: str | None = None, referred_by_id: int | None = None) -> User:
        """Register the user in the database if not present."""
        return await self.user_repository.get_or_create_user(telegram_id, username, referred_by_id)
