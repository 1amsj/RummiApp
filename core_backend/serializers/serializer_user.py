from typing import Type

from django.db.models import Prefetch
from rest_framework import serializers

from core_backend.models import SoftDeletableModel, SoftDeletionQuerySet, User
from core_backend.serializers.serializers_plain import ContactSerializer, LocationSerializer
from core_backend.serializers.serializers_utils import BaseSerializer, extendable_serializer
from core_backend.services.core_services import is_extendable


# User needs to be in this file to avoid circular imports
class UserSerializer(serializers.ModelSerializer):
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
    admin_id = serializers.PrimaryKeyRelatedField(many=True, allow_null=True, read_only=True, source='as_admin')
    date_of_birth = serializers.DateField(allow_null=True, required=False)

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
            'admin_id',
            'is_operator',
            'is_provider',
            'is_recipient',
            'is_requester',
            'is_payer',
        )

    @staticmethod
    def get_default_queryset() -> SoftDeletionQuerySet:
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
