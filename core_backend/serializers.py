from typing import Type

from django.contrib.auth.password_validation import validate_password
from django.db import models
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from core_backend.models import Affiliation, Agent, Booking, Business, Category, Company, Contact, Event, \
    Expense, ExtendableModel, Extra, Invoice, Ledger, Location, Operator, Payer, Provider, Recipient, Requester, \
    Service, User
from core_backend.services import assert_extendable, get_model_field_names, is_extendable, \
    manage_extra_attrs, fetch_updated_from_validated_data, sync_m2m


# Extra serializers
class ExtraAttrSerializer(serializers.ModelSerializer):
    class Meta:
        model = Extra
        fields = ('key', 'value')


def extendable_serializer(serializer_model: Type[models.Model], serializer_fields='__all__'):
    assert_extendable(serializer_model)

    class ExtendableSerializer(serializers.ModelSerializer):
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
def generic_serializer(serializer_model: Type[models.Model], serializer_fields='__all__'):
    parent_serializer = (
        extendable_serializer(serializer_model)
        if is_extendable(serializer_model)
        else serializers.ModelSerializer
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
class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = '__all__'

    def validate(self, data: dict):
        if not (data.get('email') or data.get('phone') or data.get('fax')):
            raise serializers.ValidationError(_('Contact data can not be empty'))

        return super(ContactSerializer, self).validate(data)


class ContactUnsafeSerializer(ContactSerializer):
    id = serializers.IntegerField(read_only=False, allow_null=True, required=False)


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = '__all__'


class CompanySerializer(serializers.ModelSerializer):
    contacts = ContactSerializer(many=True)
    locations = LocationSerializer(many=True)

    class Meta:
        model = Company
        fields = '__all__'


class CompanyCreateSerializer(CompanySerializer):
    def create(self, validated_data=None) -> int:
        data: dict = validated_data or self.validated_data
        contacts_data = data.pop('contacts', None)
        locations_data = data.pop('locations', None)

        company = Company.objects.create(**data)

        if contacts_data:
            contacts = [Contact(**d) for d in contacts_data]
            contact_ids = [c.id for c in Contact.objects.bulk_create(contacts)]
            company.contacts.add(*contact_ids)

        if locations_data:
            locations = [Location(**d) for d in locations_data]
            location_ids = [c.id for c in Location.objects.bulk_create(locations)]
            company.locations.add(*location_ids)

        return company.id


# User serializers
class UserSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    contacts = ContactSerializer(many=True)
    operator_id = serializers.PrimaryKeyRelatedField(allow_null=True, read_only=True, source='as_operator')
    requester_id = serializers.PrimaryKeyRelatedField(allow_null=True, read_only=True, source='as_requester')

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'national_id',
            'ssn',
            'contacts',
            'operator_id',
            'requester_id',
            'is_operator',
            'is_provider',
            'is_recipient',
            'is_requester',
            'is_payer',
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
            'contacts',
            'password',
            'confirmation',
        )

    def validate(self, attrs):
        if (attrs['password'] or attrs['confirmation']) and attrs['password'] != attrs['confirmation']:
            raise serializers.ValidationError({"confirmation": "Password fields didn't match."})
        return attrs

    def create(self, validated_data=None):
        data: dict = validated_data or self.validated_data
        password = data.pop('password', None)
        data.pop('confirmation', None)
        contacts_data = data.pop('contacts', None)

        user = User.objects.create(**data)
        if password:
            user.set_password(password)
            user.save()

        if contacts_data:
            contacts = [Contact(**d) for d in contacts_data]
            contact_ids = [c.id for c in Contact.objects.bulk_create(contacts)]
            user.contacts.add(*contact_ids)

        return user


class UserUpdateSerializer(UserCreateSerializer):
    contacts = ContactUnsafeSerializer(many=True)
    username = serializers.ReadOnlyField()

    def update(self, instance: User, validated_data=None):
        data: dict = validated_data or self.validated_data

        password = data.pop('password', None)
        data.pop('confirmation', None)
        if password:
            instance.set_password(password)
            instance.save()

        if contacts_data := data.pop('contacts', None):
            created_contacts, updated_contacts = fetch_updated_from_validated_data(Contact, contacts_data)
            # Create
            if created_contacts:
                created_contacts = Contact.objects.bulk_create(created_contacts)
                instance.contacts.add(*created_contacts)
            # Update
            if updated_contacts:
                Contact.objects.bulk_update(updated_contacts, ['phone', 'email', 'fax'])

        for (k, v) in data.items():
            setattr(instance, k, v)
        instance.save()


