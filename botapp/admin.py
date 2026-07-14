from django.contrib import admin
from botapp.models import BotUser, MandatoryChannel, RequestLog, CoinTransaction, VipChannel, SystemSetting
from presentation.admin.admin import (
    CleanBotUserAdmin, 
    CleanMandatoryChannelAdmin, 
    CleanRequestLogAdmin,
    CoinTransactionAdmin,
    VipChannelAdmin,
    SystemSettingAdmin
)

admin.site.register(BotUser, CleanBotUserAdmin)
admin.site.register(MandatoryChannel, CleanMandatoryChannelAdmin)
admin.site.register(RequestLog, CleanRequestLogAdmin)
admin.site.register(CoinTransaction, CoinTransactionAdmin)
admin.site.register(VipChannel, VipChannelAdmin)
admin.site.register(SystemSetting, SystemSettingAdmin)
