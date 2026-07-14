from django.contrib import admin
from botapp.models import BotUser, MandatoryChannel, RequestLog
from presentation.admin.admin import CleanBotUserAdmin, CleanMandatoryChannelAdmin, CleanRequestLogAdmin

admin.site.register(BotUser, CleanBotUserAdmin)
admin.site.register(MandatoryChannel, CleanMandatoryChannelAdmin)
admin.site.register(RequestLog, CleanRequestLogAdmin)
