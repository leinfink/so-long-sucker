# Generated by Django 4.0.3 on 2022-04-10 16:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0005_player_color'),
    ]

    operations = [
        migrations.AlterField(
            model_name='player',
            name='color',
            field=models.IntegerField(default=0, unique=True),
        ),
    ]