from django.contrib import admin
from botapp.models import BotUser, MandatoryChannel, RequestLog, CoinTransaction, VipChannel, SystemSetting

class CleanBotUserAdmin(admin.ModelAdmin):
    list_display = (
        'telegram_id', 
        'username', 
        'referral_code', 
        'total_coins', 
        'has_vip_access', 
        'is_subscribed', 
        'referred_by', 
        'created_at'
    )
    list_filter = ('is_subscribed', 'has_vip_access', 'created_at')
    search_fields = ('telegram_id', 'username', 'referral_code')
    readonly_fields = ('created_at',)
    raw_id_fields = ('referred_by',)
    list_per_page = 50


class CleanMandatoryChannelAdmin(admin.ModelAdmin):
    list_display = ('channel_id', 'channel_link', 'is_active')
    list_filter = ('is_active',)
    list_editable = ('is_active',)


class CleanRequestLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'instagram_url', 'short_hashtags', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'user__telegram_id', 'instagram_url', 'hashtags_found')
    readonly_fields = ('created_at',)
    list_per_page = 50
    raw_id_fields = ('user',)

    @admin.display(description='Hashtags')
    def short_hashtags(self, obj):
        text = obj.hashtags_found
        return text[:80] + '...' if len(text) > 80 else text


class CoinTransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'reason', 'created_at')
    list_filter = ('reason', 'created_at')
    search_fields = ('user__username', 'user__telegram_id', 'reason')
    readonly_fields = ('created_at',)
    raw_id_fields = ('user',)
    list_per_page = 50


class VipChannelAdmin(admin.ModelAdmin):
    list_display = ('channel_id', 'invite_link', 'is_active')
    list_filter = ('is_active',)
    list_editable = ('is_active',)


class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'description')
    search_fields = ('key', 'value')
    list_editable = ('value',)



