from typing import Type

from django.db import models
from rest_framework import serializers

from core_backend.models import ExtendableModel, SoftDeletionQuerySet
from core_backend.services import assert_extendable, get_model_field_names, \
    is_extendable


class BaseSerializer(serializers.ModelSerializer):
    @staticmethod
    def get_default_queryset() -> SoftDeletionQuerySet:
        raise NotImplementedError


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
