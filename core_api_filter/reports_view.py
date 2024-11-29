from datetime import datetime
import json
from xml.etree.ElementTree import ParseError
import pytz
from rest_framework.response import Response
from core_api.constants import ApiSpecialKeys
from core_api.decorators import expect_does_not_exist
from core_api.queries.reports import ApiSpecialSqlReports
from core_api.services import prepare_query_params
from core_api.services_datamanagement import handle_events_bulk
from core_api.views import basic_view_manager
from core_backend.models import Category, Event, Language, Payer, Provider, Rate, User
from core_api.decorators import expect_does_not_exist, expect_key_error
from rest_framework import status
from core_api.services_datamanagement import update_event_wrap, create_reports_wrap, create_event
from core_api.exceptions import BadRequestException
from django.db import connection, transaction
from django.db.models import Count, Q, Subquery, OuterRef
from rest_framework.utils.urls import replace_query_param

from core_backend.serializers.serializers import EventNoBookingSerializer, EventSerializer
from core_backend.serializers.serializers_patch import EventPatchSerializer

class ManageEventsReports(basic_view_manager(Event, EventSerializer)):

    @classmethod
    @expect_does_not_exist(Event)
    def get(cls, request, business_name=None, event_id=None):
        query_param_start_at = request.GET.get('start_at', None)
        query_param_end_at = request.GET.get('end_at', None)
        query_param_status_included = request.GET.getlist('status_included', [])
        query_param_status_excluded = request.GET.getlist('status_excluded', [])
        query_param_pending_items_included = request.GET.get('pending_items_included', [])
        query_param_pending_items_excluded = request.GET.get('pending_items_excluded', [])
        query_param_recipient_id = request.GET.get('recipient_id', None)
        query_param_agent_id = request.GET.get('agent_id', None)
        query_param_field_to_sort = request.GET.get('field_to_sort', None)
        query_param_order_to_sort = request.GET.get('order_to_sort', None)
        query_param_id = request.GET.get('id', None)
        
        query_event_id = event_id if event_id is not None else query_param_id
        query_start_at = datetime.strptime(query_param_start_at, "%Y-%m-%dT%H:%M:%S.%f%z").astimezone(pytz.utc) if query_param_start_at is not None else None
        query_end_at = datetime.strptime(query_param_end_at, "%Y-%m-%dT%H:%M:%S.%f%z").astimezone(pytz.utc) if query_param_end_at is not None else None
        query_field_to_sort = 'event.start_at'
        query_order_to_sort = 'ASC' if query_param_order_to_sort == 'asc' else 'DESC'
        
        if query_param_field_to_sort is not None:
            if query_param_field_to_sort == 'booking__services__provider__user__first_name':
                query_field_to_sort = 'provider_user.first_name'
            elif query_param_field_to_sort == 'booking__public_id':
                query_field_to_sort = 'booking.public_id'
            elif query_param_field_to_sort == 'affiliates__recipient__user__first_name':
                query_field_to_sort = 'recipient_user.first_name'
            elif query_param_field_to_sort == 'booking__companies__name':
                query_field_to_sort = 'company.name'
            
        try:
            query_param_page_size = int(request.GET.get('page_size', '-1'))
        except:
            raise ParseError(detail='invalid "page_size" in the query parameters', code=None)

        try:
            query_param_page = int(request.GET.get('page', '1'))
        except:
            raise ParseError(detail='invalid "page" in the query parameters', code=None)

        offset = ((query_param_page - 1) * query_param_page_size) if (query_param_page_size > 0 and query_param_page > 0) else 0

        with connection.cursor() as cursor:
            result = ApiSpecialSqlReports.get_event_report_sql(
                cursor,
                query_event_id,
                query_param_page_size,
                offset,
                query_start_at,
                query_end_at,
                query_param_status_included,
                query_param_status_excluded,
                query_param_pending_items_included,
                query_param_pending_items_excluded,
                query_param_recipient_id,
                query_param_agent_id,
                query_field_to_sort,
                query_order_to_sort
            )

        if query_param_page_size > 0:
            with connection.cursor() as cursor:
                count = ApiSpecialSqlReports.get_event_report_count_sql(
                    cursor,
                    query_event_id,
                    query_start_at,
                    query_end_at,
                    query_param_status_included,
                    query_param_status_excluded,
                    query_param_pending_items_included,
                    query_param_pending_items_excluded,
                    query_param_recipient_id,
                    query_param_agent_id
                )

            next_page = query_param_page + 1 if (count > (query_param_page_size * query_param_page)) else None
            if next_page is not None:
                next_page = replace_query_param(request.build_absolute_uri(), 'page', next_page)

            previous_page = query_param_page - 1 if query_param_page > 1 else None
            if previous_page is not None:
                previous_page = replace_query_param(request.build_absolute_uri(), 'page', previous_page)

            return Response({
                'count': count,
                'next': next_page,
                'previous': previous_page,
                'results': result
            })
            
        if (query_event_id is not None):
            return Response(result[0])
        
        return Response(result)

    # def get(cls, request, business_name=None, event_id=None):
    #     serializer_class = EventSerializer
    #     no_booking_serializer_class = EventNoBookingSerializer
    #     query_params = prepare_query_params(request.GET)

    #     serializer = serializer_class if request.GET.get(ApiSpecialKeys.INCLUDE_BOOKING, False) else no_booking_serializer_class

    #     queryset = serializer.get_default_queryset()
    #     reqBod = request.GET.get(ApiSpecialKeys.YEAR_MONTH)

    #     if business_name:
    #         queryset = queryset.filter(booking__business__name=business_name)

    #     if reqBod != '':
    #         queryset = queryset.filter(booking__status='delivered', start_at__icontains=reqBod)
    #     else:
    #         queryset = queryset.filter(booking__status='delivered')
                
        
    #     queryset = cls.apply_filters(queryset.order_by('-start_at'), query_params)
    #     serialized = serializer(queryset, many=True)
    #     report_values = []
    #     for obj in serialized.data:
            
    #         def representation_phone(repr):
    #                 return repr["phone"]
                    
    #         def representation_email(repr):
    #                 return repr["email"]
                    
    #         def representation_fax(repr):
    #                 return repr["fax"]
            
    #         phone = map(representation_phone, obj['affiliates'][0]['recipient']['contacts'])
    #         email = map(representation_email, obj['affiliates'][0]['recipient']['contacts'])
    #         fax = map(representation_fax, obj['affiliates'][0]['recipient']['contacts'])
            
    #         phoneUnzip = ", ".join(list(phone))
    #         emailUnzip = ", ".join(list(email))
    #         faxUnzip = ", ".join(list(fax))
            
    #         def representation_note(repr):
    #                 return repr["text"]
    #         notes = map(representation_note, obj['booking']['companies'][0]['notes'])
    #         notesUnzip = ", ".join(list(notes))
            
    #         def representation_auth(repr):
    #             if repr["status"] == "ACCEPTED":
    #                 return repr['last_updated_at']
    #             else:
    #                 return ""
    #         authorized = list(map(representation_auth, obj['authorizations']))
    #         non_empty_authorized = list(filter(lambda x: x != "", authorized))
    #         if non_empty_authorized:
    #             latest_authorization = max(non_empty_authorized, key=lambda x: x.split()[0])
    #         else:
    #             latest_authorization = ""
            
    #         def representation_auth_by(repr):
    #             if repr["status"] == "ACCEPTED" and latest_authorization \
    #                 != "" and repr['last_updated_at'] == latest_authorization:
    #                 payer = Payer.objects.filter(id=repr["authorizer"]).values()
    #                 user_authorizer = User.objects.filter(id=payer[0]['user_id']).values()
    #                 return f"{user_authorizer[0]['first_name']} {user_authorizer[0]['last_name']}"
    #             else:
    #                 return ""
    #         auth_by = map(representation_auth_by, obj['authorizations'])
    #         auth_byUnzip = ", ".join(list(auth_by))
            
    #         obj_date = obj['start_at'].split('.')[0] if obj['start_at'] != None else ''
    #         obj_arrive = obj['reports'][-1]['arrive_at'].split('.')[0] if obj['reports'][-1]['arrive_at'] != None else ''
    #         obj_start = obj['reports'][-1]['start_at'].split('.')[0] if obj['reports'][-1]['start_at'] != None else ''
    #         obj_end = obj['reports'][-1]['end_at'].split('.')[0] if obj['reports'][-1]['end_at'] != None else ''
    #         print(obj_date)
            
    #         if obj_date.__len__() != 0:
    #             dt = datetime.fromisoformat(obj_date.split('Z')[0]) 
    #             dt_date = dt.date()
    #         else:
    #             dt_date
    #         if obj_arrive.__len__() != 0:
    #             dt = datetime.fromisoformat(obj_arrive.split('Z')[0]) 
    #             dt_arrive = dt.time()
    #         else:
    #             dt_arrive = ''
    #         if obj_start.__len__() != 0:
    #             dt = datetime.fromisoformat(obj_start.split('Z')[0]) 
    #             dt_start = dt.time()
    #         else:
    #             dt_start = ''
    #         if obj_end.__len__() != 0:
    #             dt = datetime.fromisoformat(obj_end.split('Z')[0])
    #             dt_end = dt.time()
    #         else:
    #             dt_end = ''
            
    #         contacts = obj['booking']['companies'][0]['contacts']
    #         if len(contacts) == 1:
    #             contactsUnzip = contacts[0]
    #         elif len(contacts) > 1:
    #             contactsUnzip = ", ".join(contacts)
    #         else:
    #             contactsUnzip = "" 
            
    #         language = Language.objects.filter(alpha3=obj['booking']['target_language_alpha3']).values()

    #         def rates_values(values):
    #             if (len(values.filter(extra__data__contains='"Common Languages"')) > 0 and language[0]['common'] == True) or \
    #             (len(values.filter(extra__data__contains='"Rare Languages"')) > 0 and language[0]['common'] == False) or \
    #             len(values.filter(extra__data__contains='"All Languages"')) > 0:
    #                 return values.values_list('bill_amount')
    #             else:
    #                 return [[""]]
    #         rates = Rate.objects.all().filter(root__description=obj['booking']['service_root']['description']).order_by('-pk')
    #         price = []
    #         if len(rates) > 0:
    #             if len(rates.values_list('company')[0]) > 0:
    #                 if rates.values_list('company')[0][0] != None:
    #                     if obj['payer'] is not None and obj['payer']['companies'] != []:
    #                         rates = rates.filter(company=obj['payer']['companies'][-1]['id'])
    #                         price.append(rates_values(rates))
    #                     else:
    #                         price.append(rates_values(rates))
    #                 else:
    #                     price.append(rates_values(rates))
    #         certification_number = []
    #         certification = []
    #         if(len(obj['booking']['services']) != 0):
    #             provider = Provider.objects.filter(id=obj['booking']['services'][0]['provider']['id'])
    #             if(provider.filter(extra__key='certifications')):
    #                 extract_certification = provider.filter(extra__key='certifications').values_list('extra__data')[0][0]
    #                 jsoncertification = json.loads(extract_certification)
    #                 if(len(jsoncertification) != 0):
    #                     certification_number = jsoncertification[-1]['certificate_number']
    #                     certification = Category.objects.filter(id=jsoncertification[-1]['certificate_id']).values('description')[0]['description']
            
    #         values = {
    #             #Patient
    #             "first_name": obj['affiliates'][0]['recipient']['first_name'],
    #             "last_name": obj['affiliates'][0]['recipient']['last_name'],
    #             "date_of_birth": obj['affiliates'][0]['recipient']['date_of_birth'],
    #             "phone_contact": phoneUnzip if obj['affiliates'][0]['recipient']['contacts'] != [] else "",
    #             "email_contact": emailUnzip if obj['affiliates'][0]['recipient']['contacts'] != [] else "",
    #             "fax_contact": faxUnzip if obj['affiliates'][0]['recipient']['contacts'] != [] else "",
    #             "address": obj['affiliates'][0]['recipient']['location']['address'] if obj['affiliates'][0]['recipient']['location'] is not None else '',
    #             "unit_number": obj['affiliates'][0]['recipient']['location']['unit_number'] if obj['affiliates'][0]['recipient']['location'] is not None else "",
    #             "city": obj['affiliates'][0]['recipient']['location']['city'] if obj['affiliates'][0]['recipient']['location'] is not None else '',
    #             "state": obj['affiliates'][0]['recipient']['location']['state'] if obj['affiliates'][0]['recipient']['location'] is not None else '',
    #             "country": obj['affiliates'][0]['recipient']['location']['country'] if obj['affiliates'][0]['recipient']['location'] is not None else '',
    #             "zip": obj['affiliates'][0]['recipient']['location']['zip'] if obj['affiliates'][0]['recipient']['location'] is not None else '',
    #             #Event
    #             "public_id": obj['booking']['public_id'],
    #             "date": dt_date,
    #             "arrive_time": dt_arrive,
    #             "start_time": dt_start,
    #             "end_time": dt_end,
    #             "date_of_injury": obj['date_of_injury'] if obj.__contains__('date_of_injury') else "",
    #             "payer_company_type": obj['payer']['companies'][-1]['type'] if obj['payer'] != None else "",
    #             "payer_company_name": obj['payer']['companies'][-1]['name'] if obj['payer'] != None else "",
    #             "payer_company_address": obj['payer']['companies'][-1]['locations'][-1]['address'] if obj['payer'] != None and obj['payer']['companies'] != [] and obj['payer']['companies'][-1]['locations'] != [] else "",
    #             "payer_company_city": obj['payer']['companies'][-1]['locations'][-1]['city'] if obj['payer'] != None and obj['payer']['companies'] != [] and obj['payer']['companies'][-1]['locations'] != [] else "",
    #             "payer_company_state": obj['payer']['companies'][-1]['locations'][-1]['state'] if obj['payer'] != None and obj['payer']['companies'] != [] and obj['payer']['companies'][-1]['locations'] != [] else "",
    #             "payer_company_send_method": obj['payer']['companies'][-1]['send_method'] if obj['payer'] != None and obj['payer']['companies'] != [] and obj['payer']['companies'][-1]['locations'] != [] else "",
    #             "provider": f"{obj['agents'][-1]['first_name']} {obj['agents'][-1]['last_name']}" if obj['agents'] != [] else "",
    #             "claim_number": obj['claim_number'] if obj.__contains__('claim_number') else "",
    #             "clinic": obj['booking']['companies'][0]['name'],
    #             "clinic_address": obj['booking']['companies'][0]['locations'][0]['address'] if obj['booking']['companies'][0]['locations'] != [] else "",
    #             "clinic_unit_number": obj['booking']['companies'][0]['locations'][0]['unit_number'] if obj['booking']['companies'][0]['locations'] != [] else "",
    #             "clinic_city": obj['booking']['companies'][0]['locations'][0]['city'] if obj['booking']['companies'][0]['locations'] != [] else "",
    #             "clinic_state": obj['booking']['companies'][0]['locations'][0]['state'] if obj['booking']['companies'][0]['locations'] != [] else "",
    #             "clinic_country": obj['booking']['companies'][0]['locations'][0]['country'] if obj['booking']['companies'][0]['locations'] != [] else "",
    #             "clinic_zip": obj['booking']['companies'][0]['locations'][0]['zip'] if obj['booking']['companies'][0]['locations'] != [] else "",
    #             "send_method": obj['booking']['companies'][0]['send_method'],
    #             "notes": notesUnzip,
    #             "contacts": contactsUnzip,
    #             "languague": language[0]['name'],
    #             "type_of_appointment": obj['description'],
    #             "interpreter": f"{obj['booking']['services'][-1]['provider']['first_name']} {obj['booking']['services'][-1]['provider']['last_name']}" if obj['booking']['services'] != [] else "",
    #             "modality": obj['booking']['service_root']['description'],
    #             "status_report": obj['reports'][-1]['status'] if obj['reports'] != [] else "",
    #             "authorized": "ACCEPTED" if latest_authorization != "" else "",
    #             "auth_by": auth_byUnzip,
    #             "operators_first_name": obj['booking']['operators'][-1]['first_name'] if obj['booking']['operators'] != [] else "",
    #             "operators_last_name": obj['booking']['operators'][-1]['last_name'] if obj['booking']['operators'] != [] else "",
    #             "price": price[0][0][0] if len(price) > 0 else price,
    #             "certification_number": certification_number,
    #             "certification": certification,
                
    #         }
            
    #         report_values.append(values)
        
    #     return Response(report_values)
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
