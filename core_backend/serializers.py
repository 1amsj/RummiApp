from typing import List, Type

from django.contrib.auth.password_validation import validate_password
from django.db import models
from django.db.models import Prefetch
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from core_backend.models import Affiliation, Agent, Booking, Business, Category, Company, Contact, Event, \
    Expense, ExtendableModel, Extra, Invoice, Ledger, Location, Note, Offer, Operator, Payer, Provider, Recipient, Requester, \
    Service, ServiceRoot, SoftDeletableModel, SoftDeletionQuerySet, User
from core_backend.services import assert_extendable, fetch_updated_from_validated_data, get_model_field_names, \
    is_extendable, manage_extra_attrs, sync_m2m, user_sync_email_with_contact


class BaseSerializer(serializers.ModelSerializer):
    @staticmethod
    def get_default_queryset() -> SoftDeletionQuerySet:
        pass  # This is to avoid the warning in children: Class X must implement all abstract methods
        raise NotImplementedError


# Extra serializers
class ExtraAttrSerializer(BaseSerializer):
    class Meta:
        model = Extra
        fields = ('key', 'value')

    @staticmethod
    def get_default_queryset():
        return Extra.objects.all().not_deleted()


def extendable_serializer(serializer_model: Type[models.Model], serializer_fields='__all__'):
    assert_extendable(serializer_model)

    class ExtendableSerializer(BaseSerializer):
        extra = serializers.SerializerMethodField('get_extra_attrs')

        class Meta:
            model = serializer_model
            fields = serializer_fields
            abstract = True

        def get_extra_attrs(self, obj: ExtendableModel):
            assert_extendable(obj.__class__)
            business = self.context.get('business')
            return obj.get_extra_attrs(business)

        def to_representation(self, instance):
            """Flatten extra fields"""
            representation = super().to_representation(instance)
            extra_representation = representation.pop('extra', {})
            for k in extra_representation:
                representation[k] = extra_representation[k]
            return representation

        def to_internal_value(self, data: dict):
            model_fields = get_model_field_names(serializer_model)
            ser_fields = self.get_fields().keys()
            extra_fields = {}
            for k in list(data.keys()):
                if k in model_fields or k in ser_fields:
                    continue
                extra_fields[k] = data.pop(k)
            data = super(ExtendableSerializer, self).to_internal_value(data)
            data['extra'] = extra_fields  # TODO validate here rules regarding extra fields
            return data

    return ExtendableSerializer


# Helper
def generic_serializer(serializer_model: Type[models.Model], serializer_fields='__all__') -> Type[BaseSerializer]:
    parent_serializer = (
        extendable_serializer(serializer_model)
        if is_extendable(serializer_model)
        else BaseSerializer
    )

    class GenericSerializer(parent_serializer):
        class Meta:
            model = serializer_model
            fields = serializer_fields

    return GenericSerializer


# Custom fields
class BusinessField(serializers.RelatedField):
    default_error_messages = {
        'required': _('This field is required.'),
        'does_not_exist': _('Invalid business name "{name}".'),
        'incorrect_type': _('Incorrect type. Expected id, string or Business, received {data_type}.'),
    }

    def __init__(self, **kwargs):
        try:
            qs = kwargs.pop('queryset', Business.objects.all())
            super(BusinessField, self).__init__(queryset=qs, **kwargs)
        except AssertionError:
            super(BusinessField, self).__init__(**kwargs)

    def to_internal_value(self, data):
        try:
            if isinstance(data, str):
                return Business.objects.get(name=data)
            if isinstance(data, int):
                return Business.objects.get(id=data)
            if isinstance(data, Business):
                return data
            raise TypeError

        except Business.DoesNotExist:
            self.fail('does_not_exist', name=data)

        except (TypeError, ValueError):
            self.fail('incorrect_type', data_type=type(data).__name__)

    def to_representation(self, value):
        return super(BusinessField, self).to_representation(value)


# General serializers
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
    
    def get_phone_extension(self, contact_instance):
        if (contact_instance.phone):
            return contact_instance.phone.extension
        else:
            return ""


class ContactUnsafeSerializer(ContactSerializer):
    id = serializers.IntegerField(read_only=False, allow_null=True, required=False)


class LocationSerializer(BaseSerializer):
    class Meta:
        model = Location
        fields = '__all__'

    @staticmethod
    def get_default_queryset():
        return Location.objects.all().not_deleted()


class LocationUnsafeSerializer(LocationSerializer):
    id = serializers.IntegerField(read_only=False, allow_null=True, required=False)


class CategorySerializer(generic_serializer(Category)):
    class Meta:
        model = Category
        fields = '__all__'

    @staticmethod
    def get_default_queryset():
        return Category.objects.all().not_deleted()


class CategoryCreateSerializer(CategorySerializer):
    def create(self, validated_data=None) -> int:
        data: dict = validated_data or self.validated_data
        company = Category.objects.create(**data)
        return company.id

    def update(self, instance: Category, validated_data=None):
        data: dict = validated_data or self.validated_data
        for (k, v) in data.items():
            setattr(instance, k, v)
        instance.save()


