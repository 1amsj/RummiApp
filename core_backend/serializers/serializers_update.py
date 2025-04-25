from rest_framework import serializers

from core_backend.models import Admin, Agent, Authorization, Booking, Category, Company, CompanyRelationship, Event, Expense, GlobalSetting, Language, \
    Location, NotificationOption, Offer, Operator, Payer, Provider, Rate, Recipient, Report, Requester, Service, ServiceArea, ServiceRoot, User
from core_backend.serializers.serializers import AuthorizationBaseSerializer, CompanyRelationshipSerializer, CompanyWithParentSerializer, \
    ContactSerializer, LocationSerializer, NoteSerializer, NotificationOptionSerializer
from core_backend.serializers.serializers_create import BookingCreateSerializer, CategoryCreateSerializer, CompanyRelationshipCreateSerializer, \
    EventCreateSerializer, ExpenseCreateSerializer, GlobalSettingCreateSerializer, LanguageCreateSerializer, OfferCreateSerializer, RateCreateSerializer, RecipientCreateSerializer, ReportCreateSerializer, ServiceCreateSerializer, ServiceAreaCreateSerializer, ServiceRootCreateSerializer, \
    UserCreateSerializer
from core_backend.serializers.serializers_fields import BusinessField
from core_backend.serializers.serializers_plain import ContactUnsafeSerializer, LocationUnsafeSerializer, \
    NoteUnsafeSerializer
from core_backend.serializers.serializers_utils import extendable_serializer
from core_backend.services.core_services import manage_extra_attrs, sync_m2m, update_model_unique_field
from core_backend.services.core_services import user_sync_email_with_contact
from django.contrib.postgres.search import SearchVector
from django.db.models import Q
from core_backend.models import Notification

class AuthorizationUpdateSerializer(AuthorizationBaseSerializer):
    def update(self, instance: Authorization, validated_data=None):
        data: dict = validated_data or self.validated_data
        events_data = data.pop('events', None)

        for (k, v) in data.items():
            setattr(instance, k, v)
        instance.save()

        if events_data is not None:
            instance.events.set(events_data)

class GlobalSettingUpdateSerializer(GlobalSettingCreateSerializer):
    def update(self, instance: GlobalSetting, business, validated_data=None):
        data: dict = validated_data or self.validated_data
        extras = data.pop('extra', {})
        print(extras)
        
        manage_extra_attrs(business, instance, extras)
        
        for (k, v) in data.items():
            setattr(instance, k, v)
        instance.save()


class BookingUpdateSerializer(BookingCreateSerializer):
    def update(self, instance: Booking, business, validated_data=None):
        data: dict = validated_data or self.validated_data
        data.pop('business', None)  # Ensure business will not be modified accidentally
        business = BusinessField().to_internal_value(business)
        extras = data.pop('extra', {})
        children = data.pop('children', [])
        companies = data.pop('companies', [])
        operators = data.pop('operators', [])
        services = data.pop('services', [])
        notes_data = data.pop('notes', [])

        NoteSerializer.sync_notes(instance, notes_data)

        for (k, v) in data.items():
            setattr(instance, k, v)
        instance.save()
        instance.children.set(children)

        sync_m2m(instance.companies, companies)
        sync_m2m(instance.operators, operators)
        sync_m2m(instance.services, services)

        manage_extra_attrs(business, instance, extras)

        return instance

class CategoryUpdateSerializer(CategoryCreateSerializer):
    def update(self, instance: Category, validated_data=None):
        data: dict = validated_data or self.validated_data
        for (k, v) in data.items():
            setattr(instance, k, v)
        instance.save()


