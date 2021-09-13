# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('analytics', '0001_initial'),
        ('catalogue', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='userserviceview',
            name='service',
            field=models.ForeignKey(verbose_name='Service', to='catalogue.Service', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='userserviceview',
            name='user',
            field=models.ForeignKey(verbose_name='User', to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='servicerecord',
            name='service',
            field=models.OneToOneField(verbose_name='Service', related_name='stats', to='catalogue.Service',
                                       on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
