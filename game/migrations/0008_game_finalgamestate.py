# Generated by Django 4.0.3 on 2022-04-17 09:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0007_alter_player_color'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='finalGameState',
            field=models.BinaryField(blank=True, null=True),
        ),
    ]