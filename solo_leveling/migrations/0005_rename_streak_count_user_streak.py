# Generated by Django 5.1.7 on 2025-03-20 09:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('solo_leveling', '0004_alter_user_rank_dailytask'),
    ]

    operations = [
        migrations.RenameField(
            model_name='user',
            old_name='streak_count',
            new_name='streak',
        ),
    ]
