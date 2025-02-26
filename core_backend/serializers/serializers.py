from typing import List
from django.db.models import Prefetch
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from core_backend.models import Admin, Affiliation, Agent, Authorization, Booking, Company, CompanyRelationship, Contact, Event, GlobalSetting, \
    Invoice, Language, Ledger, Location, Notification, Offer, Operator, Payer, Provider, Rate, Recipient, Report, Requester, \
    Service, ServiceArea, ServiceRoot
from core_backend.serializers.serializer_user import UserSerializer, user_subtype_serializer
from core_backend.serializers.serializers_plain import CategorySerializer, ContactSerializer, ExpenseSerializer, \
    ExtraAttrSerializer, \
    LocationSerializer, \
    NoteSerializer
from core_backend.serializers.serializers_utils import BaseSerializer, extendable_serializer, \
    generic_serializer
from core_backend.services.core_services import fetch_updated_from_validated_data

class ChangePasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(required=True)

class GetUser(serializers.Serializer):
    email = serializers.CharField(required=True)

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
    categories = CategorySerializer(many=True)

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
                    'categories',
                    queryset=CategorySerializer.get_default_queryset(),
                ),
            )
        )


# Serializers
class RateSerializer(extendable_serializer(Rate)):
    root = ServiceRootBaseSerializer(required=False)
    class Meta:
        model = Rate
        fields = '__all__'

    @staticmethod
    def get_default_queryset():
        return (
            Rate.objects
            .all()
            .not_deleted()
            .prefetch_related(
                Prefetch(
                    'root',
                    queryset=ServiceRootBaseSerializer.get_default_queryset(),
                )
            )
        )

class CompanySerializer(extendable_serializer(Company)):
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
                )
            )
        )
    

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
            set(instance.company_relationships_from.all().values_list('id'))
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


class CompanyRelationshipWithCompaniesSerializer(CompanyRelationshipSerializer):
    company_to = CompanySerializer()

    @staticmethod
    def get_default_queryset():
        return (
            super(CompanyRelationshipWithCompaniesSerializer, CompanyRelationshipWithCompaniesSerializer)
            .get_default_queryset()
            .prefetch_related(
                Prefetch(
                    'company_to',
                    queryset=CompanySerializer.get_default_queryset()
                )
            )
        )


class CompanyWithParentSerializer(CompanySerializer):
    parent_company = CompanySerializer()
    rates = RateSerializer(many=True, required=False)
    company_relationships_from = CompanyRelationshipSerializer(many=True, default=[])

    @staticmethod
    def get_default_queryset():
        return (
            super(CompanyWithParentSerializer, CompanyWithParentSerializer)
            .get_default_queryset()
            .prefetch_related(
                Prefetch(
                    'parent_company',
                    queryset=CompanySerializer.get_default_queryset()
                ),
                Prefetch(
                    'rates',
                    queryset=RateSerializer.get_default_queryset()
                ),
                 Prefetch(
                    'company_relationships_from',
                    queryset=CompanyRelationshipSerializer.get_default_queryset()
                ),
            )
        )


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

class GlobalSettingSerializer(extendable_serializer(GlobalSetting)):
    rates = RateSerializer(many=True, required=False)

    class Meta:
        model = GlobalSetting
        fields = '__all__'

    @staticmethod
    def get_default_queryset():
        return (
            GlobalSetting.objects
            .all()
            .not_deleted()
            .prefetch_related(
                Prefetch(
                    'rates',
                    queryset=RateSerializer.get_default_queryset()
                ),
                Prefetch(
                    'extra',
                    queryset=ExtraAttrSerializer.get_default_queryset()
                )
            )
        )

# Roles serializers
class AdminSerializer(user_subtype_serializer(Admin)):
    role = serializers.CharField()

    @staticmethod
    def get_default_queryset():
        return (
            Admin.objects
            .all()
            .not_deleted('user')
            .prefetch_related(
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

class AgentSerializer(user_subtype_serializer(Agent)):
    companies = serializers.PrimaryKeyRelatedField(many=True, queryset=Company.objects.all().not_deleted())
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
                    queryset=Company.objects.all().not_deleted()
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


class AgentWithCompaniesSerializer(AgentSerializer):
    companies = CompanyWithParentSerializer(many=True)

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
                )
            )
        )


class OperatorNoCompaniesSerializer(user_subtype_serializer(Operator)):

    class Meta:
        model = Operator
        exclude = ('companies',)

    @staticmethod
    def get_default_queryset():
        return (
            Operator.objects
            .all()
            .not_deleted('user')
            .prefetch_related(
                Prefetch(
                    'user',
                    queryset=UserSerializer.get_default_queryset(),
                ),
            )
        )

class OperatorSerializer(OperatorNoCompaniesSerializer):
    companies = CompanyWithParentSerializer(many=True)

    class Meta:
        model = Operator
        fields = '__all__'

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
                'user',
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


class ServiceAreaSerializer(BaseSerializer):
    class Meta:
        model = ServiceArea
        fields = '__all__'
    
    @staticmethod
    def get_default_queryset():
        return (
            ServiceArea.objects
            .all()
            .not_deleted()
            .prefetch_related(
                Prefetch(
                    'provider',
                    queryset=ProviderNoServiceSerializer.get_default_queryset(),
                ),
            )
        )

