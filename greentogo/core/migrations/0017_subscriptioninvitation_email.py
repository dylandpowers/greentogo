# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-04-14 15:21
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_subscriptioninvitation'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscriptioninvitation',
            name='email',
            field=models.EmailField(default='user@example.org', max_length=254),
            preserve_default=False,
        ),
    ]