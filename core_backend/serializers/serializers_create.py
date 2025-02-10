from django.contrib.auth.models import Group, Permission
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from core_backend.models import Admin, Affiliation, Agent, Authorization, Booking, Category, Company, CompanyRelationship, Event, \
    Expense, GlobalSetting, Language, Location, Note, Notification, Offer, Operator, Payer, Provider, Rate, Recipient, Report, Requester, \
    Service, ServiceArea, ServiceRoot, User
from core_backend.serializers.serializers import AffiliationSerializer, AgentWithCompaniesSerializer, AuthorizationBaseSerializer, \
    CategorySerializer, CompanyRelationshipSerializer, \
    CompanyWithParentSerializer, \
    ContactSerializer, ExpenseSerializer, GlobalSettingSerializer, LanguageSerializer, LocationSerializer, NoteSerializer, \
    NotificationSerializer, OperatorSerializer, PayerSerializer, RateSerializer, ServiceNoProviderSerializer, \
    UserSerializer
from core_backend.serializers.serializers_fields import BusinessField
from core_backend.serializers.serializers_plain import NoteUnsafeSerializer
from core_backend.serializers.serializers_utils import extendable_serializer, generic_serializer
from core_backend.services.core_services import generate_public_id, manage_extra_attrs, update_model_unique_field, \
    user_sync_email_with_contact
from django.contrib.postgres.search import SearchVector

# Group for permissions
def get_or_create_operators_group():
    group, created = Group.objects.get_or_create(name='Operators')
    
    if created:
        permissions = Permission.objects.all()
        group.permissions.set(permissions)
        
    return group

def get_or_create_provider_group():
    group, created = Group.objects.get_or_create(name='Provider')
    names_of_permissions = [
        'Can change user', 
        'Can view user', 
        'Can view agent',
        'Can add booking',
        'Can change booking',
        'Can view booking',
        'Can view business',
        'Can view category',
        'Can add contact',
        'Can change contact',
        'Can view contact',
        'Can add event',
        'Can change event',
        'Can view event',
        'Can view invoice',
        'Can add location',
        'Can change location',
        'Can view location',
        'Can change provider data',
        'Can view provider data',
        'Can view service',
        'Can change recipient data'
        'Can view recipient data',
        'Can view payer data',
        'Can add extra data',
        'Can change extra data',
        'Can view extra data',
        'Can view company',
        'Can change affiliation',
        'Can view affiliation',
        'Can change service root',
        'Can view service root',
        'Can add note',
        'Can change note',
        'Can view note',
        'Can view language',
        'Can add offer',
        'Can change offer',
        'Can view offer',
        'Can add report',
        'Can change report',
        'Can view report',
        'Can view service area',
    ]
    
    if created:
        permissions = Permission.objects.filter(name__in=names_of_permissions)
        group.permissions.set(permissions)
        
    return group

class GlobalSettingCreateSerializer(GlobalSettingSerializer):
    def create(self, business_name, validated_data=None) -> int:
        data = validated_data or self.validated_data
        extras = data.pop('extra', {})
        global_setting = GlobalSetting.objects.create(**data)

        manage_extra_attrs(business_name, global_setting, extras)

        return global_setting.id

class AffiliationCreateSerializer(AffiliationSerializer):
    company = serializers.PrimaryKeyRelatedField(queryset=Company.objects.all(), allow_null=True)
    recipient = serializers.PrimaryKeyRelatedField(queryset=Recipient.objects.all())

    def create(self, business_name, validated_data=None):
        data = validated_data or self.validated_data
        extras = data.pop('extra', {})
        affiliation = Affiliation.objects.create(**data)

        manage_extra_attrs(business_name, affiliation, extras)

        return affiliation


