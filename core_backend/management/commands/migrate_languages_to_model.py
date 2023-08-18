from django.core.management import BaseCommand
from django.db import transaction

from core_backend.models import Extra, Language


class Command(BaseCommand):
    help = 'Change all Extra keys to use the new naming convention, then change the value to the new one'

    @transaction.atomic
    def handle(self, *args, **options):
        keys = [
            ('language', 'language_id'),
            ('source_language', 'source_language_id'),
            ('target_language', 'target_language_id'),
        ]

        english = Language.objects.get(name='English')
        french = Language.objects.get(name='French')
        spanish = Language.objects.get(name='Spanish (aka: Castilian)')

        for (old_key, new_key) in keys:
            Extra.objects.filter(key=old_key, value='en').update(key=new_key, value=english.id)
            Extra.objects.filter(key=old_key, value='fr').update(key=new_key, value=french.id)
            Extra.objects.filter(key=old_key, value='es').update(key=new_key, value=spanish.id)

            if unchanged := Extra.objects.filter(key=old_key):
                values = unchanged.distinct('value').values_list('value', flat=True).join(', ')
                self.stdout.write(self.style.ERROR(f'Failed to migrate {old_key}, because of values {values}'))
                raise Exception('Failed to migrate') # Rollback

        self.stdout.write(self.style.SUCCESS('Successfully migrated languages'))
