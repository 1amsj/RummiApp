from datetime import datetime, timedelta
import django

django.setup()

from django.core.management.base import BaseCommand
from core_backend.models import Authorization, Booking, Event, Report

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
         
    def validator_clinic_type(value):
        return (value.payer is not None and value.payer_company is None)
    
    def self_list_return(value):
        return value
    
    bookings = Booking.objects.all()
    
    for booking in bookings:
        try:
            auth = Authorization.objects.all()
            event_datalist = Event.objects.get(id=booking.id)
            event_get_extra = event_datalist.get_extra_attrs()
            report = Report.objects.filter(event__id=event_datalist.id)
            payer_company_not_none = event_datalist.payer_company is not None
            
            for aut in auth:
                report_status = map(self_list_return, report.values_list('status', flat=True))
                list_report_status = list(report_status)    
                aut_list = aut.events.all().filter(id=event_datalist.id)
                
                if payer_company_not_none:
                    if list_report_status != [] and list_report_status[-1] == 'COMPLETED' \
                    and validator_type(event_datalist) \
                    and event_get_extra.__contains__('claim_number') is not None:
                        booking.status = "delivered"
                        delivered_count += 1
                    elif aut_list.count() > 0:
                        aut_list_status = aut_list._hints['instance'].status
                        if aut_list_status == 'ACCEPTED' and validator_short_type(event_datalist):
                            booking.status = "authorized"
                            authorized_count += 1
                        elif aut_list_status == 'OVERRIDE' and validator_short_type(event_datalist):
                            booking.status = "override"
                            override_count += 1
                        elif event_get_extra.__contains__('claim_number') is not None and validator_type(event_datalist):
                            booking.status = "booked"
                            booked_count += 1
                        else:
                            booking.status = "pending"
                            pending_count += 1
                    elif event_get_extra.__contains__('claim_number') is not None and validator_type(event_datalist):
                        booking.status = "booked"
                        booked_count += 1
                    else:
                        booking.status = "pending"
                        pending_count += 1
                else:
                    if list_report_status != [] and list_report_status[-1] == 'COMPLETED' \
                    and validator_clinic_type(event_datalist) \
                    and event_get_extra.__contains__('claim_number') is not None:
                        booking.status = "delivered"
                        delivered_count += 1
                    elif event_get_extra.__contains__('claim_number') is not None and validator_clinic_type(event_datalist):
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
