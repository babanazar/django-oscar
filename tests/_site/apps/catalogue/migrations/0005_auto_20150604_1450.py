# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('catalogue', '0004_auto_20150217_1710'),
    ]

    operations = [
        migrations.AlterField(
            model_name='service',
            name='service_class',
            field=models.ForeignKey(related_name='services', on_delete=django.db.models.deletion.PROTECT, blank=True, to='catalogue.ServiceClass', help_text='Choose what type of service this is', null=True, verbose_name='Service type'),
        ),
    ]
