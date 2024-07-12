from enum import Enum

from core_backend.settings import BACKEND_URL


# API special payload keys
class ApiSpecialKeys(str, Enum):
    # Querying
    EVENTS_QUERY = '_events_query'
    PATCH_QUERY = '_query'
    RECIPIENT_ID = '_recipient_id'
    AGENTS_ID = '_agents_id'
    START_DATE = '_start_date'
    END_DATE = '_end_date'

    # Includes
    INCLUDE_BOOKING = '_include_booking'
    INCLUDE_COMPANIES = '_include_companies'
    INCLUDE_EVENTS = '_include_events'
    INCLUDE_ROLES = '_include_roles'

    # Flags
    DELETED_FLAG = '_deleted'
    
    #Filters
    STATUS = '_status'

    # Appended data
    AFFILIATION_DATALIST = '_affiliation_datalist'
    AGENT_DATA = '_agent_data'
    AGENTS_DATA = '_agents_data'
    BUSINESS = '_business'
    COMPANY_RATES_DATALIST = '_company_rates_datalist'
    COMPANY_RELATIONSHIPS_DATA = '_preferred_agency_data'
    EVENT_DATALIST = '_event_datalist'
    OFFER_DATALIST = '_offer_datalist'
    OPERATOR_DATA = '_operator_data'
    PAYER_DATA = '_payer_data'
    PROVIDER_DATA = '_provider_data'
    RATES_DATALIST = '_rates_datalist'
    RECIPIENT_DATA = '_recipient_data'
    REPORT_DATALIST = '_report_datalist'
    REQUESTER_DATA = '_requester_data'
    SERVICE_DATALIST = '_service_datalist'
    SERVICE_AREA_DATALIST = '_service_area_datalist'
    



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
    "sw": "startswith",
    "array_in": "in",
    "isnull": "isnull",
}

# External APIs
CONCORD_API_NAME = 'concord'
CONCORD_DEBUG_JOB_PREFIX = 'DEBUG_JOB_ID'
CONCORD_EXPECTED_SEND_WAIT_THRESHOLD_IN_DAYS = 0 # TODO should be 7 whence we configure listener
CONCORD_NOTIFY_ENDPOINT = 'api/v1/notifications/fax'
CONCORD_NOTIFY_DESTINATION = (
    f'{BACKEND_URL}{CONCORD_NOTIFY_ENDPOINT}'
    if BACKEND_URL[-1] == '/'
    else f'{BACKEND_URL}/{CONCORD_NOTIFY_ENDPOINT}'
)

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

class CacheTime(int, Enum):
    MINUTE = 60
    HOUR = 3600
    DAY = 86400
    WEEK = 604800
    MONTH = 2592000