class CompanyUpdateSerializer(CompanyWithParentSerializer):
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


    def update(self, instance: Company, business, validated_data=None):
        data: dict = validated_data or self.validated_data

        data.pop('company_relationships_from')

        agents_data = data.pop('agents', None)
        operators_data = data.pop('operators', None)
        payers_data = data.pop('payers', None)
        providers_data = data.pop('providers', None)
        recipients_data = data.pop('recipients', None)
        requesters_data = data.pop('requesters', None)
        extras = data.pop('extra', [])

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

        ContactSerializer.sync_contacts(
            instance,
            contacts_data=data.pop('contacts')
        )

        LocationSerializer.sync_locations(
            instance,
            locations_data=data.pop('locations')
        )

        NoteSerializer.sync_notes(
            instance,
            notes_data=data.pop('notes')
        )

        manage_extra_attrs(business, instance, extras)

        for (k, v) in data.items():
            setattr(instance, k, v)

        instance.save()

class RateUpdateSerializer(RateCreateSerializer):
    def update(self, instance: Rate, business, validated_data=None):
        data: dict = validated_data or self.validated_data
        extras = data.pop('extra', [])

        for (k, v) in data.items():
            setattr(instance, k, v)
        instance.save()

        manage_extra_attrs(business, instance, extras)

class EventUpdateSerializer(EventCreateSerializer):
    def update(self, instance: Event, business, group_booking, validated_data=None):
        data: dict = validated_data or self.validated_data
        affiliates = data.pop('affiliates', [])
        agents = data.pop('agents', [])
        extras = data.pop('extra', [])
        
        formatted_date_start = data['start_at'].strftime("%Y-%m-%d %H:%M")
        formatted_date_end = data['end_at'].strftime("%Y-%m-%d %H:%M")
        
        overlapping_events = Event.objects.filter(
            ~Q(booking_id=data['booking'].id),
            start_at__lt=formatted_date_end,
            end_at__gt=formatted_date_start,
            affiliates=affiliates[0].id
        )
        
        overlapping_agents = Event.objects.filter(
            ~Q(booking_id=data['booking'].id),
            start_at__lt=formatted_date_end,
            end_at__gt=formatted_date_start,
            agents=agents[0].id
        )
        
        group_bookings = []
        for event in overlapping_agents:
            if event.booking:
                extras = event.booking.get_extra_attrs()
                group_booking_previous = extras.get('group_booking', None)
                group_bookings.append(group_booking_previous)

        group_bookings.append(group_booking)
        group_bookings = [value == '"True"' or value == True for value in group_bookings]      
        agentsCanOverlap = all(group_bookings)
   
        
        if(extras.__contains__('claim_number')):
            claim_number = extras['claim_number']
        else:
            claim_number = None
        
        overlapping_claim = Event.objects.annotate(
            search=SearchVector('extra__data')
        ).filter(
            extra__key='claim_number',
            search=claim_number
        ).filter(
            ~Q(booking_id=data['booking'].id),
            affiliates=affiliates[0].id,
        )
        
        if overlapping_events.exists():
            #OVERLAP
            raise Exception("Overlapping event")
        elif overlapping_agents.exists() and not agentsCanOverlap:
            #SAME EVENT DIFFER
            raise Exception("Overlapping medical provider", overlapping_agents)

        for (k, v) in data.items():
            setattr(instance, k, v)
        instance.save()

        sync_m2m(instance.affiliates, affiliates)
        sync_m2m(instance.agents, agents)
        manage_extra_attrs(business, instance, extras)

        update_model_unique_field(business, instance)


class ExpenseUpdateSerializer(ExpenseCreateSerializer):
    def update(self, instance: Expense, validated_data=None):
        data: dict = validated_data or self.validated_data
        for (k, v) in data.items():
            setattr(instance, k, v)
        instance.save()


class LanguageUpdateSerializer(LanguageCreateSerializer):
    def update(self, instance: Language, validated_data=None):
        data: dict = validated_data or self.validated_data
        for (k, v) in data.items():
            setattr(instance, k, v)
        instance.save()


class AdminUpdateSerializer(extendable_serializer(Admin)):
    user = serializers.ReadOnlyField()
    role = serializers.StringRelatedField()

    class Meta:
        model = Admin
        fields = '__all__'

    def update(self, instance: Admin, business_name, validated_data=None):
        data = validated_data or self.validated_data
        extras = data.pop('extra', {})

        for (k, v) in data.items():
            setattr(instance, k, v)
        instance.save()

        sync_m2m(instance.companies)

        manage_extra_attrs(business_name, instance, extras)

