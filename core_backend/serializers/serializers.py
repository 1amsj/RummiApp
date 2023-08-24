from django.db.models import Prefetch
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from core_backend.models import Affiliation, Agent, Authorization, Booking, Company, Contact, Event, \
    Invoice, Language, Ledger, Location, Notification, Offer, Operator, Payer, Provider, Recipient, Report, Requester, \
    Service, ServiceRoot, SoftDeletionQuerySet
from core_backend.serializers.serializer_user import UserSerializer, user_subtype_serializer
from core_backend.serializers.serializers_plain import CategorySerializer, ContactSerializer, ExpenseSerializer, \
    ExtraAttrSerializer, \
    LocationSerializer, \
    NoteSerializer
from core_backend.serializers.serializers_utils import BaseSerializer, extendable_serializer, \
    generic_serializer


# Base serializers
class AuthorizationBaseSerializer(BaseSerializer):
    authorizer = serializers.PrimaryKeyRelatedField(queryset=Payer.objects.all().not_deleted())
    company = serializers.PrimaryKeyRelatedField(queryset=Company.objects.all().not_deleted())
    contact = serializers.PrimaryKeyRelatedField(required=False, queryset=Contact.objects.all().not_deleted())
    events = serializers.PrimaryKeyRelatedField(many=True, queryset=Event.objects.all().not_deleted())

    class Meta:
        model = Authorization
        fields = '__all__'

    @staticmethod
    def get_default_queryset():
        return (
            Authorization.objects
            .all()
            .not_deleted()
            .prefetch_related(
                Prefetch(
                    'authorizer',
                    queryset=Payer.objects.all().not_deleted(),
                ),
                Prefetch(
                    'company',
                    queryset=Company.objects.all().not_deleted(),
                ),
                Prefetch(
                    'contact',
                    queryset=Contact.objects.all().not_deleted(),
                ),
                Prefetch(
                    'events',
                    queryset=Event.objects.all().not_deleted(),
                ),
            )
        )


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


# Serializers
class CompanySerializer(BaseSerializer):
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


class CompanyWithParentSerializer(CompanySerializer):
    parent_company = CompanySerializer()


class LanguageSerializer(BaseSerializer):
    class Meta:
        model = Language
        fields = '__all__'

    @staticmethod
    def get_default_queryset():
        return (
            Language.objects
            .all()
            .not_deleted()
        )


# Roles serializers
class AgentSerializer(user_subtype_serializer(Agent)):
    companies = CompanyWithParentSerializer(many=True)
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
                    queryset=CompanyWithParentSerializer.get_default_queryset()
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


class OperatorSerializer(user_subtype_serializer(Operator)):
    companies = CompanyWithParentSerializer(many=True)

    @staticmethod
    def get_default_queryset():
        return (
            Operator.objects
            .all()
            .not_deleted('user')
            .prefetch_related(
                Prefetch(
                    'companies',
                    queryset=CompanyWithParentSerializer.get_default_queryset()
                ),
                Prefetch(
                    'user',
                    queryset=UserSerializer.get_default_queryset(),
                ),
            )
        )


class PayerSerializer(PayerBaseSerializer):
    companies = CompanyWithParentSerializer(many=True)

    @staticmethod
    def get_default_queryset():
        return (
            super(PayerSerializer, PayerSerializer)
            .get_default_queryset()
            .prefetch_related(
                Prefetch(
                    'companies',
                    queryset=CompanyWithParentSerializer.get_default_queryset()
                ),
            )
        )


class ServiceNoProviderSerializer(extendable_serializer(Service)):
    root = ServiceRootBaseSerializer(required=False)
    bill_rate = serializers.DecimalField(max_digits=32, decimal_places=2)
    bill_amount = serializers.IntegerField()

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
    companies = CompanyWithParentSerializer(many=True)
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
                    queryset=CompanyWithParentSerializer.get_default_queryset()
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


class AffiliationNoRecipientSerializer(generic_serializer(Affiliation)):
    company = CompanyWithParentSerializer()

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
                    queryset=CompanyWithParentSerializer.get_default_queryset(),
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
    company = CompanyWithParentSerializer()
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
                    queryset=CompanyWithParentSerializer.get_default_queryset(),
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


class RecipientSerializer(RecipientNoAffiliationSerializer):
    affiliations = AffiliationNoRecipientSerializer(many=True, read_only=True)


