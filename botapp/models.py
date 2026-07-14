from django.db import models


class BotUser(models.Model):
    """Telegram user who interacts with the bot."""

    telegram_id = models.BigIntegerField(unique=True, db_index=True)
    username = models.CharField(max_length=255, null=True, blank=True)
    is_subscribed = models.BooleanField(default=False)
    referred_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='referrals',
        help_text="Foydalanuvchini taklif qilgan boshqa foydalanuvchi"
    )
    referral_code = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        unique=True,
        db_index=True,
        help_text="Foydalanuvchining shaxsiy taklif kodi"
    )
    total_referrals = models.PositiveIntegerField(
        default=0,
        help_text="Jami taklif qilingan do'stlar soni"
    )
    total_coins = models.PositiveIntegerField(
        default=0,
        help_text="Foydalanuvchining umumiy tangalari balansi"
    )
    has_vip_access = models.BooleanField(
        default=False,
        help_text="VIP kanalga kirish ruxsati bor yoki yo'qligi"
    )
    vip_unlocked_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="VIP kanal ruxsati ochilgan sana va vaqt"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Bot User'
        verbose_name_plural = 'Bot Users'
        ordering = ['-created_at']

    def __str__(self):
        return f"@{self.username}" if self.username else f"ID:{self.telegram_id}"


class CoinTransaction(models.Model):
    """Log of coin transactions for auditing."""
    user = models.ForeignKey(
        BotUser,
        on_delete=models.CASCADE,
        related_name='coin_transactions',
        help_text="Tanga olgan yoki sarflagan foydalanuvchi"
    )
    amount = models.IntegerField(help_text="Qo'shilgan (+) yoki ayirilgan (-) tanga miqdori")
    reason = models.CharField(max_length=100, help_text="Tanga tranzaksiyasi sababi")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Coin Transaction'
        verbose_name_plural = 'Coin Transactions'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} -> {self.amount:+d} ({self.reason})"


class VipChannel(models.Model):
    """VIP Channel invite link details."""
    channel_id = models.CharField(max_length=255, help_text="VIP Channel Telegram ID")
    invite_link = models.URLField(help_text="VIP Channel taklif havolasi")
    is_active = models.BooleanField(default=True, help_text="Ushbu taklif havolasi faolmi?")

    class Meta:
        verbose_name = 'VIP Channel'
        verbose_name_plural = 'VIP Channels'

    def __str__(self):
        return f"VIP Channel ID: {self.channel_id}"


class SystemSetting(models.Model):
    """Database-backed dynamic settings configuration."""
    key = models.CharField(max_length=255, unique=True, db_index=True)
    value = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')

    class Meta:
        verbose_name = 'System Setting'
        verbose_name_plural = 'System Settings'

    def __str__(self):
        return f"{self.key} = {self.value}"


class MandatoryChannel(models.Model):
    """Channel that users must subscribe to before using the bot."""

    channel_id = models.CharField(
        max_length=255,
        help_text="Channel ID (e.g., -100xxxx) or username (e.g., @channel_name)",
    )
    channel_link = models.URLField(
        help_text="Public invite link (e.g., https://t.me/channel_name)",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Mandatory Channel'
        verbose_name_plural = 'Mandatory Channels'

    def __str__(self):
        return f"{self.channel_id} ({'active' if self.is_active else 'inactive'})"


class RequestLog(models.Model):
    """Log of hashtag extraction requests."""

    user = models.ForeignKey(
        BotUser,
        on_delete=models.CASCADE,
        related_name='requests',
    )
    instagram_url = models.URLField()
    hashtags_found = models.TextField(
        blank=True,
        default='',
        help_text="Comma-separated list of hashtags found",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Request Log'
        verbose_name_plural = 'Request Logs'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} → {self.instagram_url[:50]}..."