def user_subtype_serializer(serializer_model: Type[models.Model]):
    serializer_parent = (
        extendable_serializer(serializer_model)
        if is_extendable(serializer_model)
        else serializers.ModelSerializer
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


class AgentSerializer(user_subtype_serializer(Agent)):
    companies = CompanySerializer(many=True)


class OperatorSerializer(user_subtype_serializer(Operator)):
    companies = CompanySerializer(many=True)


class PayerSerializer(user_subtype_serializer(Payer)):
    companies = CompanySerializer(many=True)
    method = serializers.CharField()

class PayerCreateSerializer(PayerSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    companies = serializers.PrimaryKeyRelatedField(many=True, queryset=Company.objects.all())
    method = serializers.CharField()

    def create(self, validated_data=None):
        data = validated_data or self.validated_data
        companies_data = data.pop('companies', None)
        payer = Payer.objects.create(**data)
        if companies_data:
            payer.companies.add(*companies_data)
        return payer

class ServiceNoProviderSerializer(extendable_serializer(Service)):
    business = generic_serializer(Business)
    categories = generic_serializer(Category)(many=True)
    bill_amount = serializers.DecimalField(max_digits=32, decimal_places=2)
    bill_rate = serializers.IntegerField()

    class Meta:
        model = Service
        fields = '__all__'


class ProviderSerializer(user_subtype_serializer(Provider)):
    companies = CompanySerializer(many=True)
    services = ServiceNoProviderSerializer(many=True)

    class Meta:
        model = Provider
        fields = '__all__'


class ServiceCreateSerializer(ServiceNoProviderSerializer):
    business = BusinessField()
    categories = serializers.PrimaryKeyRelatedField(many=True, queryset=Category.objects.all())
    provider = serializers.PrimaryKeyRelatedField(queryset=Provider.objects.all())
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


class ProviderServiceSerializer(user_subtype_serializer(Provider)):
    services = ServiceNoProviderSerializer(many=True)

    class Meta:
        model = Provider
        fields = '__all__'


class AffiliationNoRecipientSerializer(generic_serializer(Affiliation)):
    company = CompanySerializer()

    class Meta:
        model = Affiliation
        fields = ('id', 'company',)


class RecipientNoAffiliationSerializer(user_subtype_serializer(Recipient)):
    class Meta:
        model = Recipient
        exclude = ('companies',)


class AffiliationSerializer(generic_serializer(Affiliation)):
    company = CompanySerializer()
    recipient = RecipientNoAffiliationSerializer()


class RecipientSerializer(RecipientNoAffiliationSerializer):
    affiliations = AffiliationNoRecipientSerializer(many=True, read_only=True)


RequesterSerializer = user_subtype_serializer(Requester)

CategorySerializer = generic_serializer(Category)

BusinessSerializer = generic_serializer(Business)


class ServiceSerializer(extendable_serializer(Service)):
    business = BusinessSerializer()
    categories = CategorySerializer(many=True)
    provider = ProviderSerializer()
    bill_amount = serializers.DecimalField(max_digits=32, decimal_places=2)
    bill_rate = serializers.IntegerField()

    class Meta:
        model = Service
        fields = '__all__'


class ExpenseSerializer(generic_serializer(Expense)):
    booking_id = serializers.PrimaryKeyRelatedField(read_only=True, source='booking')

    class Meta:
        model = Expense
        fields = '__all__'


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
    # TODO add expenses

    class Meta:
        model = Booking
        fields = '__all__'


class EventNoBookingSerializer(serializers.ModelSerializer):
    affiliates = AffiliationSerializer(many=True)
    agents = AgentSerializer(many=True)
    booking = serializers.PrimaryKeyRelatedField(queryset=Booking.objects.all())
    payer = PayerSerializer()
    requester = RequesterSerializer()

    class Meta:
        model = Event
        fields = '__all__'


class BookingSerializer(BookingNoEventsSerializer):
    events = EventNoBookingSerializer(many=True)


class BookingCreateSerializer(extendable_serializer(Booking)):
    business = BusinessField(required=False)
    categories = serializers.PrimaryKeyRelatedField(many=True, required=False, queryset=Category.objects.all())
    companies = serializers.PrimaryKeyRelatedField(many=True, required=False, queryset=Company.objects.all())
    operators = serializers.PrimaryKeyRelatedField(many=True, required=False, queryset=Operator.objects.all())
    services = serializers.PrimaryKeyRelatedField(many=True, required=False, queryset=Service.objects.all())

    class Meta:
        model = Booking
        fields = (
            'business',
            'categories',
            'companies',
            'operators',
            'services',  # TODO add constraints here for incomplete bookings
        )

    def create(self, validated_data=None) -> int:
        data = validated_data or self.validated_data
        business = BusinessField().to_internal_value(data.get('business'))
        extras = data.pop('extra', {})
        categories = data.pop('categories', [])
        companies = data.pop('companies', [])
        operators = data.pop('operators', [])
        services = data.pop('services', [])

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


class EventCreateSerializer(serializers.ModelSerializer):
    affiliates = serializers.PrimaryKeyRelatedField(many=True, queryset=Affiliation.objects.all(), required=False)
    agents = serializers.PrimaryKeyRelatedField(many=True, queryset=Agent.objects.all(), required=False)
    booking = serializers.PrimaryKeyRelatedField(queryset=Booking.objects.all())
    payer = serializers.PrimaryKeyRelatedField(queryset=Payer.objects.all())
    requester = serializers.PrimaryKeyRelatedField(queryset=Requester.objects.all())

    class Meta:
        model = Event
        fields = '__all__'

    def validate(self, data: dict):
        if not data.get('location') and not data.get('meeting_url'):
            raise serializers.ValidationError(_('Either location or meeting URL must be specified'))

        return super(EventCreateSerializer, self).validate(data)

    def create(self, validated_data=None) -> int:
        data: dict = validated_data or self.validated_data
        affiliates = data.pop('affiliates', [])
        agents = data.pop('agents', [])

        event = Event.objects.create(**data)
        if affiliates:
            event.affiliates.add(*affiliates)
        if agents:
            event.agents.add(*agents)

        return event.id

    def update(self, instance: Event, validated_data=None):
        data: dict = validated_data or self.validated_data
        affiliates = data.pop('affiliates', [])
        agents = data.pop('agents', [])

        for (k, v) in data.items():
            setattr(instance, k, v)
        instance.save()

        sync_m2m(instance.affiliates, affiliates)
        sync_m2m(instance.agents, agents)


InvoiceSerializer = generic_serializer(Invoice)


class LedgerSerializer(serializers.ModelSerializer):
    booking = BookingSerializer()
    event = EventSerializer()
    invoice = InvoiceSerializer()

    class Meta:
        model = Ledger
        fields = '__all__'
