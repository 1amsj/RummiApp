import json

from core_api.constants import EXACT_MATCH_KEY, NO_EXACT_MATCH_SUFFIX


def prepare_query_params(params: dict, exact_match=None) -> dict:
    """
    :param params: dict
    :param exact_match: whether or not to append NO_EXACT_MATCH_SUFFIX to every key. If None, it will search for the
    value for EXACT_MATCH_KEY in params; defaults to True if not found
    :return: params dict with NO_EXACT_MATCH_SUFFIX appended to the end of every key according to exact_match
    """
    if exact_match is None:
        exact_match = json.loads(params.get(EXACT_MATCH_KEY, 'true'))

    return {
        (k.split('__')[0] + (NO_EXACT_MATCH_SUFFIX if not exact_match else '')): v
        for (k, v) in params.items()
    }
