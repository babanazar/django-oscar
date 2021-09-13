# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import oscar.models.fields.autoslugfield
import django.db.models.deletion
import django.core.validators
import oscar.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AttributeOption',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('option', models.CharField(max_length=255, verbose_name='Option')),
            ],
            options={
                'verbose_name_plural': 'Attribute options',
                'verbose_name': 'Attribute option',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AttributeOptionGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, verbose_name='Name')),
            ],
            options={
                'verbose_name_plural': 'Attribute option groups',
                'verbose_name': 'Attribute option group',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('path', models.CharField(unique=True, max_length=255)),
                ('depth', models.PositiveIntegerField()),
                ('numchild', models.PositiveIntegerField(default=0)),
                ('name', models.CharField(max_length=255, db_index=True, verbose_name='Name')),
                ('description', models.TextField(verbose_name='Description', blank=True)),
                ('image', models.ImageField(upload_to='categories', verbose_name='Image', max_length=255, blank=True, null=True)),
                ('slug', models.SlugField(max_length=255, editable=False, verbose_name='Slug')),
                ('full_name', models.CharField(max_length=255, editable=False, db_index=True, verbose_name='Full Name')),
            ],
            options={
                'ordering': ['full_name'],
                'verbose_name_plural': 'Categories',
                'verbose_name': 'Category',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Option',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, verbose_name='Name')),
                ('code', oscar.models.fields.autoslugfield.AutoSlugField(populate_from='name', unique=True, verbose_name='Code', max_length=128, editable=False, blank=True)),
                ('type', models.CharField(default='Required', max_length=128, verbose_name='Status', choices=[('Required', 'Required - a value for this option must be specified'), ('Optional', 'Optional - a value for this option can be omitted')])),
            ],
            options={
                'verbose_name_plural': 'Options',
                'verbose_name': 'Option',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Service',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('structure', models.CharField(default='standalone', max_length=10, verbose_name='Service structure', choices=[('standalone', 'Stand-alone service'), ('parent', 'Parent service'), ('child', 'Child service')])),
                ('upc', oscar.models.fields.NullCharField(unique=True, verbose_name='UPC', max_length=64, help_text='Universal Service Code (UPC) is an identifier for a service which is not specific to a particular  supplier. Eg an ISBN for a book.')),
                ('title', models.CharField(max_length=255, verbose_name='Title', blank=True)),
                ('slug', models.SlugField(max_length=255, verbose_name='Slug')),
                ('description', models.TextField(verbose_name='Description', blank=True)),
                ('rating', models.FloatField(editable=False, verbose_name='Rating', null=True)),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Date created')),
                ('date_updated', models.DateTimeField(auto_now=True, db_index=True, verbose_name='Date updated')),
                ('is_discountable', models.BooleanField(default=True, verbose_name='Is discountable?', help_text='This flag indicates if this service can be used in an offer or not')),
            ],
            options={
                'ordering': ['-date_created'],
                'verbose_name_plural': 'Services',
                'verbose_name': 'Service',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ServiceAttribute',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, verbose_name='Name')),
                ('code', models.SlugField(max_length=128, verbose_name='Code', validators=[django.core.validators.RegexValidator(regex='^[a-zA-Z\\-_][0-9a-zA-Z\\-_]*$', message="Code can only contain the letters a-z, A-Z, digits, minus and underscores, and can't start with a digit")])),
                ('type', models.CharField(default='text', max_length=20, verbose_name='Type', choices=[('text', 'Text'), ('integer', 'Integer'), ('boolean', 'True / False'), ('float', 'Float'), ('richtext', 'Rich Text'), ('date', 'Date'), ('option', 'Option'), ('entity', 'Entity'), ('file', 'File'), ('image', 'Image')])),
                ('required', models.BooleanField(default=False, verbose_name='Required')),
                ('option_group', models.ForeignKey(null=True, verbose_name='Option Group', help_text='Select an option group if using type "Option"', to='catalogue.AttributeOptionGroup', blank=True, on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ['code'],
                'verbose_name_plural': 'Service attributes',
                'verbose_name': 'Service attribute',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ServiceAttributeValue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value_text', models.TextField(blank=True, verbose_name='Text', null=True)),
                ('value_integer', models.IntegerField(blank=True, verbose_name='Integer', null=True)),
                ('value_boolean', models.NullBooleanField(verbose_name='Boolean')),
                ('value_float', models.FloatField(blank=True, verbose_name='Float', null=True)),
                ('value_richtext', models.TextField(blank=True, verbose_name='Richtext', null=True)),
                ('value_date', models.DateField(blank=True, verbose_name='Date', null=True)),
                ('value_file', models.FileField(upload_to='images/services/%Y/%m/', max_length=255, blank=True, null=True)),
                ('value_image', models.ImageField(upload_to='images/services/%Y/%m/', max_length=255, blank=True, null=True)),
                ('entity_object_id', models.PositiveIntegerField(blank=True, editable=False, null=True)),
                ('attribute', models.ForeignKey(verbose_name='Attribute', to='catalogue.ServiceAttribute', on_delete=models.CASCADE)),
                ('entity_content_type', models.ForeignKey(null=True, editable=False, to='contenttypes.ContentType', blank=True, on_delete=models.CASCADE)),
                ('service', models.ForeignKey(verbose_name='Service', related_name='attribute_values', to='catalogue.Service', on_delete=models.CASCADE)),
                ('value_option', models.ForeignKey(null=True, verbose_name='Value option', to='catalogue.AttributeOption', blank=True, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name_plural': 'Service attribute values',
                'verbose_name': 'Service attribute value',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ServiceCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.ForeignKey(verbose_name='Category', to='catalogue.Category', on_delete=models.CASCADE)),
                ('service', models.ForeignKey(verbose_name='Service', to='catalogue.Service', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ['service', 'category'],
                'verbose_name_plural': 'Service categories',
                'verbose_name': 'Service category',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ServiceClass',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, verbose_name='Name')),
                ('slug', oscar.models.fields.autoslugfield.AutoSlugField(populate_from='name', unique=True, verbose_name='Slug', max_length=128, editable=False, blank=True)),
                ('requires_shipping', models.BooleanField(default=True, verbose_name='Requires shipping?')),
                ('track_stock', models.BooleanField(default=True, verbose_name='Track stock levels?')),
                ('options', models.ManyToManyField(verbose_name='Options', to='catalogue.Option', blank=True)),
            ],
            options={
                'ordering': ['name'],
                'verbose_name_plural': 'Service classes',
                'verbose_name': 'Service class',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ServiceImage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('original', models.ImageField(upload_to='images/services/%Y/%m/', max_length=255, verbose_name='Original')),
                ('caption', models.CharField(max_length=200, verbose_name='Caption', blank=True)),
                ('display_order', models.PositiveIntegerField(default=0, verbose_name='Display order', help_text='An image with a display order of zero will be the primary image for a service')),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Date created')),
                ('service', models.ForeignKey(verbose_name='Service', related_name='images', to='catalogue.Service', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ['display_order'],
                'verbose_name_plural': 'Service images',
                'verbose_name': 'Service image',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ServiceRecommendation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ranking', models.PositiveSmallIntegerField(default=0, verbose_name='Ranking', help_text='Determines order of the services. A service with a higher value will appear before one with a lower ranking.')),
                ('primary', models.ForeignKey(verbose_name='Primary service', related_name='primary_recommendations', to='catalogue.Service', on_delete=models.CASCADE)),
                ('recommendation', models.ForeignKey(verbose_name='Recommended service', to='catalogue.Service', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ['primary', '-ranking'],
                'verbose_name_plural': 'Service recomendations',
                'verbose_name': 'Service recommendation',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='servicerecommendation',
            unique_together=set([('primary', 'recommendation')]),
        ),
        migrations.AlterUniqueTogether(
            name='serviceimage',
            unique_together=set([('service', 'display_order')]),
        ),
        migrations.AlterUniqueTogether(
            name='servicecategory',
            unique_together=set([('service', 'category')]),
        ),
        migrations.AlterUniqueTogether(
            name='serviceattributevalue',
            unique_together=set([('attribute', 'service')]),
        ),
        migrations.AddField(
            model_name='serviceattribute',
            name='service_class',
            field=models.ForeignKey(null=True, verbose_name='Service type', related_name='attributes', to='catalogue.ServiceClass', blank=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='service',
            name='attributes',
            field=models.ManyToManyField(verbose_name='Attributes', help_text='A service attribute is something that this service may have, such as a size, as specified by its class', to='catalogue.ServiceAttribute', through='catalogue.ServiceAttributeValue'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='service',
            name='categories',
            field=models.ManyToManyField(through='catalogue.ServiceCategory', verbose_name='Categories', to='catalogue.Category'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='service',
            name='parent',
            field=models.ForeignKey(null=True, verbose_name='Parent service', related_name='children', help_text="Only choose a parent service if you're creating a child service.  For example if this is a size 4 of a particular t-shirt.  Leave blank if this is a stand-alone service (i.e. there is only one version of this service).", to='catalogue.Service', blank=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='service',
            name='service_class',
            field=models.ForeignKey(verbose_name='Service type', on_delete=django.db.models.deletion.PROTECT, related_name='services', help_text='Choose what type of service this is', to='catalogue.ServiceClass', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='service',
            name='service_options',
            field=models.ManyToManyField(verbose_name='Service options', help_text="Options are values that can be associated with a item when it is added to a customer's basket.  This could be something like a personalised message to be printed on a T-shirt.", to='catalogue.Option', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='service',
            name='recommended_services',
            field=models.ManyToManyField(verbose_name='Recommended services', help_text='These are services that are recommended to accompany the main service.', to='catalogue.Service', through='catalogue.ServiceRecommendation', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='attributeoption',
            name='group',
            field=models.ForeignKey(verbose_name='Group', related_name='options', to='catalogue.AttributeOptionGroup', on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
