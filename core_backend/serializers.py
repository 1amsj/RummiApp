from typing import Type

from django.db import models
from rest_framework import serializers

from core_backend.models import Agent, Booking, Business, Category, Company, Contact, Event, ExtendableModel, Extra, \
    Invoice, Ledger, Location, Operator, Payer, Provider, Recipient, Requester, Service, User
from core_backend.services import assert_extendable, is_extendable


# Extra serializers
class ExtraAttrSerializer(serializers.ModelSerializer):
    class Meta:
        model = Extra
        fields = ('key', 'value')


class ExtendableSerializer(serializers.ModelSerializer):
    extra = serializers.SerializerMethodField('get_extra_attrs')

    class Meta:
        model = ExtendableModel
        abstract = True

    def get_extra_attrs(self, obj: ExtendableModel):
        assert_extendable(obj.__class__)
        business = self.context.get('business')
        return obj.get_extra_attrs(business)

    def to_representation(self, instance):
        """Flatten extra fields"""
        representation = super().to_representation(instance)
        extra_representation = representation.pop('extra')
        for k in extra_representation:
            representation[k] = extra_representation[k]
        return representation


# Helper
def generic_serializer(serializer_model: Type[models.Model], serializer_fields='__all__'):
    parent_serializer = (
        ExtendableSerializer
        if is_extendable(serializer_model)
        else serializers.ModelSerializer
    )

    class GenericSerializer(parent_serializer):
        class Meta:
            model = serializer_model
            fields = serializer_fields

    return GenericSerializer


# General serializers
ContactSerializer = generic_serializer(Contact)

LocationSerializer = generic_serializer(Location)


class CompanySerializer(serializers.ModelSerializer):
    contact = ContactSerializer()
    location = LocationSerializer()

    class Meta:
        model = Company
        fields = '__all__'


# User serializers
class UserSerializer(serializers.ModelSerializer):
    company = CompanySerializer()
    contact = ContactSerializer()
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
            'company',
            'contact',
            'operator_id',
            'requester_id',
        )


class CreateUserSerializer(UserSerializer):
    company = serializers.PrimaryKeyRelatedField(queryset=Company.objects.all(), allow_null=True)

    def create(self, validated_data=None):
        data = validated_data or self.validated_data
        contact = Contact.objects.create(**data.pop('contact'))
        return User.objects.create(**data, contact=contact)


def user_subtype_serializer(serializer_model: Type[models.Model]):
    serializer_parent = (
        ExtendableSerializer
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


AgentSerializer = user_subtype_serializer(Agent)

OperatorSerializer = user_subtype_serializer(Operator)

PayerSerializer = user_subtype_serializer(Payer)


class ProviderSerializer(user_subtype_serializer(Provider)):
    services = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Provider
        fields = '__all__'


class ServiceNoProviderSerializer(ExtendableSerializer):
    business = generic_serializer(Business)
    categories = generic_serializer(Category)(many=True)

    class Meta:
        model = Service
        fields = '__all__'


class ProviderServiceSerializer(user_subtype_serializer(Provider)):
    services = ServiceNoProviderSerializer(many=True)

    class Meta:
        model = Provider
        fields = '__all__'


RecipientSerializer = user_subtype_serializer(Recipient)

RequesterSerializer = user_subtype_serializer(Requester)


# Service serializers
CategorySerializer = generic_serializer(Category)

BusinessSerializer = generic_serializer(Business)


class ServiceSerializer(ExtendableSerializer):
    business = BusinessSerializer()
    categories = CategorySerializer(many=True)
    provider = ProviderSerializer()

    class Meta:
        model = Service
        fields = '__all__'


class BookingSerializer(ExtendableSerializer):
    categories = CategorySerializer(many=True)
    operators = OperatorSerializer(many=True)
    services = ServiceSerializer(many=True)

    class Meta:
        model = Booking
        fields = '__all__'


class EventSerializer(serializers.ModelSerializer):
    agents = AgentSerializer(many=True)
    booking = BookingSerializer()
    payer = PayerSerializer()
    recipients = RecipientSerializer(many=True)
    requester = RequesterSerializer()

    class Meta:
        model = Event
        fields = '__all__'


InvoiceSerializer = generic_serializer(Invoice)


class LedgerSerializer(serializers.ModelSerializer):
    booking = BookingSerializer()
    event = EventSerializer()
    invoice = InvoiceSerializer()

    class Meta:
        model = Ledger
        fields = '__all__'
