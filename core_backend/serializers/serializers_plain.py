from typing import List

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from core_backend.models import Business, Category, Company, CompanyRelationship, Contact, Expense, Extra, Location, Note, User
from core_backend.serializers.serializers_utils import BaseSerializer, generic_serializer
from core_backend.services.core_services import fetch_updated_from_validated_data

BusinessSerializer = generic_serializer(Business)


class CategorySerializer(generic_serializer(Category)):
    class Meta:
        model = Category
        fields = '__all__'

    @staticmethod
    def get_default_queryset():
        return Category.objects.all().not_deleted()


class ContactSerializer(BaseSerializer):
    phone_extension = serializers.SerializerMethodField('get_phone_extension')

    class Meta:
        model = Contact
        fields = '__all__'

    def validate(self, data: dict):
        if not (data.get('email') or data.get('phone') or data.get('fax')):
            raise serializers.ValidationError(_('Contact data can not be empty'))

        return super(ContactSerializer, self).validate(data)

    @staticmethod
    def get_default_queryset():
        return Contact.objects.all().not_deleted()

    # noinspection PyMethodMayBeStatic
    def get_phone_extension(self, contact_instance):
        if contact_instance.phone:
            return contact_instance.phone.extension
        else:
            return ""

    @staticmethod
    def create_instances(contact_dicts: List[dict]):
        contact_instances = [Contact(**contact_data) for contact_data in contact_dicts]
        return Contact.objects.bulk_create(contact_instances)

    @staticmethod
    def sync_contacts(instance, contacts_data: List[dict]):
        created_contacts, updated_contacts, deleted_contacts = fetch_updated_from_validated_data(
            Contact,
            contacts_data,
            set(instance.contacts.all().values_list('id')))

        # Create
        if created_contacts:
            created_contacts = Contact.objects.bulk_create(created_contacts)
            instance.contacts.add(*created_contacts)

        # Update
        if updated_contacts:
            Contact.objects.bulk_update(
                updated_contacts,
                ['phone', 'phone_context', 'email', 'email_context', 'fax', 'fax_context']
            )

        # Delete
        Contact.objects.filter(id__in=deleted_contacts).delete()


class ContactUnsafeSerializer(ContactSerializer):
    id = serializers.IntegerField(read_only=False, allow_null=True, required=False)


class ExpenseSerializer(generic_serializer(Expense)):
    booking_id = serializers.PrimaryKeyRelatedField(read_only=True, source='booking')

    class Meta:
        model = Expense
        fields = '__all__'

    @staticmethod
    def get_default_queryset():
        return Expense.objects.all().not_deleted()


class ExtraAttrSerializer(BaseSerializer):
    class Meta:
        model = Extra
        fields = ('key', 'value')

    @staticmethod
    def get_default_queryset():
        return Extra.objects.all().not_deleted()


class LocationSerializer(BaseSerializer):
    class Meta:
        model = Location
        fields = '__all__'

    @staticmethod
    def get_default_queryset():
        return Location.objects.all().not_deleted()

    @staticmethod
    def create_instances(location_dicts: List[dict]):
        location_instances = [Location(**location_data) for location_data in location_dicts]
        return Location.objects.bulk_create(location_instances)

    @staticmethod
    def sync_locations(instance, locations_data: List[dict]):
        created_locations, updated_locations, deleted_locations = fetch_updated_from_validated_data(
            Location,
            locations_data,
            set(instance.locations.all().values_list('id'))
        )

        # Create
        if created_locations:
            created_locations = Location.objects.bulk_create(created_locations)
            instance.locations.add(*created_locations)

        # Update
        if updated_locations:
            Location.objects.bulk_update(
                updated_locations,
                ['address', 'city', 'state', 'country', 'zip']
            )

        # Delete
        Location.objects.filter(id__in=deleted_locations).delete()


class LocationUnsafeSerializer(LocationSerializer):
    id = serializers.IntegerField(read_only=False, allow_null=True, required=False)


class NoteSerializer(BaseSerializer):
    created_by = serializers.PrimaryKeyRelatedField(required=False, allow_null=True, queryset=User.objects.all())
    created_by_first_name = serializers.CharField(read_only=True, source='created_by.first_name')
    created_by_last_name = serializers.CharField(read_only=True, source='created_by.last_name')
    text = serializers.CharField(required=True, allow_blank=True)

    class Meta:
        model = Note
        fields = '__all__'

    @staticmethod
    def get_default_queryset():
        return Note.objects.all().not_deleted()

    @staticmethod
    def build_model_instance(data: dict):
        return Note(
            created_by=data.get('created_by', None),
            text=data['text'],
        )

    @staticmethod
    def create_instances(note_dicts: List[dict]):
        note_instances = [NoteSerializer.build_model_instance(note_data) for note_data in note_dicts]
        return Note.objects.bulk_create(note_instances)

    @staticmethod
    def sync_notes(instance, notes_data: List[dict]):
        created_notes, updated_notes, deleted_notes = fetch_updated_from_validated_data(
            Note,
            notes_data,
            set(instance.notes.all().not_deleted().values_list('id'))
        )

        # Create
        if created_notes:
            created_notes = Note.objects.bulk_create(created_notes)
            instance.notes.add(*created_notes)

        # Update
        if updated_notes:
            Note.objects.bulk_update(updated_notes, ['text'])

        # Delete
        Note.objects.filter(id__in=deleted_notes).delete()


class NoteUnsafeSerializer(NoteSerializer):
    id = serializers.IntegerField(read_only=False, allow_null=True, required=False)

class CompanyRelationshipSerializer(BaseSerializer):
    company_to = serializers.PrimaryKeyRelatedField(required=False, allow_null=True, queryset=Company.objects.all())
    company_from = serializers.PrimaryKeyRelatedField(required=False, allow_null=True, queryset=Company.objects.all())
    relationship = serializers.CharField(required=True, allow_blank=True)
    class Meta:
        model = CompanyRelationship
        fields = '__all__'

    @staticmethod
    def get_default_queryset():
        return CompanyRelationship.objects.all().not_deleted()

    @staticmethod
    def build_model_instance(data: dict):
        return CompanyRelationship(
            company = data['company'],
            company_relationships = data['company_relationships'],
        )

    @staticmethod
    def create_instances(company_relationship_dicts: List[dict]):
        company_relationship_instances = [CompanyRelationshipSerializer.build_model_instance(company_relationship_data) for company_relationship_data in company_relationship_dicts]
        return CompanyRelationship.objects.bulk_create(company_relationship_instances)
   
    @staticmethod
    def sync_company_relationships(instance, company_relationships_data: List[dict]):
        created_company_relationships, updated_company_relationships, deleted_company_relationships = fetch_updated_from_validated_data(
            CompanyRelationship,
            company_relationships_data,
            set(instance.company_relationships.all().values_list('id'))
        )

        # Create
        if created_company_relationships:
            created_company_relationships = CompanyRelationship.objects.bulk_create(created_company_relationships)
            instance.company_relationships.add(*created_company_relationships)

        # Update
        if updated_company_relationships:
            CompanyRelationship.objects.bulk_update(updated_company_relationships, ['company_relationships'])

        # Delete
        CompanyRelationship.objects.filter(id__in=deleted_company_relationships).delete()

