from enum import Enum

# API special payload keys
class ApiSpecialKeys(str, Enum):
    # Includes
    INCLUDE_BOOKING = '_include_booking'
    INCLUDE_EVENTS = '_include_events'
    INCLUDE_ROLES = '_include_roles'

    # Appended data
    BUSINESS = '_business'
    AFFILIATION_DATALIST = '_affiliation_datalist'
    PROVIDER_DATA = '_provider_data'
    RECIPIENT_DATA = '_recipient_data'
    EVENT_DATALIST = '_event_datalist'
    AGENT_DATA = '_agent_data'
    REQUESTER_DATA = '_requester_data'


FIELDS_BLACKLIST = [key for key in ApiSpecialKeys]

# API separators
API_NESTED_QUERY_PARAM_SEPARATOR = '.'
API_QUERY_LOOKUP_SEPARATOR = '__'

# API querying keys
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