class AgentUpdateSerializer(extendable_serializer(Agent)):
    user = serializers.ReadOnlyField()
    companies = serializers.PrimaryKeyRelatedField(many=True, queryset=Company.objects.all().not_deleted())
    role = serializers.StringRelatedField()

    class Meta:
        model = Agent
        fields = '__all__'

    def update(self, instance: Agent, business_name, validated_data=None):
        data = validated_data or self.validated_data
        extras = data.pop('extra', {})
        companies = data.pop('companies', [])

        for (k, v) in data.items():
            setattr(instance, k, v)
        instance.save()

        sync_m2m(instance.companies, companies)

        manage_extra_attrs(business_name, instance, extras)


class ProviderUpdateSerializer(extendable_serializer(Provider)):
    user = serializers.ReadOnlyField()
    companies = serializers.PrimaryKeyRelatedField(many=True, queryset=Company.objects.all().not_deleted())
    notes = NoteUnsafeSerializer(many=True, default=[])

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


class ServiceUpdateSerializer(ServiceCreateSerializer):
    def update(self, instance: Service, validated_data=None):
        data = validated_data or self.validated_data
        extras = data.pop('extra', {})

        for (k, v) in data.items():
            setattr(instance, k, v)
        instance.save()

        manage_extra_attrs(instance.business, instance, extras)

class ServiceAreaUpdateSerializer(ServiceAreaCreateSerializer):
    def update(self, instance: ServiceArea, validated_data=None):
        data = validated_data or self.validated_data

        for (k, v) in data.items():
            setattr(instance, k, v)
        instance.save()


class ServiceRootUpdateSerializer(ServiceRootCreateSerializer):
    def update(self, instance: ServiceRoot, validated_data=None):
        data: dict = validated_data or self.validated_data
        categories = data.pop('categories', None)

        for (k, v) in data.items():
            setattr(instance, k, v)
        instance.save()

        sync_m2m(instance.categories, categories)


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
        ContactSerializer.sync_contacts(instance, contacts_data)

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


class OfferUpdateSerializer(OfferCreateSerializer):
    # Override the fields from the parent class and set required=False
    booking = serializers.PrimaryKeyRelatedField(read_only=True, required=False)
    service = serializers.PrimaryKeyRelatedField(read_only=True, required=False)
    status = serializers.CharField(required=True)

    def update(self, instance: Offer, business_name, validated_data=None):
        data: dict = validated_data or self.validated_data
        data.pop('booking', None)
        data.pop('service', None)
        extras = data.pop('extra', None)

        for (k, v) in data.items():
            setattr(instance, k, v)

        instance.save()

        manage_extra_attrs(business_name, instance, extras)


class ReportUpdateSerializer(ReportCreateSerializer):
    def update(self, instance: Report, business_name, validated_data=None):
        data: dict = validated_data or self.validated_data
        extras = data.pop('extra', None)

        for (k, v) in data.items():
            setattr(instance, k, v)

        instance.save()

        manage_extra_attrs(business_name, instance, extras)

class CompanyRelationshipUpdateSerializer(CompanyRelationshipCreateSerializer):
    company_from = serializers.ReadOnlyField()
    company_to = serializers.PrimaryKeyRelatedField(queryset=Company.objects.all().not_deleted())
    relationship = serializers.CharField()

    class Meta:
        model = CompanyRelationship
        fields = '__all__'

    def update(self, instance: CompanyRelationship, validated_data=None):
        data = validated_data or self.validated_data
        
        for (k, v) in data.items():
            setattr(instance, k, v)
        
        instance.save()

class NotificationOptionUpdateSerializer(NotificationOptionSerializer):
    def update(self, instance: NotificationOption, validated_data=None):
        data: dict = validated_data or self.validated_data
        for (k, v) in data.items():
            setattr(instance, k, v)
        instance.save()
