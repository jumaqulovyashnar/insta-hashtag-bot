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
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Bot User'
        verbose_name_plural = 'Bot Users'
        ordering = ['-created_at']

    def __str__(self):
        return f"@{self.username}" if self.username else f"ID:{self.telegram_id}"


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
