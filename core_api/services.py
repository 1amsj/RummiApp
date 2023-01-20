import json
from typing import Union

from core_backend.exceptions import IllegalArgumentException
from core_api.constants import EXACT_MATCH_KEY
from core_backend.datastructures import QueryParams


def prepare_query_params(params: dict) -> QueryParams:
    """
    :param params: dict
    :return: query params
    """
    ret_params = QueryParams()
    for (k, v) in params.items():
        ret_params[k] = v
    return ret_params