class NoteSerializer(BaseSerializer):
    created_by = serializers.PrimaryKeyRelatedField(required=True, queryset=User.objects.all())
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
            created_by=data['created_by'],
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


class NoteCreateSerializer(NoteSerializer):
    def create(self, validated_data=None) -> int:
        data: dict = validated_data or self.validated_data

        note = Note.objects.create(**data)

        return note.id


# User serializers
class UserSerializer(BaseSerializer):
    id = serializers.ReadOnlyField()
    user_id = serializers.ReadOnlyField(source='id')
    contacts = ContactSerializer(many=True)
    location = LocationSerializer(required=False, allow_null=True)
    agents_id = serializers.PrimaryKeyRelatedField(many=True, allow_null=True, read_only=True, source='as_agents')
    operator_id = serializers.PrimaryKeyRelatedField(allow_null=True, read_only=True, source='as_operator')
    payer_id = serializers.PrimaryKeyRelatedField(allow_null=True, read_only=True, source='as_payer')
    provider_id = serializers.PrimaryKeyRelatedField(allow_null=True, read_only=True, source='as_provider')
    recipient_id = serializers.PrimaryKeyRelatedField(allow_null=True, read_only=True, source='as_recipient')
    requester_id = serializers.PrimaryKeyRelatedField(allow_null=True, read_only=True, source='as_requester')
    date_of_birth = serializers.DateField(required=False)

    class Meta:
        model = User
        fields = (
            'id',
            'user_id',
            'username',
            'email',
            'first_name',
            'last_name',
            'national_id',
            'ssn',
            'date_of_birth',
            'title',
            'suffix',
            'contacts',
            'location',
            'agents_id',
            'operator_id',
            'payer_id',
            'provider_id',
            'recipient_id',
            'requester_id',
            'is_operator',
            'is_provider',
            'is_recipient',
            'is_requester',
            'is_payer',
        )

    @staticmethod
    def get_default_queryset():
        return (
            User.objects
                .all()
                .not_deleted()
                .prefetch_related(
                    Prefetch(
                        'contacts',
                        queryset=ContactSerializer.get_default_queryset(),
                    ),
                    Prefetch(
                        'location',
                        queryset=LocationSerializer.get_default_queryset(),
                    )
                )
        )


class UserCreateSerializer(UserSerializer):
    password = serializers.CharField(
        write_only=True, required=False, allow_blank=True, validators=[validate_password])
    confirmation = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'first_name',
            'last_name',
            'national_id',
            'ssn',
            'date_of_birth',
            'title',
            'suffix',
            'contacts',
            'location',
            'password',
            'confirmation',
        )

    def validate(self, attrs):
        password = attrs.get('password')
        confirmation = attrs.get('confirmation')
        if (password or confirmation) and password != confirmation:
            raise serializers.ValidationError({"confirmation": "Password fields didn't match."})
        return attrs

    def create(self, validated_data=None):
        data: dict = validated_data or self.validated_data
        password = data.pop('password', None)
        data.pop('confirmation', None)
        contacts_data = data.pop('contacts', None)
        location_data = data.pop('location', None)

        user = User.objects.create(**data)
        if password:
            user.set_password(password)
            user.save()

        if contacts_data:
            contacts = [Contact(**d) for d in contacts_data]
            contact_ids = [c.id for c in Contact.objects.bulk_create(contacts)]
            user.contacts.add(*contact_ids)

        if location_data:
            user.location = Location.objects.create(**location_data)
            user.save()

        user_sync_email_with_contact(user)

        return user


class UserUpdateSerializer(UserCreateSerializer):
    contacts = ContactUnsafeSerializer(many=True, required=False)
    username = serializers.ReadOnlyField()

    def update(self, instance: User, validated_data=None):
        data: dict = validated_data or self.validated_data

        password = data.pop('password', None)
        data.pop('confirmation', None)
        
        if password:
            instance.set_password(password)
            instance.save()

        contacts_data = data.pop('contacts', [])

        created_contacts, updated_contacts, deleted_contacts = fetch_updated_from_validated_data(Contact, contacts_data, set(instance.contacts.all().values_list('id')))

        # Create
        if created_contacts:
            created_contacts = Contact.objects.bulk_create(created_contacts)
            instance.contacts.add(*created_contacts)

        # Update
        if updated_contacts:
            Contact.objects.bulk_update(updated_contacts, ['phone', 'phone_context', 'email', 'email_context', 'fax', 'fax_context'])

        # Delete
        for id in deleted_contacts:
            Contact.objects.filter(id=id).delete()

        if (
            (new_email := data.get('email'))
            and new_email != instance.email
            and (contact := instance.contacts.filter(email=instance.email).first())
        ):
            contact.email = new_email
            contact.save()

        location_data = data.pop('location', None)

        if location_data:
            location = instance.location

            if location:
                for (k, v) in location_data.items():
                    setattr(location, k, v)
            
                location.save()

            else:
                instance.location = Location.objects.create(**location_data)

        for (k, v) in data.items():
            setattr(instance, k, v)
        
        instance.save()

        user_sync_email_with_contact(instance)


