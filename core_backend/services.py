from typing import Iterator, Tuple, Type, Union

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import QuerySet

import core_backend.models as app_models
from core_api.constants import KEYS_BLACKLIST
from core_backend.exceptions import ModelNotExtendableException


def is_extendable(model: Type[models.Model]) -> bool:
    """Checks if a model is a subtype of ExtendableModel"""
    return issubclass(model, app_models.ExtendableModel)


def assert_extendable(model: Type[models.Model]):
    """
    Raises an exception if the type is not a subtype of Extendable Model
    :raise ModelNotExtendableException
    """
    if not is_extendable(model):
        raise ModelNotExtendableException()


def iter_base_attrs(model: Type[models.Model], fields: dict) -> Iterator[Tuple[str, str]]:
    model_fields = model._meta.get_fields()
    names = [f.name for f in model_fields]
    for (k, v) in fields.items():
        k_base = k.split('__')[0]
        if k_base not in names or k_base in KEYS_BLACKLIST:
            continue
        yield k, v


def filter_base_attrs(model: Type[models.Model], fields: dict) -> dict:
    return {
        k: v
        for (k, v) in iter_base_attrs(model, fields)
    }


def iter_extra_attrs(model: Type[models.Model], fields: dict) -> Iterator[Tuple[str, str]]:
    assert_extendable(model)
    model_fields = model._meta.get_fields()
    names = [f.name for f in model_fields]
    for (k, v) in fields.items():
        k_base = k.split('__')[0]
        if k_base in names or k_base in KEYS_BLACKLIST:
            continue
        yield k, v


def filter_extra_attrs(model: Type[models.Model], fields: dict) -> dict:
    return {
        k: v
        for (k, v) in iter_extra_attrs(model, fields)
    }


def manage_extra_attrs(business: Union[str, app_models.Business], inst: models.Model, fields: dict):
    if isinstance(business, str):
        business = app_models.Business.objects.get(name=business)
    model = inst.__class__
    ct = ContentType.objects.get_for_model(model)
    for (k, v) in iter_extra_attrs(model, fields):
        app_models.Extra.objects.update_or_create(
            business=business,
            parent_ct=ct,
            parent_id=inst.id,
            key=k,
            defaults={
                'value': v,
            }
        )


# TODO review usage
def filter_queryset(model: Type[models.Model], queryset: QuerySet[models.Model], params: dict):
    base_attrs_filters = filter_base_attrs(model, params)
    if base_attrs_filters:
        queryset = queryset.filter(**base_attrs_filters)

    if is_extendable(model):
        extra_filters = filter_extra_attrs(model, params)
        if extra_filters:
            # noinspection PyUnresolvedReferences
            queryset = queryset.filter_by_extra(**extra_filters)

    return queryset


def filter_attrs(model: Type[models.Model], fields: dict) -> Tuple[dict, dict]:
    model_fields = model._meta.get_fields()
    names = [f.name for f in model_fields]
    base_attrs = {}
    other_attrs = {}
    for (k, v) in fields.items():
        k_base = k.split('__')[0]
        if k_base in KEYS_BLACKLIST:
            continue
        (base_attrs if k_base in names else other_attrs)[k] = v
    return base_attrs, other_attrs
