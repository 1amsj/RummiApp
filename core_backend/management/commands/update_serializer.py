from datetime import datetime, timedelta
import django
# from django.db.models import Subquery, OuterRef

from core_backend.serializers.serializers import EventSerializer

django.setup()

from django.core.management.base import BaseCommand
from core_backend.models import Authorization, Booking, Event

pending_count = 0
booked_count = 0 
delivered_count = 0
override_count = 0
authorized_count = 0
error_count = 0
error_ids = []

class Command(BaseCommand):

    start = datetime.now()

    def validator_type(value):
        return (value.payer_company.type == 'insurance' and value.payer is not None and value.payer_company is not None) or \
                (value.payer_company.type == 'agency' and value.payer is not None and value.payer_company is not None) or \
                (value.payer_company.type == 'lawfirm' and value.payer is not None and value.payer_company is not None) or \
                (value.payer_company.type == 'clinic' and value.payer_company is not None)

    def validator_short_type(value):
        return (value.payer_company.type == 'insurance' and value.payer is not None and value.payer_company is not None) or \
                (value.payer_company.type == 'agency' and value.payer is not None and value.payer_company is not None) or \
                (value.payer_company.type == 'lawfirm' and value.payer is not None and value.payer_company is not None)
         
    def validator_patient_type(value):
        return (value.payer is not None and value.payer_company is None)
    
    def self_list_return(value):
        return value
    
    def list_authorizations(value):
        return value.status
        
    bookings = Booking.objects.all()
    
    
    eventlist = Event.objects.all()
    serializer_class = EventSerializer
    query = serializer_class(eventlist)
    query_added = query.get_default_queryset()
    
    for booking in bookings:
        try:
            event_datalist = Event.objects.get(booking__id=booking.id)
            general_query = query_added.filter(booking__public_id = booking.public_id)
            reports_query = general_query.filter(reports__status='COMPLETED')
            
            event_get_extra = event_datalist.get_extra_attrs()
            payer_company_not_none = event_datalist.payer_company is not None
                
            if payer_company_not_none:
                if reports_query.count() > 0 and reports_query[0].__dict__['_prefetched_objects_cache']['reports'][:10][-1].status == 'COMPLETED' \
                and validator_type(event_datalist) \
                and event_get_extra.__contains__('claim_number') == True:
                    booking.status = "delivered"
                    delivered_count += 1
                elif general_query[0].__dict__['_prefetched_objects_cache'].__contains__('authorizations'):
                    authorizations_status = map(list_authorizations, general_query[0].__dict__['_prefetched_objects_cache']['authorizations'])
                    list_authorizations_status = list(authorizations_status)
                    if list_authorizations_status.__contains__('ACCEPTED') and validator_short_type(event_datalist):
                        booking.status = "authorized"
                        authorized_count += 1
                    elif list_authorizations_status.__contains__('OVERRIDE') and validator_short_type(event_datalist):
                        booking.status = "override"
                        override_count += 1
                    elif event_get_extra.__contains__('claim_number') == True and validator_type(event_datalist):
                        booking.status = "booked"
                        booked_count += 1
                    else:
                        booking.status = "pending"
                        pending_count += 1
                elif event_get_extra.__contains__('claim_number') == True and validator_type(event_datalist):
                    booking.status = "booked"
                    booked_count += 1
                else:
                    booking.status = "pending"
                    pending_count += 1
            else:
                if reports_query.count() > 0 and reports_query[0].__dict__['_prefetched_objects_cache']['reports'][:10][-1].status == 'COMPLETED' \
                and validator_patient_type(event_datalist) \
                and event_get_extra.__contains__('claim_number') == True:
                    booking.status = "delivered"
                    delivered_count += 1
                elif event_get_extra.__contains__('claim_number') == True and validator_patient_type(event_datalist):
                    booking.status = "booked"
                    booked_count += 1
                else:
                    booking.status = "pending"
                    pending_count += 1
                    
            booking.save()
        except:
            error_count += 1
            error_ids.append(booking.public_id)
            print(f"Error creating booking_status: {booking.public_id}")
    
            continue
        
        end = datetime.now()
        duration = end - start

        print(f"Pending: {pending_count}")
        print(f"Booked: {booked_count}")
        print(f"Delivered: {delivered_count}")
        print(f"Override: {override_count}")
        print(f"Authorized: {authorized_count}")

        print(f"Errors: {error_count}. IDs: {error_ids}")

        print(f"Time: {duration}")
