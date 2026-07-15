from django.db import migrations


def create_mandatory_channel(apps, schema_editor):
    MandatoryChannel = apps.get_model('botapp', 'MandatoryChannel')
    channel_id = '@instagram_chat77'
    channel_link = 'https://t.me/instagram_chat77'

    if not MandatoryChannel.objects.filter(channel_id=channel_id).exists():
        MandatoryChannel.objects.create(
            channel_id=channel_id,
            channel_link=channel_link,
            is_active=True,
        )


def reverse_create_mandatory_channel(apps, schema_editor):
    MandatoryChannel = apps.get_model('botapp', 'MandatoryChannel')
    MandatoryChannel.objects.filter(channel_id='@instagram_chat77').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('botapp', '0004_botuser_total_referrals'),
    ]

    operations = [
        migrations.RunPython(create_mandatory_channel, reverse_create_mandatory_channel),
    ]
