import json
from datetime import datetime
from functools import lru_cache
from typing import Dict, Iterator, List, Set, Tuple, Type, Union

from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction
from pytz import timezone

import core_backend.models as app_models
from core_api.constants import FIELDS_BLACKLIST
from core_api.exceptions import BusinessNotProvidedException
from core_backend.datastructures import Param, QueryParams
from core_backend.exceptions import ModelNotExtendableException


def is_extendable(model: Type[models.Model]) -> bool:
    """Checks if a model is a subtype of ExtendableModel"""
    return issubclass(model, app_models.ExtendableModel)


def is_soft_deletable(model: Type[models.Model]) -> bool:
    """Checks if a model is a subtype of SoftDeletableModel"""
    return issubclass(model, app_models.SoftDeletableModel)


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


def manage_extra_attrs(business: Union[None, str, app_models.Business], inst: models.Model, fields: dict):
    if not business:
        raise BusinessNotProvidedException

    if isinstance(business, str):
        business = app_models.Business.objects.get(name=business)

    model = inst.__class__
    ct = ContentType.objects.get_for_model(model)
    for (key, data) in iter_extra_attrs(model, fields):
        query = {
            'business': business,
            'parent_ct': ct,
            'parent_id': inst.id,
            'key': key,
        }

        if data is not None:
            try:
                json.loads(data)
                json_data = data
            except (json.JSONDecodeError, TypeError):
                json_data = json.dumps(str(data)) if isinstance(data, int) else json.dumps(data)

            app_models.Extra.objects.update_or_create(
                **query,
                defaults={
                    'data': json_data,
                    'is_deleted': False,
                }
            )

        else:
            app_models.Extra.objects.filter(**query).delete()


def filter_params(model_cls: Type[models.Model], params: QueryParams) -> Tuple[QueryParams, QueryParams, QueryParams]:
    model_field_names = get_model_field_names(model_cls)

    base_params = QueryParams()
    nested_params = QueryParams()
    extra_params = QueryParams()

    for (field, param) in params.items():
        if field in FIELDS_BLACKLIST:
            continue

        if field in model_field_names:
            if isinstance(param, QueryParams):
                nested_params[field] = param
            else:
                base_params[field] = param

        else:
            extra_params[field] = param

    return base_params, extra_params, nested_params


def sync_sets(original_set, new_set, add, remove):
    original_set = set(original_set)
    new_set = set(new_set)

    deleted = original_set.difference(new_set)
    if deleted:
        remove(deleted)

    created = new_set.difference(original_set)
    if created:
        add(created)


def sync_m2m(manager, new_set, field='id'):
    """Sync a many-to-many relationship based on the ids"""
    return sync_sets(
        original_set=manager.all().values_list(field, flat=True),
        new_set=new_set,
        add=lambda s: manager.add(*s),
        remove=lambda s: manager.remove(*s),
    )


def fetch_updated_from_validated_data(
        obj_type: Type[models.Model],
        dataset,
        current_ids: Set[int],
) -> Tuple[Set[models.Model], Set[models.Model], Set[int]]:
    created, updated, deleted = [], [], []
    ids_list = set()

    for data in dataset:
        obj_id = data.get('id', None)
        if not obj_id:
            # Created
            obj = obj_type(**data)
            created.append(obj)
            continue

        # Updated
        obj = obj_type.objects.get(id=obj_id)
        for (k, v) in data.items():
            setattr(obj, k, v)
        updated.append(obj)

        ids_list.add(obj_id)

    # Deleted
    usable_current_ids = set()

    for (id,) in current_ids:
        usable_current_ids.add(id)

    deleted = usable_current_ids.difference(ids_list)

    return created, updated, deleted


def user_sync_email_with_contact(user: app_models.User):
    if (not user.email
            or (user.contacts and user.contacts.filter(email=user.email).exists())):
        return
    contact = app_models.Contact.objects.create(email=user.email)
    user.contacts.add(contact)


def generate_public_id():
    pst = timezone('US/Pacific')
    datetime_pst = datetime.now(pst)

    # Get the last object with the same date prefix
    queryset = app_models.Booking.objects.filter(public_id__startswith=datetime_pst.strftime('%y%m%d'))
    last_object = queryset.last()

    # Increment the sequence number
    sequence_number = 1
    if last_object:
        last_sequence_number = int(last_object.public_id[7:])
        sequence_number = last_sequence_number + 1

    # Unique identifier field value
    return '{}-{:03d}'.format(datetime_pst.strftime('%y%m%d'), sequence_number)