class ProviderNoServiceSerializer(user_subtype_serializer(Provider)):
    companies = serializers.PrimaryKeyRelatedField(many=True, default=[], queryset=Company.objects.all().not_deleted())

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
                'notes',
                'extra',
                'user',
            )
        )


class ProviderSerializer(ProviderNoServiceSerializer):
    services = ServiceNoProviderSerializer(many=True)

    @staticmethod
    def get_default_queryset():
        return (
            Provider.objects
            .all()
            .not_deleted('user')
            .prefetch_related(
                Prefetch(
                    'services',
                    queryset=ServiceNoProviderSerializer.get_default_queryset(),
                ),
                Prefetch(
                    'service_areas',
                    queryset=ServiceAreaSerializer.get_default_queryset(),
                ),
            )
        )
    
class ServiceNoRootSerializer(ServiceNoProviderSerializer):
    provider = ProviderNoServiceSerializer()

    class Meta:
        model = Service
        fields = [
        "id",
        "bill_rate",
        "bill_amount",
        "is_deleted",
        "bill_rate_type",
        "bill_min_payment",
        "bill_no_show_fee",
        "bill_rate_minutes_threshold",
        "business",
        "provider"]

    @staticmethod
    def get_default_queryset():
        return (
            super(ServiceSerializer, ServiceSerializer)
            .get_default_queryset()
            .prefetch_related(
                Prefetch(
                    'provider',
                    queryset=ProviderNoServiceSerializer.get_default_queryset(),
                ),
            )
        )
    

class ServiceSerializer(ServiceNoProviderSerializer):
    provider = ProviderNoServiceSerializer()
    class Meta:
        model = Service
        fields = '__all__'


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

class ServiceRootBookingSerializer(ServiceRootNoBookingSerializer):
    bookings = serializers.PrimaryKeyRelatedField(queryset=Booking.objects.all(), many=True)

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
            )
        )


class AffiliationNoRecipientSerializer(generic_serializer(Affiliation)):
    company = CompanyWithParentSerializer()

    class Meta:
        model = Affiliation
        fields = ('id', 'company',)

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
            )
        )



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

    @staticmethod
    def get_default_queryset():
        return (
            super(RecipientSerializer, RecipientSerializer)
            .get_default_queryset()
            .prefetch_related(
                Prefetch(
                    'affiliations',
                    queryset=AffiliationNoRecipientSerializer.get_default_queryset(),
                ),
            )
        )

class RequesterNoCompaniesSerializer(user_subtype_serializer(Requester)):

    class Meta:
        model = Requester
        exclude = ('companies', )

    @staticmethod
    def get_default_queryset():
        return (
            Requester.objects
            .all()
            .not_deleted('user')
            .prefetch_related(
                Prefetch(
                    'user',
                    queryset=UserSerializer.get_default_queryset(),
                ),
            )
        )

class RequesterSerializer(RequesterNoCompaniesSerializer):
    companies = CompanyWithParentSerializer(many=True)

    class Meta:
        model = Requester
        fields = '__all__'

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
                'user',
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
    
class ReportSerializer(BaseSerializer):
    class Meta:
        model = Report
        fields = '__all__'

    @staticmethod
    def get_default_queryset():
        return (
            Report.objects.all().not_deleted()
        )

class ChildrenBooking(extendable_serializer(Booking)):
    
    class Meta:
        model = Booking
        fields = ('id', 'public_id')
        
    @staticmethod
    def get_default_queryset():
        return (
            Booking.objects.all().not_deleted('business')
        )

class BookingNoEventsSerializer(extendable_serializer(Booking)):
    public_id = serializers.ReadOnlyField()
    children = ChildrenBooking(many=True, default=[])
    companies = CompanyWithParentSerializer(many=True)
    events_count = serializers.IntegerField(source='events.count', read_only=True)
    expenses = ExpenseSerializer(many=True)
    operators = OperatorNoCompaniesSerializer(many=True)
    parent = serializers.PrimaryKeyRelatedField(queryset=Booking.objects.all().not_deleted('business'), allow_null=True)
    services = ServiceNoRootSerializer(many=True)
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
                    'children',
                    queryset=ChildrenBooking.get_default_queryset(),
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
    
