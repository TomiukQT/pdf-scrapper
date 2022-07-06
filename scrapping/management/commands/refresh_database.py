from django.core.management.base import BaseCommand, CommandError
import scrapper


class Command(BaseCommand):
    help = 'Refresh database of resolutions RMe and ZMe'

    def handle(self, *args, **options):
        scrapper.refresh_data()
        return
