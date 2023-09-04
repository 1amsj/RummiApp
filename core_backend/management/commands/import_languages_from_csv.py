import csv

from django.core.management.base import BaseCommand
from django.db import transaction

from core_backend.models import Language


class Command(BaseCommand):
    help = 'Import languages from a CSV file. A language will be updated if alpha2, alpha3 and english name match.'

    def add_arguments(self, parser):
        parser.add_argument('filepath', help='Path to the CSV file')

    @transaction.atomic
    def handle(self, *args, **kwargs):
        filepath = kwargs['filepath']
        if not filepath:
            self.stdout.write(
                self.style.ERROR(
                    'Please provide the path to the CSV file'
                )
            )
            return

        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                self.create_languages_from_csv_file(file)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'File not found at {filepath}'))
            raise
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'An error occurred: {str(e)}'))
            raise

    @transaction.atomic
    def create_languages_from_csv_file(self, file):
        count = 0
        update_count = 0
        csv_reader = csv.DictReader(file)

        for row in csv_reader:
            alpha2 = row['alpha2']
            alpha3 = row['Key']
            available = row['Show'] == 'TRUE'
            common = row['Common'] == 'TRUE'
            name = row['English Name']
            description = row['English Description']

            language, created = Language.objects.update_or_create(
                alpha3=alpha3,
                name=name,
                defaults={
                    'available': available,
                    'alpha2': alpha2,
                    'common': common,
                    'description': description,
                    'name': name,
                },
            )

            if created:
                count += 1
            else:
                update_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully imported {count} new languages from the CSV file, with {update_count} updated'
            )
        )
