NO_EXACT_MATCH_SUFFIX = '__icontains'

EXACT_MATCH_KEY = '_exact_match'
INCLUDE_BOOKING_KEY = '_include_booking'
INCLUDE_EVENTS_KEY = '_include_events'
INCLUDE_ROLES_KEY = '_include_roles'

FIELDS_BLACKLIST = [
    EXACT_MATCH_KEY,
    INCLUDE_EVENTS_KEY,
    INCLUDE_ROLES_KEY,
]

API_NESTED_QUERY_PARAM_SEPARATOR = '.'
API_QUERY_LOOKUP_SEPARATOR = '__'

API_QUERY_LOOKUP_MAP = {
    "em": "exact",
    "nem": "icontains",
    "gt": "gt",
    "lt": "lt",
    "gte": "gte",
    "lte": "lte",
    "array_in": "in",
    "isnull": "isnull",
}
