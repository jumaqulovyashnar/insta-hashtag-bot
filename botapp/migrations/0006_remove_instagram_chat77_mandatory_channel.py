from django.db import migrations


def remove_mandatory_channel(apps, schema_editor):
    MandatoryChannel = apps.get_model('botapp', 'MandatoryChannel')
    MandatoryChannel.objects.filter(channel_id='@instagram_chat77').delete()


def restore_mandatory_channel(apps, schema_editor):
    MandatoryChannel = apps.get_model('botapp', 'MandatoryChannel')
    if not MandatoryChannel.objects.filter(channel_id='@instagram_chat77').exists():
        MandatoryChannel.objects.create(
            channel_id='@instagram_chat77',
            channel_link='https://t.me/instagram_chat77',
            is_active=True,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('botapp', '0005_add_instagram_chat77_mandatory_channel'),
    ]

    operations = [
        migrations.RunPython(remove_mandatory_channel, restore_mandatory_channel),
    ]
