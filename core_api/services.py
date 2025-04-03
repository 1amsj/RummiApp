from core_backend.datastructures import QueryParams
from core_backend.models import Authorization

def prepare_query_params(params: dict) -> QueryParams:
    """
    :param params: dict
    :return: query params
    """
    ret_params = QueryParams()
    for (k, v) in params.items():
        ret_params[k] = v
    return ret_params

def representation_services(auth_id):
    authorization = Authorization.objects.get(id=auth_id)
    return authorization.status

def validator_claim_number(value):
    if 'claim_number' in value[-1]:
        return value[-1]['claim_number']
    else:
        return None

def calculate_booking_status(event_datalist, company_type_short_validation, company_type_validation, services) -> str:
    status = 'pending'
    
    if validator_claim_number(event_datalist) is not None and company_type_validation and services.exists():
        status = "booked"
        
    if event_datalist[-1].__contains__('authorizations'):
        auth = map(representation_services, event_datalist[-1]['authorizations'])
        list_auth = list(auth)

        if list_auth.__contains__('OVERRIDE') and company_type_short_validation:
            status = "override"

        if list_auth.__contains__('ACCEPTED') and company_type_short_validation:
            status = "authorized"
        
    if event_datalist[0]['payer_company_type'] == 'noPayer':
        status = "abandoned"
            
    if event_datalist[-1]['_report_datalist'][-1]['status'].__contains__('RESCHEDULED'):
        status = "rescheduled"
    
    if event_datalist[-1]['_report_datalist'][-1]['status'].__contains__('CANCELLED'):
        status = "cancelled"
        
    if event_datalist[-1]['_report_datalist'][-1]['status'].__contains__('NO_SHOW'):
        status = "noShow"

    if event_datalist[-1]['_report_datalist'][-1]['status'].__contains__('COMPLETED') \
        and company_type_validation and validator_claim_number(event_datalist) is not None \
        and services.exists() == True:
            status = "delivered"
            
    return status
