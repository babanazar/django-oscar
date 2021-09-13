# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand

from oscar.core.loading import get_model

Service = get_model('catalogue', 'Service')


class Command(BaseCommand):
    help = """Update the denormalised reviews average on all Service instances.
              Should only be necessary when changing to e.g. a weight-based
              rating."""

    def handle(self, *args, **options):
        # Iterate over all Services (not just ones with reviews)
        services = Service.objects.all()
        for service in services:
            service.update_rating()
        self.stdout.write(
            'Successfully updated %s services\n' % services.count())