def user_subtype_serializer(serializer_model: Type[SoftDeletableModel]) -> Type[BaseSerializer]:
    serializer_parent = (
        extendable_serializer(serializer_model)
        if is_extendable(serializer_model)
        else BaseSerializer
    )

    class UserSubTypeSerializer(serializer_parent):
        user = UserSerializer()

        class Meta:
            model = serializer_model
            fields = '__all__'

        def to_representation(self, instance):
            """Flatten user fields"""
            representation = super().to_representation(instance)
            user_representation = representation.pop('user')
            for k in user_representation:
                key = k if k != 'id' else 'user_id'
                representation[key] = user_representation[k]
            return representation

    return UserSubTypeSerializer


class PayerBaseSerializer(user_subtype_serializer(Payer)):
    notes = NoteSerializer(many=True, default=[])

    @staticmethod
    def get_default_queryset():
        return (
            Payer.objects
                .all()
                .not_deleted('user')
                .prefetch_related(
                    Prefetch(
                        'notes',
                        queryset=NoteSerializer.get_default_queryset()
                    ),
                    Prefetch(
                        'user',
                        queryset=UserSerializer.get_default_queryset(),
                    ),
                )
        )


class BaseCompanySerializer(BaseSerializer):
    contacts = ContactSerializer(many=True)
    locations = LocationSerializer(many=True)
    notes = NoteSerializer(many=True, default=[])

    class Meta:
        model = Company
        fields = '__all__'

    @staticmethod
    def get_default_queryset():
        return (
            Company.objects
                .all()
                .not_deleted()
                .prefetch_related(
                    Prefetch(
                        'contacts',
                        queryset=Contact.objects.all().not_deleted(),
                    ),
                    Prefetch(
                        'locations',
                        queryset=Location.objects.all().not_deleted(),
                    ),
                    Prefetch(
                        'notes',
                        queryset=NoteSerializer.get_default_queryset()
                    ),
                )
        )


class CompanySerializer(BaseCompanySerializer):
    parent_company = BaseCompanySerializer()


class CompanyCreateSerializer(CompanySerializer):
    parent_company = serializers.PrimaryKeyRelatedField(queryset=Company.objects.all(), required=False, allow_null=True)
    agents = serializers.PrimaryKeyRelatedField(many=True, default=[], queryset=Agent.objects.all())
    operators = serializers.PrimaryKeyRelatedField(many=True, default=[], queryset=Operator.objects.all())
    payers = serializers.PrimaryKeyRelatedField(many=True, default=[], queryset=Payer.objects.all())
    providers = serializers.PrimaryKeyRelatedField(many=True, default=[], queryset=Provider.objects.all())
    recipients = serializers.PrimaryKeyRelatedField(many=True, default=[], queryset=Recipient.objects.all())
    requesters = serializers.PrimaryKeyRelatedField(many=True, default=[], queryset=Requester.objects.all())
    notes = NoteSerializer(many=True, default=[])

    def create(self, validated_data=None) -> int:
        data: dict = validated_data or self.validated_data

        parent_company = data.get('parent_company', None)

        contacts_data = data.pop('contacts', None)
        locations_data = data.pop('locations', None)
        notes_data = data.pop('notes', [])

        agents_data = data.pop('agents', None)
        operators_data = data.pop('operators', None)
        payers_data = data.pop('payers', None)
        providers_data = data.pop('providers', None)
        recipients_data = data.pop('recipients', None)
        requesters_data = data.pop('requesters', None)

        company = Company.objects.create(**data)

        if agents_data is not None:
            company.agents.set(agents_data)
        if operators_data is not None:
            company.operators.set(operators_data)
        if payers_data is not None:
            company.payers.set(payers_data)
        if providers_data is not None:
            company.providers.set(providers_data)
        if recipients_data is not None:
            company.recipients.set(recipients_data)
        if requesters_data is not None:
            company.requesters.set(requesters_data)

        if contacts_data:
            contacts = [Contact(**d) for d in contacts_data]
            contact_ids = [c.id for c in Contact.objects.bulk_create(contacts)]
            company.contacts.add(*contact_ids)

        if locations_data:
            locations = [Location(**d) for d in locations_data]
            location_ids = [c.id for c in Location.objects.bulk_create(locations)]
            company.locations.add(*location_ids)

        if notes_data:
            note_instances = NoteSerializer.create_instances(notes_data)
            company.notes.add(*note_instances)

        return company.id