class AgentCreateSerializer(AgentWithCompaniesSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    companies = serializers.PrimaryKeyRelatedField(many=True, queryset=Company.objects.all())
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

class AdminCreateSerializer():
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    role = serializers.CharField()

    def create(self, business_name, validated_data=None):
        data = validated_data or self.validated_data
        extras = data.pop('extra', {})
        admin = Admin.objects.create(**data)
        manage_extra_attrs(business_name, admin, extras)
        return admin

class AuthorizationCreateSerializer(AuthorizationBaseSerializer):
    def create(self, validated_data=None) -> int:
        data: dict = validated_data or self.validated_data
        events_data = data.pop('events', None)

        authorization = Authorization.objects.create(**data)

        if events_data is not None:
            authorization.events.set(events_data)

        return authorization.id


class BookingCreateSerializer(extendable_serializer(Booking)):
    business = BusinessField(required=False)
    children = serializers.PrimaryKeyRelatedField(many=True, required=False, queryset=Booking.objects.all())
    companies = serializers.PrimaryKeyRelatedField(many=True, required=False, queryset=Company.objects.all())
    operators = serializers.PrimaryKeyRelatedField(many=True, required=False, queryset=Operator.objects.all())
    parent = serializers.PrimaryKeyRelatedField(required=False, queryset=Booking.objects.all())
    service_root = serializers.PrimaryKeyRelatedField(required=False, queryset=ServiceRoot.objects.all())
    services = serializers.PrimaryKeyRelatedField(many=True, required=False, queryset=Service.objects.all())
    created_at = serializers.DateTimeField(required=False)
    public_id = serializers.ReadOnlyField()
    notes = NoteUnsafeSerializer(many=True, default=[])
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Booking
        fields = '__all__'

    def create(self, validated_data=None) -> int:
        data = validated_data or self.validated_data
        business = BusinessField().to_internal_value(data.get('business'))
        extras = data.pop('extra', {})
        children = data.pop('children', [])
        companies = data.pop('companies', [])
        operators = data.pop('operators', [])
        services = data.pop('services', [])
        notes = data.pop('notes', [])

        data['public_id'] = generate_public_id()

        booking = Booking.objects.create(**data)
        if children:
            booking.children.add(*children)
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


class CategoryCreateSerializer(CategorySerializer):
    def create(self, validated_data=None) -> int:
        data: dict = validated_data or self.validated_data
        company = Category.objects.create(**data)
        return company.id


class CompanyCreateSerializer(CompanyWithParentSerializer):
    parent_company = serializers.PrimaryKeyRelatedField(queryset=Company.objects.all(), required=False,
                                                        allow_null=True)
    agents = serializers.PrimaryKeyRelatedField(many=True, default=[], queryset=Agent.objects.all())
    operators = serializers.PrimaryKeyRelatedField(many=True, default=[], queryset=Operator.objects.all())
    payers = serializers.PrimaryKeyRelatedField(many=True, default=[], queryset=Payer.objects.all())
    providers = serializers.PrimaryKeyRelatedField(many=True, default=[], queryset=Provider.objects.all())
    recipients = serializers.PrimaryKeyRelatedField(many=True, default=[], queryset=Recipient.objects.all())
    requesters = serializers.PrimaryKeyRelatedField(many=True, default=[], queryset=Requester.objects.all())
    notes = NoteSerializer(many=True, default=[])
    company_relationships_from = CompanyRelationshipSerializer(many=True, default=[])

    def create(self, business_name, validated_data=None) -> int:
        data: dict = validated_data or self.validated_data

        contacts_data = data.pop('contacts', None)
        locations_data = data.pop('locations', None)
        notes_data = data.pop('notes', [])
        extras = data.pop('extra', {})

        agents_data = data.pop('agents', None)
        operators_data = data.pop('operators', None)
        payers_data = data.pop('payers', None)
        providers_data = data.pop('providers', None)
        recipients_data = data.pop('recipients', None)
        requesters_data = data.pop('requesters', None)

        company_relationships_from_data = data.pop('company_relationships_from', [])

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
            contact_instances = ContactSerializer.create_instances(contacts_data)
            company.contacts.add(*contact_instances)

        if locations_data:
            location_instances = LocationSerializer.create_instances(locations_data)
            company.locations.add(*location_instances)

        if notes_data:
            note_instances = NoteSerializer.create_instances(notes_data)
            company.notes.add(*note_instances)

        if company_relationships_from_data:
            company_relationship_instances = CompanyRelationshipSerializer.create_instances(company_relationships_from_data)
            company.company_relationships.add(*company_relationship_instances)

        manage_extra_attrs(business_name, company, extras)
    
        return company

class RateCreateSerializer(RateSerializer):
    root = serializers.PrimaryKeyRelatedField(queryset=ServiceRoot.objects.all(), required=False)
    bill_amount = serializers.DecimalField(max_digits=32, decimal_places=2)
    bill_rate = serializers.IntegerField()

    class Meta:
        model = Rate
        fields = '__all__'

    def create(self, business_name, validated_data=None) -> int:
        data = validated_data or self.validated_data
        extras = data.pop('extra', {})
        rate = Rate.objects.create(**data)

        manage_extra_attrs(business_name, rate, extras)

        return rate.id

class EventCreateSerializer(extendable_serializer(Event)):
    affiliates = serializers.PrimaryKeyRelatedField(many=True, queryset=Affiliation.objects.all(), required=False)
    agents = serializers.PrimaryKeyRelatedField(many=True, queryset=Agent.objects.all(), required=False)
    booking = serializers.PrimaryKeyRelatedField(queryset=Booking.objects.all())
    payer = serializers.PrimaryKeyRelatedField(queryset=Payer.objects.all(), required=False, allow_null=True)
    payer_company = serializers.PrimaryKeyRelatedField(queryset=Company.objects.all().not_deleted(), required=False, allow_null=True)
    requester = serializers.PrimaryKeyRelatedField(queryset=Requester.objects.all())

    class Meta:
        model = Event
        fields = '__all__'

    def create(self, business, group_booking, validated_data=None) -> int:
        data: dict = validated_data or self.validated_data
        affiliates = data.pop('affiliates', [])
        agents = data.pop('agents', [])
        extras = data.pop('extra', {})
        
        formatted_date_start = data['start_at'].strftime("%Y-%m-%d %H:%M")
        formatted_date_end = data['end_at'].strftime("%Y-%m-%d %H:%M")
        
        overlapping_events = Event.objects.filter(
            start_at__lte=formatted_date_end,
            end_at__gte=formatted_date_start,
            affiliates=affiliates[0].id
        )
        
        overlapping_agents = Event.objects.filter(
            start_at__lte=formatted_date_end,
            end_at__gte=formatted_date_start,
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
            affiliates=affiliates[0].id,
        )

        if overlapping_events.exists():
            #OVERLAP
            raise Exception("Overlapping event")
        elif overlapping_agents.exists() and not agentsCanOverlap:
            #SAME EVENT DIFFER
            raise Exception("Overlapping medical provider")

        event = Event.objects.create(**data)

        if affiliates:
            event.affiliates.add(*affiliates)
        if agents:
            event.agents.add(*agents)
        manage_extra_attrs(business, event, extras)

        update_model_unique_field(business, event)

        return event.id


class ExpenseCreateSerializer(ExpenseSerializer):
    booking = serializers.PrimaryKeyRelatedField(queryset=Booking.objects.all())

    def create(self, validated_data=None) -> int:
        data: dict = validated_data or self.validated_data
        expense = Expense.objects.create(**data)
        return expense.id


class LanguageCreateSerializer(LanguageSerializer):
    def create(self, validated_data=None) -> int:
        data: dict = validated_data or self.validated_data

        language = Language.objects.create(**data)

        return language.id


class NoteCreateSerializer(NoteSerializer):
    def create(self, validated_data=None) -> int:
        data: dict = validated_data or self.validated_data

        note = Note.objects.create(**data)

        return note.id


class NotificationCreateSerializer(NotificationSerializer):
    data = serializers.ReadOnlyField()
    booking_to_log = serializers.PrimaryKeyRelatedField(queryset=Booking.objects.all(), required=False)

    def create(self, validated_data=None, render_data=None) -> int:
        data: dict = validated_data or self.validated_data
        notification = Notification.objects.create(**data, data=render_data)
        return notification.id


class OperatorCreateSerializer(OperatorSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    companies = serializers.PrimaryKeyRelatedField(many=True, queryset=Company.objects.all())

    def create(self, validated_data=None):
        data = validated_data or self.validated_data

        companies_data = data.pop('companies', None)

        operator = Operator.objects.create(**data)

        if companies_data:
            operator.companies.add(*companies_data)

        return operator


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


class ProviderCreateSerializer(extendable_serializer(Provider)):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    companies = serializers.PrimaryKeyRelatedField(many=True, queryset=Company.objects.all().not_deleted(), default=[])
    notes = NoteSerializer(many=True, default=[])

    def create(self, business_name, validated_data=None):
        data = validated_data or self.validated_data
        extras = data.pop('extra', {})
        companies = data.pop('companies', [])
        notes = data.pop('notes', [])

        provider = Provider.objects.create(**data)
        if companies:
            provider.companies.add(*companies)
        if notes:
            note_instances = NoteSerializer.create_instances(notes)
            provider.notes.add(*note_instances)

        manage_extra_attrs(business_name, provider, extras)

        return provider


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
            recipient.companies.add(*companies)
        if notes:
            note_instances = NoteSerializer.create_instances(notes)
            recipient.notes.add(*note_instances)

        manage_extra_attrs(business_name, recipient, extras)

        return recipient


class RequesterCreateSerializer(generic_serializer(Requester)):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    companies = serializers.PrimaryKeyRelatedField(many=True, queryset=Company.objects.all().not_deleted(), default=[])

    def create(self, business_name, validated_data=None):
        data = validated_data or self.validated_data
        companies = data.pop('companies', [])

        requester = Requester.objects.create(**data)
        if companies:
            requester.companies.add(*companies)

        return requester


class ServiceCreateSerializer(ServiceNoProviderSerializer):
    business = BusinessField()
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

        service = Service.objects.create(**data)
        manage_extra_attrs(service.business, service, extras)

        return service.id
    
class ServiceAreaCreateSerializer(generic_serializer(ServiceArea)):
    provider = serializers.PrimaryKeyRelatedField(queryset=Provider.objects.all())

    class Meta:
        model = ServiceArea
        fields = '__all__'
    
    def create(self, validated_data=None) -> int:
        data = validated_data or self.validated_data

        service_area = ServiceArea.objects.create(**data)
        
        return service_area.id
    

class ServiceRootCreateSerializer(generic_serializer(ServiceRoot)):
    categories = serializers.PrimaryKeyRelatedField(many=True, queryset=Category.objects.all())

    def create(self, validated_data=None) -> int:
        data = validated_data or self.validated_data
        categories_data = data.pop('categories', None)
        service_root = ServiceRoot.objects.create(**data)
        if categories_data:
            service_root.categories.add(*categories_data)
        return service_root.id


class UserCreateSerializer(UserSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True, validators=[validate_password])
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

    def create(self, provider_data, validated_data=None):
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
            contact_instances = ContactSerializer.create_instances(contacts_data)
            user.contacts.add(*contact_instances)

        if location_data:
            user.location = Location.objects.create(**location_data)
            user.save()

        if provider_data is not None:
            provider_group = get_or_create_provider_group()
            user.groups.add(provider_group)
        else:
            operators_group = get_or_create_operators_group()
            user.groups.add(operators_group)

        user_sync_email_with_contact(user)

        return user


class OfferCreateSerializer(extendable_serializer(Offer)):
    booking = serializers.PrimaryKeyRelatedField(queryset=Booking.objects.all())
    service = serializers.PrimaryKeyRelatedField(queryset=Service.objects.all())

    class Meta:
        model = Offer
        fields = '__all__'

    def create(self, business, validated_data=None) -> int:
        data: dict = validated_data or self.validated_data
        extras = data.pop('extra', {})

        offer = Offer.objects.create(**data)
        manage_extra_attrs(business, offer, extras)

        return offer.id


class ReportCreateSerializer(extendable_serializer(Report)):
    event = serializers.PrimaryKeyRelatedField(queryset=Event.objects.all())

    class Meta:
        model = Report
        fields = '__all__'

    def create(self, business, validated_data=None) -> int:
        data: dict = validated_data or self.validated_data
        extras = data.pop('extra', None)
        
        report = Report.objects.create(**data)
        manage_extra_attrs(business, report, extras)

    
class CompanyRelationshipCreateSerializer(CompanyRelationshipSerializer):
    def create(self, validated_data=None) -> int:
        data: dict = validated_data or self.validated_data

        company_relationship = CompanyRelationship.objects.create(**data)

        return company_relationship