def generate_unique_field(business: Union[str, app_models.Business],
                          instance: Union[models.Model, app_models.ExtendableModel], fields: list):
    """
    Generates a unique field for a model instance
    :param business: Business
    :param instance: Model instance
    :param fields: List of fields to be used to generate the unique field
    """

    if isinstance(business, str):
        business = app_models.Business.objects.get(name=business)

    model = instance.__class__
    content_type = ContentType.objects.get_for_model(model)

    extras = app_models.Extra.objects.filter(
        business=business,
        parent_ct=content_type,
        parent_id=instance.id,
    )

    values = []

    for field in fields:
        if hasattr(instance, field):
            value = getattr(instance, field)

        else:
            assert_extendable(instance.__class__)
            try:
                value = extras.get(key=field).data
            except app_models.Extra.DoesNotExist:
                value = None

        values.append(str(value))

    return '|'.join(values)


def update_model_unique_field(business: Union[str, app_models.Business], instance: app_models.UniquifiableModel):
    """
    Updates the unique field of a model instance. Note that this function saves the instance.
    :param business: Business
    :param instance: UniquifiableModel
    """
    if isinstance(business, str):
        business = app_models.Business.objects.get(name=business)

    model = instance.__class__
    content_type = ContentType.objects.get_for_model(model)

    try:
        unique_condition = app_models.UniqueCondition.objects.get(business=business, content_type=content_type)

    except app_models.UniqueCondition.DoesNotExist:
        return None

    instance.unique_field = generate_unique_field(business, instance, unique_condition.fields)
    instance.save(update_fields=['unique_field'])


@transaction.atomic
def regenerate_unique_condition_fields(unique_condition: app_models.UniqueCondition) -> int:
    model = unique_condition.content_type.model_class()
    model.objects.all().update(unique_field=None)

    unique_fields = []
    updated_instances = []
    for instance in model.objects.all():
        instance.unique_field = generate_unique_field(unique_condition.business, instance, unique_condition.fields)
        unique_fields.append(f"{instance.unique_field}, {instance.id}")
        updated_instances.append(instance)

    return model.objects.bulk_update(updated_instances, ['unique_field'])


def log_notification_status_change(notification: app_models.Notification, status: app_models.Notification.Status):
    if not notification.booking_to_log:
        return

    send_method = notification.get_send_method_display()
    addressee = notification.data.get('addressee', 'Unknown')

    if status == app_models.Notification.Status.SUBMITTED:
        text = F"{send_method} sent to {addressee}"

    elif status == app_models.Notification.Status.SENT:
        text = F"{send_method} received by {addressee}"

    elif status == app_models.Notification.Status.FAILED:
        text = F"{send_method} failed to send to {addressee}"

    else:
        return

    app_models.Note.objects.create(
        booking=notification.booking_to_log,
        notification=notification,
        text=text,
    )


def collect_queryset_filters_by_query_params(query_params: QueryParams,
                                             related_prefix: str = '') -> List[dict]:
    """
    Collect filter values based on extra query parameters.

    :param query_params: Dictionary of query parameters.
    :param related_prefix: Prefix for related query parameters.
    :return: List of filters.
    """
    prefix = f'{related_prefix}__' if related_prefix else ''
    filters_dict = {}

    def apply_filter(filter_key: str, filter_param: Param, suffix: str):
        """
        Apply filter values based on given key and param.

        :param filter_key: Key for the filter.
        :param filter_param: Parameter for the filter.
        :param suffix: Suffix for nested query keys.
        """
        extra_data_field = 'data'
        query_value = f'{prefix}extra__{extra_data_field}{suffix}'
        if filter_param.lookup:
            query_value += f'__{filter_param.lookup}'

        param_value = json.dumps(str(filter_param.value))

        if filter_key in filters_dict:
            filters_dict[filter_key][query_value] = param_value
        else:
            filters_dict[filter_key] = {query_value: param_value}

    def collect_nested_filters(main_key: str,
                               nested_params: Dict[str, Union[Param, QueryParams]],
                               nested_suffix: str):
        """
        Recursively collect filter values with nested parameters.

        :param main_key: Main key for the filter.
        :param nested_params: Nested query parameters.
        :param nested_suffix: Suffix for nested query keys.
        """
        for nested_key, nested_param in nested_params.items():
            new_prefix = f'{nested_suffix}__{nested_key}'
            if isinstance(nested_param, Param):
                apply_filter(main_key, nested_param, new_prefix)
            elif isinstance(nested_param, QueryParams):
                collect_nested_filters(main_key, nested_param, new_prefix)
            else:
                raise ValueError(f"Invalid type {type(nested_param)}: expected Param or QueryParams")

    # Collect filters, starts recursion
    for key, param in query_params.items():
        if isinstance(param, Param):
            apply_filter(key, param, '')
        elif isinstance(param, QueryParams):
            collect_nested_filters(key, param, '')
        else:
            raise ValueError(f"Invalid type {type(param)}: expected Param or QueryParams")

    # Return filters
    query_key = f'{prefix}extra__key'
    query_filters = [
        {
            query_key: key,  # Filter for extra key
            **data_filters,  # Filters for extra data
        }
        for key, data_filters in filters_dict.items()
    ]
    return query_filters