class CompanyUpdateSerializer(CompanySerializer):
    contacts = ContactUnsafeSerializer(many=True)
    locations = LocationUnsafeSerializer(many=True)
    notes = NoteUnsafeSerializer(many=True, default=[])
    parent_company = serializers.PrimaryKeyRelatedField(queryset=Company.objects.all(), required=False, allow_null=True)
    name = serializers.CharField()
    agents = serializers.PrimaryKeyRelatedField(many=True, required=False, queryset=Agent.objects.all())
    operators = serializers.PrimaryKeyRelatedField(many=True, required=False, queryset=Operator.objects.all())
    payers = serializers.PrimaryKeyRelatedField(many=True, required=False, queryset=Payer.objects.all())
    providers = serializers.PrimaryKeyRelatedField(many=True, required=False, queryset=Provider.objects.all())
    recipients = serializers.PrimaryKeyRelatedField(many=True, required=False, queryset=Recipient.objects.all())
    requesters = serializers.PrimaryKeyRelatedField(many=True, required=False, queryset=Requester.objects.all())

    def update(self, instance: Company, validated_data=None):
        data: dict = validated_data or self.validated_data

        agents_data = data.pop('agents', None)
        operators_data = data.pop('operators', None)
        payers_data = data.pop('payers', None)
        providers_data = data.pop('providers', None)
        recipients_data = data.pop('recipients', None)
        requesters_data = data.pop('requesters', None)

        if agents_data is not None:
            instance.agents.set(agents_data)
        if operators_data is not None:
            instance.operators.set(operators_data)
        if payers_data is not None:
            instance.payers.set(payers_data)
        if providers_data is not None:
            instance.providers.set(providers_data)
        if recipients_data is not None:
            instance.recipients.set(recipients_data)
        if requesters_data is not None:
            instance.requesters.set(requesters_data)

        contacts_data = data.pop('contacts')

        created_contacts, updated_contacts, deleted_contacts = fetch_updated_from_validated_data(Contact, contacts_data,
                                                                                                 set(instance.contacts.all().values_list(
                                                                                                     'id')))

        # Create
        if created_contacts:
            created_contacts = Contact.objects.bulk_create(created_contacts)
            instance.contacts.add(*created_contacts)

        # Update
        if updated_contacts:
            Contact.objects.bulk_update(updated_contacts,
                                        ['phone', 'phone_context', 'email', 'email_context', 'fax', 'fax_context'])

        # Delete
        for id in deleted_contacts:
            Contact.objects.filter(id=id).delete()

        locations_data = data.pop('locations')

        created_locations, updated_locations, deleted_locations = fetch_updated_from_validated_data(Location,
                                                                                                    locations_data,
                                                                                                    set(instance.locations.all().values_list(
                                                                                                        'id')))

        # Create
        if created_locations:
            created_locations = Location.objects.bulk_create(created_locations)
            instance.locations.add(*created_locations)

        # Update
        if updated_locations:
            Location.objects.bulk_update(updated_locations, ['address', 'city', 'state', 'country', 'zip'])

        # Delete
        for id in deleted_locations:
            Location.objects.filter(id=id).delete()

        notes_data = data.pop('notes')

        NoteSerializer.sync_notes(instance, notes_data)

        for (k, v) in data.items():
            setattr(instance, k, v)

        instance.save()


# Roles serializers
class AgentSerializer(user_subtype_serializer(Agent)):
    companies = CompanySerializer(many=True)
    role = serializers.CharField()

    @staticmethod
    def get_default_queryset():
        return (
            Agent.objects
                .all()
                .not_deleted('user')
                .prefetch_related(
                    Prefetch(
                        'companies',
                        queryset=CompanySerializer.get_default_queryset()
                    ),
                    Prefetch(
                        'extra',
                        queryset=ExtraAttrSerializer.get_default_queryset(),
                    ),
                    Prefetch(
                        'user',
                        queryset=UserSerializer.get_default_queryset(),
                    ),
                )
        )

