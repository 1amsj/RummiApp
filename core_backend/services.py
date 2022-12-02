from functools import lru_cache
from typing import Iterator, Tuple, Type, Union

from django.contrib.contenttypes.models import ContentType
from django.db import models

import core_backend.models as app_models
from core_api.constants import FIELDS_BLACKLIST
from core_backend.datastructures import QueryParams
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
        raise ModelNotExtendableException(f"{str(model)} is not an extendable model")


@lru_cache(maxsize=None)
def get_model_fields(model: Type[models.Model]):
    return model._meta.get_fields()


@lru_cache(maxsize=None)
def get_model_field_names(model: Type[models.Model]):
    return [f.name for f in get_model_fields(model)]


def iter_base_attrs(model: Type[models.Model], fields: dict) -> Iterator[Tuple[str, str]]:
    names = get_model_field_names(model)
    for (k, v) in fields.items():
        k_base = k.split('__')[0]
        if k_base not in names or k_base in FIELDS_BLACKLIST:
            continue
        yield k, v


def filter_base_attrs(model: Type[models.Model], fields: dict) -> dict:
    return {
        k: v
        for (k, v) in iter_base_attrs(model, fields)
    }


def iter_extra_attrs(model: Type[models.Model], fields: dict) -> Iterator[Tuple[str, str]]:
    assert_extendable(model)
    names = get_model_field_names(model)
    for (k, v) in fields.items():
        k_base = k.split('__')[0]
        if k_base in names or k_base in FIELDS_BLACKLIST:
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


def filter_params(model: Type[models.Model], params: QueryParams) -> Tuple[QueryParams, QueryParams, QueryParams]:
    field_names = get_model_field_names(model)
    base_params = QueryParams()
    nested_params = QueryParams()
    extra_params = QueryParams()
    for (f, p) in params.items():
        if f in FIELDS_BLACKLIST:
            continue

        if isinstance(p, QueryParams):
            nested_params[f] = p

        else:
            (base_params if f in field_names else extra_params)[f] = p

    return base_params, extra_params, nested_params


def sync_sets(original_set, new_set, add, remove):
    original_set = set(original_set)
    new_set = set(new_set)

    deleted = original_set.difference(new_set)
    if deleted:
        remove(*deleted)

    created = new_set.difference(original_set)
    if created:
        add(*created)


def sync_m2m(manager, new_set, field='id'):
    return sync_sets(
        manager.all().values_list(field, flat=True),
        new_set,
        manager.add,
        manager.remove,
    )
