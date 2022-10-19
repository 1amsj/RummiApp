from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple, Union

from core_api.constants import API_NESTED_QUERY_PARAM_SEPARATOR, NO_EXACT_MATCH_SUFFIX


@dataclass
class Param:
    value: Any
    lookup: str = ''


QueryParamsKey = Union[str, Tuple[str, bool]]


class QueryParams(Dict[str, Union[Param, "QueryParams"]]):
    def __init__(self, params: Optional[Dict[QueryParamsKey, Any]] = None):
        super(QueryParams, self).__init__()
        if params:
            for (k, v) in params.items():
                self[k] = v

    def __getitem__(self, key: str) -> Param:
        ks = key.split(API_NESTED_QUERY_PARAM_SEPARATOR)
        current = self
        for k in ks:
            current = super(QueryParams, current).__getitem__(k)
        return current

    # noinspection PySuperArguments
    def __setitem__(self, key: QueryParamsKey, value: Any):
        if isinstance(key, tuple):
            suffix = NO_EXACT_MATCH_SUFFIX if not key[1] else ''
            ks = key[0].split(API_NESTED_QUERY_PARAM_SEPARATOR)

        else:
            suffix = ''
            ks = key.split(API_NESTED_QUERY_PARAM_SEPARATOR)

        current = self
        for k in ks[:-1]:
            try:
                current[k]
            except KeyError:
                super(QueryParams, current).__setitem__(k, QueryParams())
            current = current[k]

        super(QueryParams, current).__setitem__(ks[-1], Param(
            value=value,
            lookup=suffix,
        ) if not isinstance(value, (Param, QueryParams)) else value)

    def is_empty(self):
        return len(self) <= 0

    def to_dict(self, prefix='') -> dict:
        ret = {}
        for (k, p) in self.items():
            if isinstance(p, Param):
                ret[F'{prefix}{k}{p.lookup}'] = p.value
                continue

            if isinstance(p, QueryParams):
                ret.update(p.to_dict(F'{prefix}{k}__'))
                continue

            raise TypeError('Illegal QueryParams state')
        return ret
