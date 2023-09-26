from dataclasses import dataclass
from typing import Any, Dict, Optional, Union

from core_api.constants import API_NESTED_QUERY_PARAM_SEPARATOR, API_QUERY_LOOKUP_MAP, API_QUERY_LOOKUP_SEPARATOR


# Metaclasses
class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


# Query params
@dataclass
class Param:
    value: Any
    lookup: str = ''


QueryParamsKey = str
QueryParamsValue = Union[Param, "QueryParams"]


class QueryParams(Dict[str, QueryParamsValue]):
    def __init__(self, params: Optional[Dict[QueryParamsKey, Any]] = None):
        super(QueryParams, self).__init__()
        if params:
            for (k, v) in params.items():
                self[k] = v

    def __getitem__(self, key: QueryParamsKey) -> QueryParamsValue:
        ks = key.split(API_NESTED_QUERY_PARAM_SEPARATOR)
        current = self
        for k in ks:
            current = super(QueryParams, current).__getitem__(k)
        return current

    # noinspection PySuperArguments
    def __setitem__(self, key: QueryParamsKey, value: Any):
        affixes = key.split(API_QUERY_LOOKUP_SEPARATOR)
        if len(affixes) > 2 or len(affixes) < 1:
            raise ValueError('Invalid query')

        keys = affixes[0].split(API_NESTED_QUERY_PARAM_SEPARATOR)
        try:
            suffix = affixes[1]
        except IndexError:
            suffix = None

        current = self
        for key in keys[:-1]:
            try:
                current[key]
            except KeyError:
                super(QueryParams, current).__setitem__(key, QueryParams())
            current = current[key]

        value = QueryParams.correct_value(value)

        key = keys[-1]
        is_array = '[' in key

        if not is_array:
            super(QueryParams, current).__setitem__(key, Param(
                value=value,
                lookup=suffix,
            ) if not isinstance(value, (Param, QueryParams)) else value)

        else:
            key = key.split('[')[0]
            prev: Optional[Param] = super(QueryParams, current).get(key)
            if prev:
                value = (prev.value + [value]) if isinstance(prev.value, list) else [prev.value, value]
            else:
                value = [value]
            current[F'{key}__array_in'] = value

    @staticmethod
    def correct_value(value):
        if value == "true":
            return True

        elif value == "false":
            return False

        return value

    def is_empty(self):
        return len(self) <= 0

    def to_dict(self, prefix='') -> dict:
        ret = {}
        for (k, p) in self.items():
            if isinstance(p, Param):
                try:
                    lookup = API_QUERY_LOOKUP_MAP[p.lookup] if p.lookup else None
                except KeyError:
                    raise ValueError('Invalid lookup value')
                ret[F'{prefix}{k}{f"__{lookup}" if lookup else ""}'] = p.value
                continue

            if isinstance(p, QueryParams):
                ret.update(p.to_dict(F'{prefix}{k}__'))
                continue

            raise TypeError('Illegal QueryParams state')
        return ret

    def pop(self, __key: QueryParamsKey, default=None):
        ks = __key.split(API_NESTED_QUERY_PARAM_SEPARATOR)
        q = self['.'.join(ks[:-1])] if len(ks) > 1 else self
        return super(QueryParams, q).pop(ks[-1], default)
