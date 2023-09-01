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
