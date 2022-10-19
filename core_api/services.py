import json
from typing import Union

from core_api.constants import EXACT_MATCH_KEY, NO_EXACT_MATCH_SUFFIX
from core_backend.exceptions import IllegalArgumentException
from core_backend.models import Contact, Location


def prepare_query_params(params: dict, exact_match=None) -> dict:
    """
    :param params: dict
    :param exact_match: whether to append NO_EXACT_MATCH_SUFFIX to every key. If None, it will search for the
    value for EXACT_MATCH_KEY in params; defaults to True if not found
    :return: params dict with NO_EXACT_MATCH_SUFFIX appended to the end of every key according to exact_match
    """
    if exact_match is None:
        exact_match = json.loads(params.get(EXACT_MATCH_KEY, 'true'))

    return {
        (k.split('__')[0] + (NO_EXACT_MATCH_SUFFIX if not exact_match else '')): v
        for (k, v) in params.items()
    }


def generic_get_or_create(data: Union[int, dict], get_func, create_func):
    if data is None:
        return

    if isinstance(data, int):
        return get_func(data)

    if isinstance(data, dict):
        id = data.get('id')
        return get_func(id) if id else create_func(data)

    raise IllegalArgumentException('int or dict required')


def contact_get_or_create(data: Union[int, dict]):
    def get(id):
        return Contact.objects.get(id=id)

    def create(data):
        email = data.get('email')
        phone = data.get('phone')
        fax = data.get('fax')
        if not (email or phone or fax):
            raise ValueError('data can not be empty')
        return Contact.objects.create(
            email=email,
            phone=phone,
            fax=fax,
        )

    return generic_get_or_create(data, get, create)


def location_get_or_create(data: Union[int, dict]):
    def get(id):
        return Location.objects.get(id=id)

    def create(data):
        return Location.objects.create(
            address=data['address'],
            city=data['city'],
            state=data['state'],
            country=data['country'],
            zip=data.get('zip', ''),
        )

    return generic_get_or_create(data, get, create)
