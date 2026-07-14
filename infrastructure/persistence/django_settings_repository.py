from asgiref.sync import sync_to_async
from application.interfaces.settings_repository import SettingsRepository
from botapp.models import SystemSetting

class DjangoSettingsRepository(SettingsRepository):
    async def get_setting_int(self, key: str, default: int) -> int:
        """
        Fetch setting from Django DB, falling back to default.
        """
        @sync_to_async
        def _get():
            try:
                setting = SystemSetting.objects.get(key=key)
                return int(setting.value)
            except (SystemSetting.DoesNotExist, ValueError):
                return default

        return await _get()