class AgentCreateSerializer(AgentSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    companies = serializers.PrimaryKeyRelatedField(many = True, queryset=Company.objects.all())
    role = serializers.CharField()

    def create(self, business_name, validated_data=None):
        data = validated_data or self.validated_data
        extras = data.pop('extra', {})
        companies_data = data.pop('companies', None)
        agent = Agent.objects.create(**data)
        if companies_data:
            agent.companies.add(*companies_data)
        manage_extra_attrs(business_name, agent, extras)
        return agent


class OperatorSerializer(user_subtype_serializer(Operator)):
    companies = CompanySerializer(many=True)

    @staticmethod
    def get_default_queryset():
        return (
            Operator.objects
                .all()
                .not_deleted('user')
                .prefetch_related(
                    Prefetch(
                        'companies',
                        queryset= CompanySerializer.get_default_queryset()
                    ),
                    Prefetch(
                        'user',
                        queryset=UserSerializer.get_default_queryset(),
                    ),
                )
        )


class PayerSerializer(PayerBaseSerializer):
    companies = CompanySerializer(many=True)

    @staticmethod
    def get_default_queryset():
        return (
            super(PayerSerializer, PayerSerializer)
                .get_default_queryset()
                .prefetch_related(
                    Prefetch(
                        'companies',
                        queryset= CompanySerializer.get_default_queryset()
                    ),
                )
        )

class PayerCreateSerializer(PayerSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    companies = serializers.PrimaryKeyRelatedField(many=True, queryset=Company.objects.all())

    def create(self, validated_data=None):
        data = validated_data or self.validated_data
        companies_data = data.pop('companies', None)
        notes_data = data.pop('notes', None)
        payer = Payer.objects.create(**data)
        if companies_data:
            payer.companies.add(*companies_data)
        if notes_data:
            payer.notes.add(*notes_data)
        return payer


class ServiceRootBaseSerializer(generic_serializer(ServiceRoot)):
    bookings = serializers.PrimaryKeyRelatedField(queryset=Booking.objects.all(), many=True)
    categories = CategorySerializer(many=True)
    services = serializers.PrimaryKeyRelatedField(queryset=Service.objects.all(), many=True)

    class Meta:
        model = ServiceRoot
        fields = '__all__'

    @staticmethod
    def get_default_queryset():
        return (
            ServiceRoot.objects
                .all()
                .not_deleted()
                .prefetch_related(
                    Prefetch(
                        'bookings',
                        queryset=Booking.objects.all().not_deleted('business'),
                    ),
                    Prefetch(
                        'categories',
                        queryset=CategorySerializer.get_default_queryset(),
                    ),
                    Prefetch(
                        'services',
                        queryset=Service.objects.all().not_deleted('business'),
                    ),
                )
        )


class ServiceNoProviderSerializer(extendable_serializer(Service)):
    root = ServiceRootBaseSerializer(required=False)
    bill_amount = serializers.DecimalField(max_digits=32, decimal_places=2)
    bill_rate = serializers.IntegerField()

    class Meta:
        model = Service
        fields = '__all__'

    def validate(self, data: dict):
        if data.get('bill_amount') < 0:
            raise serializers.ValidationError(_('Bill amount could not be negative'))

        return super(ServiceNoProviderSerializer, self).validate(data)

    @staticmethod
    def get_default_queryset():
        return (
            Service.objects
                .all()
                .not_deleted('business')
                .prefetch_related(
                    Prefetch(
                        'extra',
                        queryset=ExtraAttrSerializer.get_default_queryset(),
                    ),
                    Prefetch(
                        'root',
                        queryset=ServiceRootBaseSerializer.get_default_queryset(),
                    )
                )
        )


class ProviderSerializer(user_subtype_serializer(Provider)):
    companies = CompanySerializer(many=True)
    services = ServiceNoProviderSerializer(many=True)
    notes = NoteSerializer(many=True, default=[])

    class Meta:
        model = Provider
        fields = '__all__'

    @staticmethod
    def get_default_queryset():
        return (
            Provider.objects
            .all()
            .not_deleted('user')
            .prefetch_related(
                Prefetch(
                    'companies',
                    queryset= CompanySerializer.get_default_queryset()
                ),
                Prefetch(
                    'notes',
                    queryset=NoteSerializer.get_default_queryset()
                ),
                Prefetch(
                    'extra',
                    queryset=ExtraAttrSerializer.get_default_queryset(),
                ),
                Prefetch(
                    'services',
                    queryset=ServiceNoProviderSerializer.get_default_queryset(),
                ),
                Prefetch(
                    'user',
                    queryset=UserSerializer.get_default_queryset(),
                ),
            )
        )


class ProviderUpdateSerializer(serializers.Serializer):
    companies = serializers.PrimaryKeyRelatedField(many=True, queryset=Company.objects.all().not_deleted())
    notes = NoteUnsafeSerializer(many=True, default=[])
    # services is not modifiable from here

    class Meta:
        model = Provider
        fields = '__all__'

    def update(self, instance: Provider, business_name, validated_data=None):
        data = validated_data or self.validated_data
        extras = data.pop('extra', {})
        companies = data.pop('companies', [])
        notes = data.pop('notes', [])

        for (k, v) in data.items():
            setattr(instance, k, v)
        instance.save()

        sync_m2m(instance.companies, companies)
        NoteSerializer.sync_notes(instance, notes)

        manage_extra_attrs(business_name, instance, extras)


class ServiceSerializer(ServiceNoProviderSerializer):
    provider = ProviderSerializer()

    class Meta:
        model = Service
        fields = '__all__'

    @staticmethod
    def get_default_queryset():
        return (
            super(ServiceSerializer, ServiceSerializer)
                .get_default_queryset()
                .prefetch_related(
                    Prefetch(
                        'provider',
                        queryset=ProviderSerializer.get_default_queryset(),
                    ),
                )
        )


class ServiceRootNoBookingSerializer(ServiceRootBaseSerializer):
    services = ServiceSerializer(many=True)

    @staticmethod
    def get_default_queryset():
        return (
            ServiceRoot.objects
                .all()
                .not_deleted()
                .prefetch_related(
                    Prefetch(
                        'services',
                        queryset=ServiceSerializer.get_default_queryset(),
                    ),
                )
        )


class ServiceCreateSerializer(ServiceNoProviderSerializer):
    business = BusinessField()
    categories = serializers.PrimaryKeyRelatedField(many=True, queryset=Category.objects.all())
    provider = serializers.PrimaryKeyRelatedField(queryset=Provider.objects.all())
    root = serializers.PrimaryKeyRelatedField(queryset=ServiceRoot.objects.all(), required=False)
    bill_amount = serializers.DecimalField(max_digits=32, decimal_places=2)
    bill_rate = serializers.IntegerField()

    class Meta:
        model = Service
        fields = '__all__'

    def create(self, validated_data=None) -> int:
        data = validated_data or self.validated_data
        extras = data.pop('extra', {})
        categories = data.pop('categories', [])

        service = Service.objects.create(**data)
        if categories:
            service.categories.add(*categories)
        manage_extra_attrs(service.business, service, extras)

        return service.id


class AffiliationNoRecipientSerializer(generic_serializer(Affiliation)):
    company = CompanySerializer()

    class Meta:
        model = Affiliation
        fields = ('id', 'company',)


class RecipientNoAffiliationSerializer(user_subtype_serializer(Recipient)):
    companies = serializers.PrimaryKeyRelatedField(many=True, queryset=Company.objects.all().not_deleted(), default=[])
    notes = NoteSerializer(many=True, default=[])
    
    class Meta:
        model = Recipient
        fields = '__all__'

    @staticmethod
    def get_default_queryset():
        return (
            Recipient.objects
                .all()
                .not_deleted('user')
                .prefetch_related(
                    Prefetch(
                        'companies',
                        queryset=CompanySerializer.get_default_queryset(),
                    ),
                    Prefetch(
                        'extra',
                        queryset=ExtraAttrSerializer.get_default_queryset(),
                    ),
                    Prefetch(
                        'notes',
                        queryset=NoteSerializer.get_default_queryset(),
                    ),
                    Prefetch(
                        'user',
                        queryset=UserSerializer.get_default_queryset(),
                    ),
                )
        )


class AffiliationSerializer(generic_serializer(Affiliation)):
    company = CompanySerializer()
    recipient = RecipientNoAffiliationSerializer()

    @staticmethod
    def get_default_queryset():
        return (
            Affiliation.objects
                .all()
                .not_deleted()
                .prefetch_related(
                    Prefetch(
                        'company',
                        queryset= CompanySerializer.get_default_queryset(),
                    ),
                    Prefetch(
                        'extra',
                        queryset=ExtraAttrSerializer.get_default_queryset(),
                    ),
                    Prefetch(
                        'recipient',
                        queryset=RecipientNoAffiliationSerializer.get_default_queryset(),
                    ),
                )
        )


class AffiliationCreateSerializer(AffiliationSerializer):
    company = serializers.PrimaryKeyRelatedField(queryset=Company.objects.all(), allow_null=True)
    recipient = serializers.PrimaryKeyRelatedField(queryset=Recipient.objects.all())

    def create(self, business_name, validated_data=None):

        data = validated_data or self.validated_data
        extras = data.pop('extra', {})
        affiliation = Affiliation.objects.create(**data)

        manage_extra_attrs(business_name, affiliation, extras)

        return affiliation


class RecipientSerializer(RecipientNoAffiliationSerializer):
    affiliations = AffiliationNoRecipientSerializer(many=True, read_only=True)


class RecipientCreateSerializer(extendable_serializer(Recipient)):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    companies = serializers.PrimaryKeyRelatedField(many=True, queryset=Company.objects.all().not_deleted(), default=[])
    notes = NoteSerializer(many=True, default=[])

    def create(self, business_name, validated_data=None):
        data = validated_data or self.validated_data
        extras = data.pop('extra', {})
        companies = data.pop('companies', [])
        notes = data.pop('notes', [])

        recipient = Recipient.objects.create(**data)
        if companies:
            recipient.categories.add(*companies)
        if notes:
            note_instances = NoteSerializer.create_instances(notes)
            recipient.notes.add(*note_instances)

        manage_extra_attrs(business_name, recipient, extras)

        return recipient


class RecipientUpdateSerializer(RecipientCreateSerializer):
    companies = serializers.PrimaryKeyRelatedField(many=True, queryset=Company.objects.all().not_deleted(), default=[])
    notes = NoteUnsafeSerializer(many=True, default=[])

    def update(self, instance: Recipient, business_name, validated_data=None):
        data = validated_data or self.validated_data
        extras = data.pop('extra', {})
        companies = data.pop('companies', [])
        notes = data.pop('notes', [])

        for (k, v) in data.items():
            setattr(instance, k, v)
        instance.save()

        sync_m2m(instance.companies, companies)
        NoteSerializer.sync_notes(instance, notes)

        manage_extra_attrs(business_name, instance, extras)


class RequesterSerializer(user_subtype_serializer(Requester)):
    companies = CompanySerializer(many=True)

    @staticmethod
    def get_default_queryset():
        return (
            Requester.objects
                .all()
                .not_deleted('user')
                .prefetch_related(
                    Prefetch(
                        'companies',
                        queryset= CompanySerializer.get_default_queryset()
                    ),
                    Prefetch(
                        'user',
                        queryset=UserSerializer.get_default_queryset(),
                    ),
                )
        )

class RequesterCreateSerializer(generic_serializer(Requester)):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    companies = serializers.PrimaryKeyRelatedField(many=True, queryset=Company.objects.all().not_deleted(), default=[])

    def create(self, business_name, validated_data=None):
        data = validated_data or self.validated_data
        companies = data.pop('companies', [])

        requester = Requester.objects.create(**data)
        if companies:
            requester.categories.add(*companies)

        return requester


BusinessSerializer = generic_serializer(Business)


class ExpenseSerializer(generic_serializer(Expense)):
    booking_id = serializers.PrimaryKeyRelatedField(read_only=True, source='booking')

    class Meta:
        model = Expense
        fields = '__all__'

    @staticmethod
    def get_default_queryset():
        return Expense.objects.all().not_deleted()


class ExpenseCreateSerializer(ExpenseSerializer):
    booking = serializers.PrimaryKeyRelatedField(queryset=Booking.objects.all())

    def create(self, validated_data=None) -> int:
        data: dict = validated_data or self.validated_data
        expense = Expense.objects.create(**data)
        return expense.id

    def update(self, instance: Event, validated_data=None):
        data: dict = validated_data or self.validated_data
        for (k, v) in data.items():
            setattr(instance, k, v)
        instance.save()


class BookingNoEventsSerializer(extendable_serializer(Booking)):
    categories = CategorySerializer(many=True)
    companies = CompanySerializer(many=True)
    events_count = serializers.IntegerField(source='events.count', read_only=True)
    expenses = ExpenseSerializer(many=True)
    operators = OperatorSerializer(many=True)
    services = ServiceSerializer(many=True)
    notes = NoteSerializer(many=True, default=[])
    offers = serializers.PrimaryKeyRelatedField(many=True, queryset=Offer.objects.all(), default=[])
    service_root = ServiceRootBaseSerializer(allow_null=True)

    class Meta:
        model = Booking
        fields = '__all__'

    @staticmethod
    def get_default_queryset():
        return (
            Booking.objects
                .all()
                .not_deleted('business')
                .prefetch_related(
                    Prefetch(
                        'categories',
                        queryset=CategorySerializer.get_default_queryset(),
                    ),
                    Prefetch(
                        'companies',
                        queryset= CompanySerializer.get_default_queryset(),
                    ),
                    Prefetch(
                        'offers',
                        queryset=OfferSerializer.get_default_queryset(),
                    ),
                    Prefetch(
                        'notes',
                        queryset=NoteSerializer.get_default_queryset()
                    ),
                    Prefetch(
                        'expenses',
                        queryset=ExpenseSerializer.get_default_queryset(),
                    ),
                    Prefetch(
                        'extra',
                        queryset=ExtraAttrSerializer.get_default_queryset(),
                    ),
                    Prefetch(
                        'operators',
                        queryset=OperatorSerializer.get_default_queryset(),
                    ),
                    Prefetch(
                        'services',
                        queryset=ServiceSerializer.get_default_queryset(),
                    ),
                    Prefetch(
                        'service_root',
                        queryset=ServiceRootBaseSerializer.get_default_queryset(),
                    ),
                )
        )


class EventNoBookingSerializer(extendable_serializer(Event)):
    affiliates = AffiliationSerializer(many=True)
    agents = AgentSerializer(many=True)
    booking = serializers.PrimaryKeyRelatedField(queryset=Booking.objects.all().not_deleted('business'))
    payer = PayerSerializer(required=False)
    payer_company = CompanySerializer(required=False)
    requester = RequesterSerializer()

    class Meta:
        model = Event
        fields = '__all__'

    @staticmethod
    def get_default_queryset():
        return (
            Event.objects
                .all()
                .not_deleted()
                .prefetch_related(
                    Prefetch(
                        'affiliates',
                        queryset=AffiliationSerializer.get_default_queryset(),
                    ),
                    Prefetch(
                        'agents',
                        queryset=AgentSerializer.get_default_queryset(),
                    ),
                    Prefetch(
                        'payer',
                        queryset=PayerSerializer.get_default_queryset(),
                    ),
                    Prefetch(
                        'payer_company',
                        queryset=CompanySerializer.get_default_queryset(),
                    ),
                    Prefetch(
                        'requester',
                        queryset=RequesterSerializer.get_default_queryset(),
                    ),
                )
        )


class BookingSerializer(BookingNoEventsSerializer):
    events = EventNoBookingSerializer(many=True)
    public_id = serializers.ReadOnlyField()

    @staticmethod
    def get_default_queryset():
        return (
            super(BookingSerializer, BookingSerializer)
                .get_default_queryset()
                .prefetch_related(
                    Prefetch(
                        'events',
                        queryset=EventNoBookingSerializer.get_default_queryset(),
                    )
                )
        )


class BookingCreateSerializer(extendable_serializer(Booking)):
    business = BusinessField(required=False)
    categories = serializers.PrimaryKeyRelatedField(many=True, required=False, queryset=Category.objects.all())
    companies = serializers.PrimaryKeyRelatedField(many=True, required=False, queryset=Company.objects.all())
    operators = serializers.PrimaryKeyRelatedField(many=True, required=False, queryset=Operator.objects.all())
    service_root = serializers.PrimaryKeyRelatedField(required=False, queryset=ServiceRoot.objects.all())
    services = serializers.PrimaryKeyRelatedField(many=True, required=False, queryset=Service.objects.all())
    created_at = serializers.DateTimeField(required=False)
    public_id = serializers.ReadOnlyField()
    notes = NoteUnsafeSerializer(many=True, default=[])

    class Meta:
        # TODO add constraints here for incomplete bookings
        model = Booking
        fields = (
            'business',
            'categories',
            'companies',
            'operators',
            'service_root',
            'services',
            'created_at',
            'public_id',
            'notes'
        )

    def create(self, validated_data=None) -> int:
        data = validated_data or self.validated_data
        business = BusinessField().to_internal_value(data.get('business'))
        extras = data.pop('extra', {})
        categories = data.pop('categories', [])
        companies = data.pop('companies', [])
        operators = data.pop('operators', [])
        services = data.pop('services', [])
        notes = data.pop('notes', [])

        # TODO add constraints here for incomplete bookings

        booking = Booking.objects.create(**data)
        if categories:
            booking.categories.add(*categories)
        if companies:
            booking.companies.add(*companies)
        if operators:
            booking.operators.add(*operators)
        if services:
            booking.services.add(*services)
        if notes:
            note_instances = NoteSerializer.create_instances(notes)
            booking.notes.add(*note_instances)
        manage_extra_attrs(business, booking, extras)

        return booking.id

    def update(self, instance: Booking, business, validated_data=None):
        data: dict = validated_data or self.validated_data
        data.pop('business', None)  # Ensure business will not be modified accidentally
        business = BusinessField().to_internal_value(business)
        extras = data.pop('extra', {})
        categories = data.pop('categories', [])
        companies = data.pop('companies', [])
        operators = data.pop('operators', [])
        services = data.pop('services', [])
        notes_data = data.pop('notes', [])

        NoteSerializer.sync_notes(instance, notes_data)

        # TODO add constraints here for incomplete bookings

        for (k, v) in data.items():
            setattr(instance, k, v)
        instance.save()

        sync_m2m(instance.categories, categories)
        sync_m2m(instance.companies, companies)
        sync_m2m(instance.operators, operators)
        sync_m2m(instance.services, services)

        manage_extra_attrs(business, instance, extras)


class EventSerializer(EventNoBookingSerializer):
    booking = BookingNoEventsSerializer()


class EventCreateSerializer(extendable_serializer(Event)):
    affiliates = serializers.PrimaryKeyRelatedField(many=True, queryset=Affiliation.objects.all(), required=False)
    agents = serializers.PrimaryKeyRelatedField(many=True, queryset=Agent.objects.all(), required=False)
    booking = serializers.PrimaryKeyRelatedField(queryset=Booking.objects.all())
    payer = serializers.PrimaryKeyRelatedField(queryset=Payer.objects.all(), required=False)
    payer_company = serializers.PrimaryKeyRelatedField(queryset=Company.objects.all().not_deleted(), required=False)
    requester = serializers.PrimaryKeyRelatedField(queryset=Requester.objects.all())

    class Meta:
        model = Event
        fields = '__all__'

    def create(self, business, validated_data=None) -> int:
        data: dict = validated_data or self.validated_data
        affiliates = data.pop('affiliates', [])
        agents = data.pop('agents', [])
        extras = data.pop('extra', {})

        event = Event.objects.create(**data)
        if affiliates:
            event.affiliates.add(*affiliates)
        if agents:
            event.agents.add(*agents)
        manage_extra_attrs(business, event, extras)

        return event.id

    def update(self, instance: Event, business, validated_data=None):
        data: dict = validated_data or self.validated_data
        affiliates = data.pop('affiliates', [])
        agents = data.pop('agents', [])
        extras = data.pop('extra', [])

        for (k, v) in data.items():
            setattr(instance, k, v)
        instance.save()

        sync_m2m(instance.affiliates, affiliates)
        sync_m2m(instance.agents, agents)
        manage_extra_attrs(business, instance, extras)


InvoiceSerializer = generic_serializer(Invoice)


class LedgerSerializer(BaseSerializer):
    booking = BookingSerializer()
    event = EventSerializer()
    invoice = InvoiceSerializer()

    class Meta:
        model = Ledger
        fields = '__all__'


class CompanySerializerWithRoles(CompanySerializer):
    agents = AgentSerializer(many=True)
    operators = OperatorSerializer(many=True)
    payers = PayerSerializer(many=True)
    providers = ProviderSerializer(many=True)
    recipients = RecipientSerializer(many=True)
    requesters = RequesterSerializer(many=True)

    class Meta:
        model = Company
        fields = '__all__'


class OfferSerializer(BaseSerializer):
    booking = BookingSerializer()
    provider = ProviderSerializer()

    class Meta:
        model = Offer
        fields = '__all__'


class OfferCreateSerializer(extendable_serializer(Offer)):
    booking = serializers.PrimaryKeyRelatedField(queryset=Booking.objects.all())
    provider = serializers.PrimaryKeyRelatedField(queryset=Provider.objects.all())

    class Meta:
        model = Offer
        fields = '__all__'

    def create(self, business, validated_data=None) -> int:
        data: dict = validated_data or self.validated_data
        extras = data.pop('extra', {})

        offer = Offer.objects.create(**data)
        manage_extra_attrs(business, offer, extras)

        return offer.id

    def update(self, instance: Offer, business, validated_data=None):
        data: dict = validated_data or self.validated_data
        extras = data.pop('extra', {})

        for (k, v) in data.items():
            setattr(instance, k, v)
        instance.save()

        manage_extra_attrs(business, instance, extras)