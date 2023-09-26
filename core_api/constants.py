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
    AFFILIATION_DATALIST = '_affiliation_datalist'
    AGENT_DATA = '_agent_data'
    BUSINESS = '_business'
    EVENT_DATALIST = '_event_datalist'
    OFFER_DATALIST = '_offer_datalist'
    OPERATOR_DATA = '_operator_data'
    PAYER_DATA = '_payer_data'
    PROVIDER_DATA = '_provider_data'
    RECIPIENT_DATA = '_recipient_data'
    REPORT_DATALIST = '_report_datalist'
    REQUESTER_DATA = '_requester_data'
    SERVICE_DATALIST = '_service_datalist'


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

# External API names
CONCORD_API_NAME = 'concord'

# Non-generic constants
INTERPRETATION_BUSINESS_NAME = 'interpretation'

class AgentRoles(str, Enum):
    MEDICAL_PROVIDER = 'medicalProvider'

class BookingReminderTargets(str, Enum):
    EXTRA_KEY = 'reminder_targets'
    ALL = "all"
    CLINIC = "clinic"
    INTERPRETER = "interpreter"

class CompanyTypes(str, Enum):
    CLINIC = 'clinic'
