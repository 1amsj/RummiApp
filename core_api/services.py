from core_api.views import validator_claim_number
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

def representation_services(repr):
    authorization = Authorization.objects.get(id=repr)
    return authorization.status

def calculate_booking_status(params: dict) -> str:
    event_datalist = params['event_datalist']
    company_type_short_validation = params['company_type_short_validation']
    company_type_validation = params['company_type_validation']
    services = params['services']
    
    status = 'pending'
    
    if event_datalist[0]['payer_company_type'] == 'noPayer':
            status = "abandoned"
        
    elif event_datalist[-1].__contains__('authorizations'):
        auth = map(representation_services, event_datalist[-1]['authorizations'])
        list_auth = list(auth)

        if list_auth.__contains__('ACCEPTED') and company_type_short_validation:
            status = "authorized"
        elif list_auth.__contains__('OVERRIDE') and company_type_short_validation:
            status = "override"

    elif validator_claim_number(event_datalist) is not None and company_type_validation and services.exists() == True:
        status = "booked"
            
    return status
