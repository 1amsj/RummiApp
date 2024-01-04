from requests import Response
from core_api.constants import ApiSpecialKeys
from core_api.decorators import expect_does_not_exist
from core_api.services import prepare_query_params
from core_api.services_datamanagement import handle_events_bulk
from core_api.views import StandardResultsSetPagination, basic_view_manager
from core_backend.models import Event, User
from core_api.decorators import expect_does_not_exist, expect_key_error
from rest_framework import status
from core_api.services_datamanagement import update_event_wrap, create_reports_wrap, create_event
from core_api.exceptions import BadRequestException
from django.db import transaction

from core_backend.serializers.serializers import EventNoBookingSerializer, EventSerializer
from core_backend.serializers.serializers_patch import EventPatchSerializer
import json

class ManageEventsMixin:

    @classmethod
    @expect_does_not_exist(Event)
    def get(cls, request, business_name=None, event_id=None):
        if event_id:
            event = cls.serializer_class.get_default_queryset().get(id=event_id)
            serialized = cls.serializer_class(event)
            return Response(serialized.data)

        include_booking = request.GET.get(ApiSpecialKeys.INCLUDE_BOOKING, False)
        query_params = prepare_query_params(request.GET)

        serializer = cls.serializer_class if include_booking else cls.no_booking_serializer_class
        
        queryset = serializer.get_default_queryset()
        
        reqBod = request.GET.get('status')
        if 'page' in request.GET or 'page_size' in request.GET:
            if business_name:
                queryset = queryset.filter(booking__business__name=business_name)
            col = []
            
            filtered = []
            queryset = queryset.order_by('-id')
            serializerComplete = serializer(queryset, many=True)
            serializeData = serializerComplete.data

            # Type of status
            if ('delivered' in reqBod):
                for item in serializeData:
                    if('claim_number' in item and 'payer' != None and 
                       'payer_company' != None and item['booking']['services'] != []):
                        for report in item.get('reports', []):
                            if report.get('status') == 'COMPLETED':
                                filtered.append(item)
                                break

                col.append('col_d')
                
            if ('override' in reqBod):
                for item in serializeData:
                    for report, authorization in zip(item.get('reports', []), item.get('authorizations', [])):
                        if authorization.get('status') == 'OVERRIDE' and report.get('status') != 'COMPLETED':
                            filtered.append(item)
                            break

            if ('authorized' in reqBod):
                for item in serializeData:
                    for report, authorization in zip(item.get('reports', []), item.get('authorizations', [])):
                        if authorization.get('status') == 'ACCEPTED' and report.get('status') != 'COMPLETED':
                            filtered.append(item)
                            break

            if('booked' in reqBod):
                for item in serializeData:
                    if('claim_number' in item and 'payer' != None and 'payer_company' != None):
                        filtered.append(item)
                
            if ('pending' in reqBod):
                for item in serializeData:
                    if('claim_number' not in item or 'payer' == None or 'payer_company' == None):
                        filtered.append(item)
                
            sorted_filtered = sorted(filtered, key=lambda x: x['id'], reverse=True)
            
            unique_ids = set()
            unique_filtered = []

            for item in sorted_filtered:
                id_value = item['id']
                if id_value not in unique_ids:
                    unique_ids.add(id_value)
                    unique_filtered.append(item)

            sorted_filtered = unique_filtered
                
            paginator = cls.pagination_class()
            paginated_two = paginator.paginate_queryset(sorted_filtered, request)
            serializedfilt = serializer(paginated_two, many=True)
            return paginator.get_paginated_response(serializedfilt.__dict__['instance'])
        else:
            # No pagination parameters, return all results
            queryset = cls.apply_filters(queryset, query_params)
            serialized = serializer(queryset, many=True)
            return Response(serialized.data)

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
        data = request.data

        # Extract query keys
        try:
            patch_query = data.pop(ApiSpecialKeys.PATCH_QUERY)
        except KeyError:
            raise BadRequestException('Missing patch query')

        # Get target queryset
        query_params = prepare_query_params(patch_query)
        queryset = cls.serializer_class.get_default_queryset()
        queryset = cls.apply_filters(queryset, query_params)

        # Apply patch to each event
        for event in queryset:
            serializer = cls.patch_serializer_class(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.patch(event, business_name)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    @transaction.atomic
    @expect_does_not_exist(Event)
    def delete(request, event_id=None):
        Event.objects.get(id=event_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class ManageEventsFilters(ManageEventsMixin, basic_view_manager(Event, EventSerializer)):
    serializer_class = EventSerializer
    no_booking_serializer_class = EventNoBookingSerializer
    patch_serializer_class = EventPatchSerializer
    pagination_class = StandardResultsSetPagination