class RequesterSerializer(user_subtype_serializer(Requester)):
    companies = CompanyWithParentSerializer(many=True)

    @staticmethod
    def get_default_queryset():
        return (
            Requester.objects
            .all()
            .not_deleted('user')
            .prefetch_related(
                Prefetch(
                    'companies',
                    queryset=CompanyWithParentSerializer.get_default_queryset()
                ),
                Prefetch(
                    'user',
                    queryset=UserSerializer.get_default_queryset(),
                ),
            )
        )



class OfferSerializer(BaseSerializer):
    booking = serializers.PrimaryKeyRelatedField(queryset=Booking.objects.all().not_deleted('business'))
    service = ServiceSerializer()

    class Meta:
        model = Offer
        fields = '__all__'

    @staticmethod
    def get_default_queryset():
        return (
            Offer.objects
            .all()
            .not_deleted()
        )


class BookingNoEventsSerializer(extendable_serializer(Booking)):
    categories = CategorySerializer(many=True)
    children = serializers.PrimaryKeyRelatedField(many=True, default=[], queryset=Booking.objects.all().not_deleted('business'))
    companies = CompanyWithParentSerializer(many=True)
    events_count = serializers.IntegerField(source='events.count', read_only=True)
    expenses = ExpenseSerializer(many=True)
    operators = OperatorSerializer(many=True)
    parent = serializers.PrimaryKeyRelatedField(queryset=Booking.objects.all().not_deleted('business'), allow_null=True)
    services = ServiceSerializer(many=True)
    notes = NoteSerializer(many=True, default=[])
    offers = OfferSerializer(many=True, default=[])
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
                    queryset=CompanyWithParentSerializer.get_default_queryset(),
                ),
                Prefetch(
                    'notes',
                    queryset=NoteSerializer.get_default_queryset()
                ),
                Prefetch(
                    'offers',
                    queryset=OfferSerializer.get_default_queryset(),
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


class ReportSerializer(BaseSerializer):
    class Meta:
        model = Report
        fields = '__all__'

    @staticmethod
    def get_default_queryset():
        return (
            Report.objects.all().not_deleted()
        )


class EventNoBookingSerializer(extendable_serializer(Event)):
    affiliates = AffiliationSerializer(many=True)
    agents = AgentSerializer(many=True)
    authorizations = AuthorizationBaseSerializer(many=True)
    booking = serializers.PrimaryKeyRelatedField(queryset=Booking.objects.all().not_deleted('business'))
    payer = PayerSerializer(required=False)
    payer_company = CompanyWithParentSerializer(required=False)
    reports = ReportSerializer(many=True)
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
                    'authorizations',
                    queryset=AuthorizationBaseSerializer.get_default_queryset(),
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
                    queryset=CompanyWithParentSerializer.get_default_queryset(),
                ),
                Prefetch(
                    'reports',
                    queryset=ReportSerializer.get_default_queryset(),
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
                ),
            )
        )


class EventSerializer(EventNoBookingSerializer):
    booking = BookingNoEventsSerializer()


InvoiceSerializer = generic_serializer(Invoice)


class LedgerSerializer(BaseSerializer):
    booking = BookingSerializer()
    event = EventSerializer()
    invoice = InvoiceSerializer()

    class Meta:
        model = Ledger
        fields = '__all__'


class CompanyWithRolesSerializer(CompanyWithParentSerializer):
    agents = AgentSerializer(many=True)
    operators = OperatorSerializer(many=True)
    payers = PayerSerializer(many=True)
    providers = ProviderSerializer(many=True)
    recipients = RecipientSerializer(many=True)
    requesters = RequesterSerializer(many=True)

    class Meta:
        model = Company
        fields = '__all__'


class AuthorizationSerializer(BaseSerializer):
    authorizer = PayerSerializer()
    company = CompanyWithParentSerializer()
    contact = ContactSerializer()
    events = EventSerializer(many=True)

    class Meta:
        model = Authorization
        fields = '__all__'

    @staticmethod
    def get_default_queryset():
        return (
            Authorization.objects
            .all()
            .not_deleted()
            .prefetch_related(
                Prefetch(
                    'authorizer',
                    queryset=PayerSerializer.get_default_queryset(),
                ),
                Prefetch(
                    'company',
                    queryset=CompanyWithParentSerializer.get_default_queryset(),
                ),
                Prefetch(
                    'contact',
                    queryset=ContactSerializer.get_default_queryset(),
                ),
                Prefetch(
                    'events',
                    queryset=EventSerializer.get_default_queryset(),
                ),
            )
        )


class NotificationSerializer(BaseSerializer):
    class Meta:
        model = Notification
        fields = '__all__'

    @staticmethod
    def get_default_queryset():
        return (
            Notification.objects
            .all()
            .not_deleted()
        )
