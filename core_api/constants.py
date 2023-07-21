from enum import Enum

# API special payload keys
class ApiSpecialKeys(str, Enum):
    # Querying
    EVENTS_QUERY = '_events_query'
    PATCH_QUERY = '_query'

    # Includes
    INCLUDE_BOOKING = '_include_booking'
    INCLUDE_EVENTS = '_include_events'
    INCLUDE_ROLES = '_include_roles'

    # Flags
    DELETED_FLAG = '_deleted'

    # Appended data
    BUSINESS = '_business'
    AFFILIATION_DATALIST = '_affiliation_datalist'
    AGENT_DATA = '_agent_data'
    PAYER_DATA = '_payer_data'
    PROVIDER_DATA = '_provider_data'
    RECIPIENT_DATA = '_recipient_data'
    REQUESTER_DATA = '_requester_data'
    EVENT_DATALIST = '_event_datalist'
    OFFER_DATALIST = '_offer_datalist'


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
