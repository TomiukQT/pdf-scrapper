from django.core.management.base import BaseCommand, CommandError
from scrapping.models import Representative


class Command(BaseCommand):
    help = 'Create Representatives for 2018-2022 period'

    def handle(self, *args, **options):
        res = [
            ('Jitka', 'Pokorná', 'VOLBA PRO NOVOU ROLI...'), ('Hana ', 'Nesybová', 'VOLBA PRO NOVOU ROLI...'),
            ('Jiří', 'Sýkora', 'ČSSD'),
            ('Libor', 'Škarda', 'HN.ZA HARM.ROZVOJ OBCÍ'), ('Václav', 'Bartoň', 'VOLBA PRO NOVOU ROLI...'),
            ('Jan', 'Kvapil', 'VOLBA PRO NOVOU ROLI...'),
            ('Tomáš', 'Pavlíček', 'VOLBA PRO NOVOU ROLI...'), ('Petra', 'Krbcová', 'VOLBA PRO NOVOU ROLI...'),
            ('Ladislav', 'Cinegr', 'SNK Nová Role - Mezirolí'),
            ('Luboš', 'Pastor', 'ODS'), ('Milena', 'Tichá', 'ODS'), ('Karel', 'Švec', 'ODS'),
            ('Miluše', 'Dušková', 'HN.ZA HARM.ROZVOJ OBCÍ'),
            ('Ladislav', 'Slíž', 'ANO 2011'), ('David', 'Niedermertl', 'ANO 2011')
        ]

        for r in res:
            representative = Representative.objects.create()
            representative.name, representative.surname, representative.party = r
            representative.save()
