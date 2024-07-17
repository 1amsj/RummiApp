from django.db.models import Prefetch
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from core_backend.models import Admin, Booking, Agent, Company, Event, Requester, Recipient, Affiliation, \
    SoftDeletionQuerySet, User, Provider, Service
from core_backend.serializers.serializer_user import user_subtype_serializer
from core_backend.serializers.serializers_utils import extendable_serializer, generic_serializer
from core_backend.serializers.serializers import EventNoBookingSerializer, BookingSerializer, EventSerializer, \
    ContactSerializer, BaseSerializer, LocationSerializer, NoteSerializer, ExtraAttrSerializer, \
    AuthorizationBaseSerializer, ServiceRootBaseSerializer, ServiceSerializer, CompanyWithParentSerializer


class UserLightSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    user_id = serializers.ReadOnlyField(source='id')
    date_of_birth = serializers.DateField(allow_null=True, required=False)

    class Meta:
        model = User
        fields = [
            'id',
            'user_id',
            'username',
            'first_name',
            'last_name',
            'date_of_birth',
            'is_operator',
            'is_provider',
            'is_recipient',
            'is_requester',
            'is_payer',
        ]

    @staticmethod
    def get_default_queryset() -> SoftDeletionQuerySet:
        return (
            User.objects
            .all()
            .not_deleted()
        )

class ProviderNoServiceLightSerializer(user_subtype_serializer(Provider)):
    user = UserLightSerializer()
    class Meta:
        model = Provider
        fields = [
            'id', 
            'user',
        ]

    @staticmethod
    def get_default_queryset():
        return (
            Provider.objects
            .all()
            .not_deleted('user')
            .prefetch_related(
                Prefetch(
                    'extra',
                    queryset=ExtraAttrSerializer.get_default_queryset(),
                ),
                Prefetch(
                    'user',
                    queryset=UserLightSerializer.get_default_queryset(),
                ),
            )
        )

class ServiceNoProviderLightSerializer(extendable_serializer(Service)):
    root = ServiceRootBaseSerializer(required=False)
    bill_rate = serializers.DecimalField(max_digits=32, decimal_places=2)
    bill_amount = serializers.IntegerField()

    class Meta:
        model = Service
        fields = '__all__'

    def validate(self, data: dict):
        if data.get('bill_amount') < 0:
            raise serializers.ValidationError(_('Bill amount could not be negative'))

        return super(ServiceNoProviderLightSerializer, self).validate(data)

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

class ServiceNoRootLightSerializer(ServiceNoProviderLightSerializer):
    provider = ProviderNoServiceLightSerializer()
    
    class Meta:
        model = Service
        fields = [
            "id",
            "business",
            "provider"
        ]

    @staticmethod
    def get_default_queryset():
        return (
            super(ServiceSerializer, ServiceSerializer)
            .get_default_queryset()
            .prefetch_related(
                Prefetch(
                    'provider',
                    queryset=ProviderNoServiceLightSerializer.get_default_queryset(),
                ),
            )
        )
    

class BookingLightNoEventsSerializer(extendable_serializer(Booking)):
    public_id = serializers.ReadOnlyField()
    services = ServiceNoRootLightSerializer(many=True)
    companies = CompanyWithParentSerializer(many=True)

    class Meta:
        model = Booking
        fields = ['id', 'business', 'public_id', 'services', 'companies']
        
    @staticmethod
    def get_default_queryset():
        return (
            Booking.objects
            .all()
            .not_deleted('business')
            .prefetch_related(
            Prefetch(
                    'companies',
                    queryset=CompanyWithParentSerializer.get_default_queryset(),
                ),
            )
        )

class CompanyLightSerializer(BaseSerializer):

    class Meta:
        model = Company
        fields = ['id', 'name', 'send_method']

    @staticmethod
    def get_default_queryset():
        return (
            Company.objects
            .all()
            .not_deleted()
        )       

class RecipientNoAffiliationLightSerializer(user_subtype_serializer(Recipient)):
    user = UserLightSerializer()
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
                    'user',
                    queryset=UserLightSerializer.get_default_queryset(),
                ),
            )
        )

class AffiliationLightSerializer(generic_serializer(Affiliation)):
    recipient = RecipientNoAffiliationLightSerializer()

    @staticmethod
    def get_default_queryset():
        return (
            Affiliation.objects
            .all()
            .not_deleted()
            .prefetch_related(
                Prefetch(
                    'recipient',
                    queryset=RecipientNoAffiliationLightSerializer.get_default_queryset(),
                ),
            )
        )


class AgentLightSerializer(user_subtype_serializer(Agent)):
    companies = CompanyLightSerializer(many=True)
    role = serializers.CharField()
    user = UserLightSerializer()
    
    @staticmethod
    def get_default_queryset():
        return (
            Agent.objects
            .all()
            .not_deleted('user')
            .prefetch_related(
                Prefetch(
                    'companies',
                    queryset=CompanyLightSerializer.get_default_queryset()
                ),
                Prefetch(
                    'extra',
                    queryset=ExtraAttrSerializer.get_default_queryset(),
                ),
                Prefetch(
                    'user',
                    queryset=UserLightSerializer.get_default_queryset(),
                ),
            )
        )
        
class AdminLightSerializer(user_subtype_serializer(Admin)):
    role = serializers.CharField()
    user = UserLightSerializer()
    
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
                    queryset=UserLightSerializer.get_default_queryset(),
                ),
            )
        )
        
class RequesterLightSerializer(user_subtype_serializer(Requester)):
    companies = CompanyLightSerializer(many=True)
    user = UserLightSerializer()
    
    @staticmethod
    def get_default_queryset():
        return (
            Requester.objects
            .all()
            .not_deleted('user')
            .prefetch_related(
                Prefetch(
                    'companies',
                    queryset=CompanyLightSerializer.get_default_queryset()
                ),
                Prefetch(
                    'user',
                    queryset=UserLightSerializer.get_default_queryset(),
                ),
            )
        )

class EventNoBookingLightSerializer(extendable_serializer(Event)):
    affiliates = AffiliationLightSerializer(many=True)
    agents = AgentLightSerializer(many=True)
    authorizations = AuthorizationBaseSerializer(many=True)
    booking = serializers.PrimaryKeyRelatedField(queryset=Booking.objects.all().not_deleted('business'))
    requester = RequesterLightSerializer()

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
                    queryset=AffiliationLightSerializer.get_default_queryset(),
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
                    'requester',
                    queryset=RequesterLightSerializer.get_default_queryset(),
                ),
            )
        )
        
class EventLightSerializer(EventNoBookingLightSerializer):
    booking = BookingLightNoEventsSerializer()

    @staticmethod
    def get_default_queryset():
        return (
            super(EventSerializer, EventSerializer)
            .get_default_queryset()
            .prefetch_related(
                Prefetch(
                    'booking',
                    queryset=BookingLightNoEventsSerializer.get_default_queryset(),
                ),
            )
        )