from abc import ABC, abstractmethod

class SettingsRepository(ABC):
    @abstractmethod
    async def get_setting_int(self, key: str, default: int) -> int:
        """
        Get an integer system setting from the database, falling back to default.
        """
        pass