class BookingNoEventsHistorySerializer(BookingNoEventsSerializer):
    history = serializers.SerializerMethodField()

    def get_history(self, value):
        history = []
        for obj in value.history.all():
            history_item = {
                "history_id": obj.history_id,
                "id": obj.id,
                "is_deleted": obj.is_deleted,
                "created_at": obj.created_at,
                "public_id": obj.public_id,
                "history_date": obj.history_date,
                "history_change_reason": obj.history_change_reason,
                "history_type": obj.history_type,
                "business": obj.business.id,
                "parent": obj.parent.id if obj.parent is not None else "No Exist",
                "history_user": obj.history_user.username,
            }
            # Include related fields from prefetch
            history_item['categories'] = CategorySerializer(value.categories.all(), many=True).data
            def representation_categories(repr):
                return {
                    "id": repr["id"],
                    "name": repr["name"],
                }
            history_item['categories'] = map(representation_categories, history_item['categories'])

            history_item['companies'] = CompanyWithParentSerializer(value.companies.all(), many=True).data
            def representation_companies(repr):
                return {
                    "id": repr["id"],
                    "name": repr["name"],
                }
            history_item['companies'] = map(representation_companies, history_item['companies'])

            history_item['notes'] = NoteSerializer(value.notes.all(), many=True).data
            
            history_item['offers']=OfferSerializer(value.offers.all(), many=True).data,
            
            history_item['expenses'] = ExpenseSerializer(value.expenses.all(), many=True).data
            
            history_item['extra'] = ExtraAttrSerializer(value.extra.all(), many=True).data
            
            history_item['operators'] = OperatorSerializer(value.operators.all(), many=True).data
            def representation_operators(repr):
                return {
                    "id": repr["id"],
                    "user_id": repr["user_id"],
                    "username": repr["username"],
                }
            history_item['operators'] = map(representation_operators, history_item['operators'])
            
            history_item['services'] = ServiceSerializer(value.services.all(), many=True).data
            def representation_services(repr):
                return {
                    "id": repr["id"],
                    "bill_rate": repr["bill_rate"],
                    "bill_amount": repr["bill_amount"],
                    "contract_type": repr["provider"]["contract_type"],
                    "user_id": repr["provider"]["user_id"],
                    "username": repr["provider"]["username"],
                }
            history_item['services'] = map(representation_services, history_item['services'])

            history_item['service_root'] = ServiceRootBaseSerializer.get_default_queryset()
            def representation_service_root(repr):
                return {
                    "id": repr.id,
                    "name": repr.name,
                }
            history_item['service_root'] = map(representation_service_root, history_item['service_root'])
            # Add the history item to the list
            history.append(history_item)
        
        return history

class EventNoBookingSerializer(extendable_serializer(Event)):
    affiliates = AffiliationSerializer(many=True)
    agents = AgentWithCompaniesSerializer(many=True)
    authorizations = AuthorizationBaseSerializer(many=True)
    booking = serializers.PrimaryKeyRelatedField(queryset=Booking.objects.all().not_deleted('business'))
    payer = PayerSerializer(required=False)
    payer_company = CompanyWithParentSerializer(required=False)
    reports = ReportSerializer(many=True)
    requester = RequesterNoCompaniesSerializer()

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
                    'extra',
                    queryset=ExtraAttrSerializer.get_default_queryset(),
                ),
                Prefetch(
                    'agents',
                    queryset=AgentWithCompaniesSerializer.get_default_queryset(),
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

    @staticmethod
    def get_default_queryset():
        return (
            super(EventSerializer, EventSerializer)
            .get_default_queryset()
            .prefetch_related(
                Prefetch(
                    'booking',
                    queryset=BookingNoEventsSerializer.get_default_queryset(),
                ),
            )
        )
    
class InvoiceSerializer(BaseSerializer):
    class Meta:
        model = Invoice
        fields = '__all__'

    @staticmethod
    def get_default_queryset():
        return (
            Invoice.objects
            .all()
            .not_deleted()
        )


class LedgerSerializer(BaseSerializer):
    booking = BookingSerializer()
    event = EventSerializer()
    invoice = InvoiceSerializer()

    class Meta:
        model = Ledger
        fields = '__all__'

    @staticmethod
    def get_default_queryset():
        return (
            Ledger.objects
            .all()
            .not_deleted()
            .prefetch_related(
                Prefetch(
                    'booking',
                    queryset=BookingSerializer.get_default_queryset(),
                ),
                Prefetch(
                    'event',
                    queryset=EventSerializer.get_default_queryset(),
                ),
                Prefetch(
                    'invoice',
                    queryset=InvoiceSerializer.get_default_queryset(),
                ),
            )
        )


class CompanyWithRolesSerializer(CompanyWithParentSerializer):
    agents = AgentSerializer(many=True)
    operators = OperatorSerializer(many=True)
    payers = PayerSerializer(many=True)
    providers = ProviderNoServiceSerializer(many=True)
    recipients = RecipientSerializer(many=True)
    requesters = RequesterSerializer(many=True)

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
                    'agents',
                    queryset=AgentSerializer.get_default_queryset(),
                ),
                Prefetch(
                    'operators',
                    queryset=OperatorSerializer.get_default_queryset(),
                ),
                Prefetch(
                    'payers',
                    queryset=PayerSerializer.get_default_queryset(),
                ),
                Prefetch(
                    'providers',
                    queryset=ProviderNoServiceSerializer.get_default_queryset(),
                ),
                Prefetch(
                    'recipients',
                    queryset=RecipientSerializer.get_default_queryset(),
                ),
                Prefetch(
                    'requesters',
                    queryset=RequesterSerializer.get_default_queryset(),
                ),
                Prefetch(
                    'rates',
                    queryset=RateSerializer.get_default_queryset(),
                )
                )
            )


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
