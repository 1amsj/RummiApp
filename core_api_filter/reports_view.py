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
