import csv
from typing import Dict

from django.core.management.base import BaseCommand
from django.db import transaction

from core_backend.models import Company, Contact, Location


def is_empty(string: str) -> bool:
    return string is None or string == '' or string == '0'


class Command(BaseCommand):
    help = 'Imports contacts, locations and companies data from CSV files into the database'

    def add_arguments(self, parser):
        parser.add_argument('--contacts_file', dest='contacts_file', help='Path to the contacts CSV file')
        parser.add_argument('--locations_file', dest='locations_file', help='Path to the locations CSV file')
        parser.add_argument('--companies_file', dest='companies_file', help='Path to the companies CSV file')

    @transaction.atomic
    def handle(self, *args, **kwargs):
        # Contacts
        contacts_file = kwargs['contacts_file']
        if not contacts_file:
            contacts_dict = {}

        else:
            try:
                with open(contacts_file, 'r') as file:
                    contacts_dict = self.create_contacts_from_csv_file(file)
            except FileNotFoundError:
                self.stdout.write(self.style.ERROR(f'File not found at {contacts_file}'))
                raise
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'An error occurred: {str(e)}'))
                raise

        # Locations
        locations_file = kwargs['locations_file']
        if not locations_file:
            locations_dict = {}

        else:
            try:
                with open(locations_file, 'r') as file:
                    locations_dict = self.create_locations_from_csv_file(file)
            except FileNotFoundError:
                self.stdout.write(self.style.ERROR(f'File not found at {locations_file}'))
                raise
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'An error occurred: {str(e)}'))
                raise

        # Companies
        companies_file = kwargs['companies_file']
        if not companies_file:
            self.stdout.write(
                self.style.ERROR(
                    'Please provide the path to the CSV file for companies using --companies_file option'
                )
            )
            return

        try:
            with open(companies_file, 'r') as file:
                self.create_companies_from_csv_file(file, contacts_dict, locations_dict)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'File not found at {companies_file}'))
            raise
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'An error occurred: {str(e)}'))
            raise

        self.stdout.write(self.style.SUCCESS('Successfully imported data from the CSV files'))

    @transaction.atomic
    def create_locations_from_csv_file(self, file) -> Dict[str, Location]:
        count = 0
        duplicate_count = 0
        new_locations = {}
        csv_reader = csv.DictReader(file)

        for row in csv_reader:
            source_id = row['id']
            if is_empty(source_id):
                raise ValueError(F'ID is for location in line {csv_reader.line_num} is empty')
            if source_id in new_locations:
                raise ValueError(F'ID is for location in line {csv_reader.line_num} is not unique')

            contact, created = Location.objects.get_or_create(
                address=row['address'],
                unit_number=row['unit_number'],
                city=row['city'],
                state=row['state'],
                country=row.get('country', 'United States of America'),
                zip=row['zip'],
            )

            new_locations[source_id] = contact

            if created:
                count += 1
            else:
                duplicate_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully imported {count} locations from the CSV file, with {duplicate_count} duplicates detected and merged'
            )
        )

        return new_locations

    @transaction.atomic
    def create_contacts_from_csv_file(self, file) -> Dict[str, Contact]:
        count = 0
        duplicate_count = 0
        new_contacts = {}
        csv_reader = csv.DictReader(file)

        for row in csv_reader:
            source_id = row['id']
            if is_empty(source_id):
                raise ValueError(F'ID is for contact in line {csv_reader.line_num} is empty')
            if source_id in new_contacts:
                raise ValueError(F'ID is for contact in line {csv_reader.line_num} is not unique')

            contact, created = Contact.objects.get_or_create(
                email=row['email'],
                phone=row['phone'],
                fax=row['fax'],
                email_context=row['email_context'],
                phone_context=row['phone_context'],
                fax_context=row['fax_context'],
            )

            new_contacts[source_id] = contact

            if created:
                count += 1
            else:
                duplicate_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully imported {count} contacts from the CSV file, with {duplicate_count} duplicates detected and merged'
            )
        )

        return new_contacts

    @transaction.atomic
    def create_companies_from_csv_file(self, file, contacts_dict: Dict[str, Contact], locations_dict: Dict[str, Location]):
        count = 0
        duplicate_count = 0
        csv_reader = csv.DictReader(file)

        for row in csv_reader:
            # Get contacts
            contact_ids = row['contacts']
            try:
                contacts = [
                    contacts_dict[contact_id]
                    for contact_id in contact_ids.split(',')
                ] if not is_empty(contact_ids) else []
            except KeyError:
                raise ValueError(F'A contact for company in line {csv_reader.line_num} does not exist')

            # Get locations
            location_ids = row['locations']
            try:
                locations = [
                    locations_dict[location_id]
                    for location_id in location_ids.split(',')
                ] if not is_empty(location_ids) else []
            except KeyError:
                raise ValueError(F'A location for company in line {csv_reader.line_num} does not exist')

            # Create
            name = row['name']
            if not name:
                continue
            company_type = row['type'].lower()
            send_method = row['send_method'].lower()
            on_hold = row['on_hold'] == 'Yes'

            company, created = Company.objects.get_or_create(
                name=name,
                type=company_type,
                send_method=send_method,
                on_hold=on_hold,
            )

            company.contacts.add(*contacts)
            company.locations.add(*locations)

            if created:
                count += 1
            else:
                duplicate_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully imported {count} companies from the CSV file, with {duplicate_count} duplicates detected and merged'
            )
        )
