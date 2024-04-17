from datetime import datetime
from rest_framework.response import Response
from core_api.constants import ApiSpecialKeys
from core_api.decorators import expect_does_not_exist
from core_api.services import prepare_query_params
from core_api.services_datamanagement import handle_events_bulk
from core_api.views import basic_view_manager
from core_backend.models import Event, Language, Payer, Report, User
from core_api.decorators import expect_does_not_exist, expect_key_error
from rest_framework import status
from core_api.services_datamanagement import update_event_wrap, create_reports_wrap, create_event
from core_api.exceptions import BadRequestException
from django.db import transaction
from django.db.models import Count, Q, Subquery, OuterRef

from core_backend.serializers.serializers import EventNoBookingSerializer, EventSerializer
from core_backend.serializers.serializers_patch import EventPatchSerializer

class ManageEventsReports(basic_view_manager(Event, EventSerializer)):

    @classmethod
    @expect_does_not_exist(Event)
    def get(cls, request, business_name=None, event_id=None):
        serializer_class = EventSerializer
        no_booking_serializer_class = EventNoBookingSerializer
        query_params = prepare_query_params(request.GET)

        serializer = serializer_class if request.GET.get(ApiSpecialKeys.INCLUDE_BOOKING, False) else no_booking_serializer_class

        queryset = serializer.get_default_queryset()

        if business_name:
            queryset = queryset.filter(booking__business__name=business_name)

        queryset = queryset.filter(Q(booking__status='delivered'))
                
        
        queryset = cls.apply_filters(queryset.order_by('-start_at'), query_params)
        serialized = serializer(queryset, many=True)
        report_values = []
        for obj in serialized.data:
            
            def representation_phone(repr):
                    return repr["phone"]
                    
            def representation_email(repr):
                    return repr["email"]
                    
            def representation_fax(repr):
                    return repr["fax"]
            
            phone = map(representation_phone, obj['affiliates'][0]['recipient']['contacts'])
            email = map(representation_email, obj['affiliates'][0]['recipient']['contacts'])
            fax = map(representation_fax, obj['affiliates'][0]['recipient']['contacts'])
            
            phoneUnzip = ", ".join(list(phone))
            emailUnzip = ", ".join(list(email))
            faxUnzip = ", ".join(list(fax))
            
            def representation_note(repr):
                    return repr["text"]
            notes = map(representation_note, obj['booking']['companies'][0]['notes'])
            notesUnzip = ", ".join(list(notes))
            
            def representation_auth(repr):
                if repr["status"] == "ACCEPTED":
                    return repr['last_updated_at']
                else:
                    return ""
            authorized = list(map(representation_auth, obj['authorizations']))
            non_empty_authorized = list(filter(lambda x: x != "", authorized))
            if non_empty_authorized:
                latest_authorization = max(non_empty_authorized, key=lambda x: x.split()[0])
            else:
                latest_authorization = ""
            
            def representation_auth_by(repr):
                if repr["status"] == "ACCEPTED" and latest_authorization \
                    != "" and repr['last_updated_at'] == latest_authorization:
                    payer = Payer.objects.filter(id=repr["authorizer"]).values()
                    user_authorizer = User.objects.filter(id=payer[0]['user_id']).values()
                    return f"{user_authorizer[0]['first_name']} {user_authorizer[0]['last_name']}"
                else:
                    return ""
            auth_by = map(representation_auth_by, obj['authorizations'])
            auth_byUnzip = ", ".join(list(auth_by))
            
            obj_date = obj['start_at'].split('.')[0] if obj['start_at'] != None else ''
            obj_arrive = obj['reports'][-1]['arrive_at'].split('.')[0] if obj['reports'][-1]['arrive_at'] != None else ''
            obj_start = obj['reports'][-1]['start_at'].split('.')[0] if obj['reports'][-1]['start_at'] != None else ''
            obj_end = obj['reports'][-1]['end_at'].split('.')[0] if obj['reports'][-1]['end_at'] != None else ''
            
            if obj_date.__len__() != 0:
                dt = datetime.fromisoformat(obj_date.split('Z')[0]) 
                dt_date = dt.date()
            else:
                dt_date
            if obj_arrive.__len__() != 0:
                dt = datetime.fromisoformat(obj_arrive.split('Z')[0]) 
                dt_arrive = dt.time()
            else:
                dt_arrive = ''
            if obj_start.__len__() != 0:
                dt = datetime.fromisoformat(obj_start.split('Z')[0]) 
                dt_start = dt.time()
            else:
                dt_start = ''
            if obj_end.__len__() != 0:
                dt = datetime.fromisoformat(obj_end.split('Z')[0])
                dt_end = dt.time()
            else:
                dt_end = ''
            
            contacts = obj['booking']['companies'][0]['contacts']
            if len(contacts) == 1:
                contactsUnzip = contacts[0]
            elif len(contacts) > 1:
                contactsUnzip = ", ".join(contacts)
            else:
                contactsUnzip = "" 
            
            language = Language.objects.filter(alpha3=obj['booking']['target_language_alpha3']).values()
            rateCardExtend = []
            FinalRateCardExtend = []
            #No Certification
            if language[0]['common'] == True and \
            obj['booking']['service_root']['description'] == 'Onsite Interpretation no certification':
                rateCard = "127.50"
                rateCardExtend.append(rateCard)
            elif language[0]['common'] == False and \
            obj['booking']['service_root']['description'] == 'Onsite Interpretation no certification':
                rateCard = "147.50"
                rateCardExtend.append(rateCard)
            elif language[0]['common'] == False and \
            obj['booking']['service_root']['description'] == 'Videochat Interpretation no certification' or \
            obj['booking']['service_root']['description'] == 'Telephonic Interpretation no certification':
                rateCard = "117.50"
                rateCardExtend.append(rateCard)
            elif language[0]['common'] == True and \
            obj['booking']['service_root']['description'] == 'Videochat Interpretation no certification' or \
            obj['booking']['service_root']['description'] == 'Telephonic Interpretation no certification':
                rateCard = "90.00"
                rateCardExtend.append(rateCard)
            
            #Certification
            elif language[0]['common'] == True and \
            obj['booking']['service_root']['description'].__contains__('no certification') == False and \
            obj['booking']['service_root']['description'].__contains__('no certified') == False and \
            (obj['booking']['service_root']['description'].__contains__('Videochat') == True or \
            obj['booking']['service_root']['description'].__contains__('Telephonic') == True):
                rateCard = "105.00"
                rateCardExtend.append(rateCard)
            elif language[0]['common'] == False and \
            obj['booking']['service_root']['description'].__contains__('no certification') == False and \
            obj['booking']['service_root']['description'].__contains__('no certified') == False and \
            (obj['booking']['service_root']['description'].__contains__('Videochat') == True or \
            obj['booking']['service_root']['description'].__contains__('Telephonic') == True):
                rateCard = "137.50"
                rateCardExtend.append(rateCard)
            elif language[0]['common'] == True and \
            obj['booking']['service_root']['description'].__contains__('no certification') == False and \
            obj['booking']['service_root']['description'].__contains__('no certified') == False and \
            obj['booking']['service_root']['description'].__contains__('Onsite') == True:
                rateCard = "167.50"
                rateCardExtend.append(rateCard)
            elif language[0]['common'] == False and \
            obj['booking']['service_root']['description'].__contains__('no certification') == False and \
            obj['booking']['service_root']['description'].__contains__('no certified') == False and \
            obj['booking']['service_root']['description'].__contains__('Onsite') == True:
                rateCard = "182.50"
                rateCardExtend.append(rateCard)

            if obj['payer'] is not None and obj['payer']['companies'][-1]['company_rates'] != [] and obj['payer']['companies'] != []:
                def representation_base_lang(repr):
                    if repr['language'] == 'Common Languages':
                        rateLang = True
                        ratePricing = repr['bill_min_payment']
                        rateModality = repr['root']['description']
                    elif repr['language'] == 'Uncommon Languages':
                        rateLang = False
                        ratePricing = repr['bill_min_payment']
                        rateModality = repr['root']['description']
                    elif repr['language'] == 'All Languages':
                        rateLang = "All"
                        ratePricing = repr['bill_min_payment']
                        rateModality = repr['root']['description']
                    return {
                        "languague": rateLang,
                        "price": ratePricing,
                        "modality": rateModality,
                    }
                BaseRateCard = map(representation_base_lang, obj['payer']['companies'][-1]['company_rates'])        
                
                BaseRateCardList = list(BaseRateCard)
                if BaseRateCardList != []:
                    def representation_lang(repr):
                        #Common
                        if language[0]['common'] == repr['languague'] and obj['booking']['service_root']['description'] == repr['modality']:
                            valueRate = repr['price']
                        #Rare
                        elif language[0]['common'] != repr['languague'] and obj['booking']['service_root']['description'] == repr['modality'] and obj['booking']['target_language_alpha3'] != "spa":
                            valueRate = repr['price']
                        else:
                            valueRate = "Void"
                        return valueRate
                            
                    FinalRateCard = map(representation_lang, BaseRateCardList)
                    
                ListRateCard =list(FinalRateCard)
                FinalRateCard = [element for element in ListRateCard if element != 'Void'] 
                FinalRateCardExtend.extend(FinalRateCard)
                
            if len(rateCardExtend):
                rateCardExtend = rateCardExtend[0]
                
            if len(FinalRateCardExtend):
                FinalRateCardExtend = FinalRateCardExtend[0]
            
            values = {
                #Patient
                "first_name": obj['affiliates'][0]['recipient']['first_name'],
                "last_name": obj['affiliates'][0]['recipient']['last_name'],
                "date_of_birth": obj['affiliates'][0]['recipient']['date_of_birth'],
                "phone_contact": phoneUnzip if obj['affiliates'][0]['recipient']['contacts'] != [] else "",
                "email_contact": emailUnzip if obj['affiliates'][0]['recipient']['contacts'] != [] else "",
                "fax_contact": faxUnzip if obj['affiliates'][0]['recipient']['contacts'] != [] else "",
                "address": obj['affiliates'][0]['recipient']['location']['address'] if obj['affiliates'][0]['recipient']['location'] is not None else '',
                "unit_number": obj['affiliates'][0]['recipient']['location']['unit_number'] if obj['affiliates'][0]['recipient']['location'] is not None else "",
                "city": obj['affiliates'][0]['recipient']['location']['city'] if obj['affiliates'][0]['recipient']['location'] is not None else '',
                "state": obj['affiliates'][0]['recipient']['location']['state'] if obj['affiliates'][0]['recipient']['location'] is not None else '',
                "country": obj['affiliates'][0]['recipient']['location']['country'] if obj['affiliates'][0]['recipient']['location'] is not None else '',
                "zip": obj['affiliates'][0]['recipient']['location']['zip'] if obj['affiliates'][0]['recipient']['location'] is not None else '',
                #Event
                "public_id": obj['booking']['public_id'],
                "date": dt_date,
                "arrive_time": dt_arrive,
                "start_time": dt_start,
                "end_time": dt_end,
                "date_of_injury": obj['date_of_injury'] if obj.__contains__('date_of_injury') else "",
                "payer_company_type": obj['payer']['companies'][-1]['type'] if obj['payer'] != None else "",
                "payer_company_name": obj['payer']['companies'][-1]['name'] if obj['payer'] != None else "",
                "payer_company_address": obj['payer']['companies'][-1]['locations'][-1]['address'] if obj['payer'] != None and obj['payer']['companies'] != [] and obj['payer']['companies'][-1]['locations'] != [] else "",
                "payer_company_city": obj['payer']['companies'][-1]['locations'][-1]['city'] if obj['payer'] != None and obj['payer']['companies'] != [] and obj['payer']['companies'][-1]['locations'] != [] else "",
                "payer_company_state": obj['payer']['companies'][-1]['locations'][-1]['state'] if obj['payer'] != None and obj['payer']['companies'] != [] and obj['payer']['companies'][-1]['locations'] != [] else "",
                "payer_company_send_method": obj['payer']['companies'][-1]['send_method'] if obj['payer'] != None and obj['payer']['companies'] != [] and obj['payer']['companies'][-1]['locations'] != [] else "",
                "provider": f"{obj['agents'][-1]['first_name']} {obj['agents'][-1]['last_name']}" if obj['agents'] != [] else "",
                "claim_number": obj['claim_number'] if obj.__contains__('claim_number') else "",
                "clinic": obj['booking']['companies'][0]['name'],
                "clinic_address": obj['booking']['companies'][0]['locations'][0]['address'],
                "clinic_unit_number": obj['booking']['companies'][0]['locations'][0]['unit_number'],
                "clinic_city": obj['booking']['companies'][0]['locations'][0]['city'],
                "clinic_state": obj['booking']['companies'][0]['locations'][0]['state'],
                "clinic_country": obj['booking']['companies'][0]['locations'][0]['country'],
                "clinic_zip": obj['booking']['companies'][0]['locations'][0]['zip'],
                "send_method": obj['booking']['companies'][0]['send_method'],
                "notes": notesUnzip,
                "contacts": contactsUnzip,
                "languague": language[0]['name'],
                "type_of_appointment": obj['description'],
                "interpreter": f"{obj['booking']['services'][-1]['provider']['first_name']} {obj['booking']['services'][-1]['provider']['last_name']}" if obj['booking']['services'] != [] else "",
                "modality": obj['booking']['service_root']['description'],
                "status_report": obj['reports'][-1]['status'] if obj['reports'] != [] else "",
                "authorized": "ACCEPTED" if latest_authorization != "" else "",
                "auth_by": auth_byUnzip,
                "operators_first_name": obj['booking']['operators'][-1]['first_name'] if obj['booking']['operators'] != [] else "",
                "operators_last_name": obj['booking']['operators'][-1]['last_name'] if obj['booking']['operators'] != [] else "",
                "price": FinalRateCardExtend if obj['payer'] is not None and obj['payer']['companies'][-1]['company_rates'] != [] and FinalRateCard != [] else rateCardExtend,
            }
            
            report_values.append(values)
        
        return Response(report_values)
    @staticmethod
    @transaction.atomic
    @expect_key_error
    def post(request, business_name=None):
        """
        Create a new event.
        If the payload is an array of objects, the events will be created/updated depending on whether they provide
        their ID or not
        """
        data = request.data
        user: User = request.user
        requester_id = user.as_requester.id if user.is_requester else None
        report_datalist = request.data.pop(ApiSpecialKeys.REPORT_DATALIST, None)

        if type(data) is list:
            # Create, update or delete events in bulk
            event_ids = handle_events_bulk(
                data,
                business_name,
                requester_id
            )
            return Response(event_ids, status=status.HTTP_201_CREATED)

        # Create a single event
        event_id = create_event(
            data,
            business_name,
            requester_id
        )

        if report_datalist:
            create_reports_wrap(report_datalist, event_id)

        return Response(event_id, status=status.HTTP_201_CREATED)

    @staticmethod
    @transaction.atomic
    @expect_does_not_exist(Event)
    def put(request, event_id=None):
        business_name = request.data.pop(ApiSpecialKeys.BUSINESS)

        event = Event.objects.get(id=event_id)

        update_event_wrap(
            request.data,
            business_name,
            event_instance=event,
        )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @classmethod
    @transaction.atomic
    @expect_does_not_exist(Event)
    def patch(cls, request, business_name=None):
        serializer_class = EventSerializer
        patch_serializer_class = EventPatchSerializer
        data = request.data

        # Extract query keys
        try:
            patch_query = data.pop(ApiSpecialKeys.PATCH_QUERY)
        except KeyError:
            raise BadRequestException('Missing patch query')

        # Get target queryset
        query_params = prepare_query_params(patch_query)
        queryset = serializer_class.get_default_queryset()
        queryset = cls.apply_filters(queryset, query_params)

        # Apply patch to each event
        for event in queryset:
            serializer = patch_serializer_class(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.patch(event, business_name)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    @transaction.atomic
    @expect_does_not_exist(Event)
    def delete(request, event_id=None):
        Event.objects.get(id=event_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
