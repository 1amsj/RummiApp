from typing import Type, Union

from django.db import models, transaction
from django.db.models import Q, QuerySet
from django.utils import timezone
from rest_framework import generics, serializers, status
from rest_framework.authentication import BasicAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.pagination import PageNumberPagination

from core_api.constants import ApiSpecialKeys
from core_api.decorators import expect_does_not_exist, expect_key_error
from core_api.exceptions import BadRequestException
from core_api.permissions import CanManageOperators, CanPushFaxNotifications, can_manage_model_basic_permissions
from core_api.serializers import CustomTokenObtainPairSerializer, RegisterSerializer
from core_api.services import prepare_query_params
from core_api.services_datamanagement import create_affiliations_wrap, create_agent_wrap, create_booking, create_company, create_company_relationships_wrap, create_event, \
    create_events_wrap, create_offers_wrap, create_operator_wrap, create_payer_wrap, create_provider_wrap, \
    create_recipient_wrap, \
    create_reports_wrap, create_requester_wrap, create_services_wrap, create_service_areas_wrap, create_user, handle_agents_bulk, handle_company_rates_bulk, handle_company_relationships_bulk, handle_events_bulk, \
    handle_services_bulk, handle_service_areas_bulk, update_event_wrap, \
    update_provider_wrap, \
    update_recipient_wrap, update_user
from core_backend.datastructures import QueryParams
from core_backend.models import Affiliation, Agent, Authorization, Booking, Business, Category, Company, CompanyRate, CompanyRelationship, Contact, Event, \
    Expense, ExtraQuerySet, GlobalSetting, Language, Note, Notification, Offer, Operator, Payer, Provider, Recipient, Requester, \
    Service, \
    ServiceArea, ServiceRoot, User
from core_backend.notification_builders import build_from_template
from core_backend.serializers.serializers_light import EventLightSerializer
from core_backend.serializers.serializers import AffiliationSerializer, AgentWithCompaniesSerializer, AuthorizationBaseSerializer, \
    AuthorizationSerializer, BookingNoEventsSerializer, BookingSerializer, CategorySerializer, CompanyRateSerializer, CompanyRelationshipSerializer, \
    CompanyWithParentSerializer, CompanyWithRolesSerializer, EventNoBookingSerializer, EventSerializer, \
    ExpenseSerializer, GlobalSettingSerializer, LanguageSerializer, NoteSerializer, NotificationSerializer, OfferSerializer, OperatorSerializer, \
    PayerSerializer, ProviderSerializer, RecipientSerializer, RequesterSerializer, ServiceRootBaseSerializer, \
    ServiceRootBookingSerializer, ServiceSerializer, ServiceAreaSerializer, UserSerializer
from core_backend.serializers.serializers_create import AffiliationCreateSerializer, AgentCreateSerializer, \
    AuthorizationCreateSerializer, CategoryCreateSerializer, CompanyCreateSerializer, CompanyRateCreateSerializer, CompanyRelationshipCreateSerializer, ExpenseCreateSerializer, GlobalSettingCreateSerializer, \
    LanguageCreateSerializer, NoteCreateSerializer, NotificationCreateSerializer, OfferCreateSerializer, \
    OperatorCreateSerializer, \
    PayerCreateSerializer, RecipientCreateSerializer, ServiceCreateSerializer, ServiceAreaCreateSerializer, ServiceRootCreateSerializer, \
    UserCreateSerializer
from core_backend.serializers.serializers_patch import EventPatchSerializer
from core_backend.serializers.serializers_update import AuthorizationUpdateSerializer, BookingUpdateSerializer, \
    CategoryUpdateSerializer, CompanyRateUpdateSerializer, CompanyRelationshipUpdateSerializer, CompanyUpdateSerializer, ExpenseUpdateSerializer, GlobalSettingUpdateSerializer, LanguageUpdateSerializer, \
    OfferUpdateSerializer, ProviderUpdateSerializer, RecipientUpdateSerializer, ServiceAreaUpdateSerializer, ServiceRootUpdateSerializer
from core_backend.services.concord.concord_interfaces import FaxPushNotification, FaxStatusCode
from core_backend.services.core_services import filter_params, is_extendable
from core_backend.settings import VERSION_FILE_DIR
from django.core.mail import BadHeaderError, send_mail, EmailMultiAlternatives
from django.http import HttpResponse, JsonResponse
from django.conf import settings

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.filter(is_deleted=False)
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer


class UserViewSet(generics.ListAPIView):
    queryset = User.objects.filter(is_deleted=False)
    permission_classes = (AllowAny,)
    serializer_class = UserSerializer

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100
    page_query_param = 'page'

@api_view(['POST'])
@transaction.atomic
@permission_classes([AllowAny])
def register_user(request):
    serializer = UserCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.create()
    return Response(user.id, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def get_routes(request):
    routes = [
        'token/',
        'register/',
        'token/refresh/'
    ]
    return Response(['api/v1/' + r for r in routes])


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def manage_users(request):
    users = User.objects.filter(is_deleted=False)

    # Get filters
    email = request.query_params.get('email')
    first_name = request.query_params.get('first_name')
    last_name = request.query_params.get('last_name')

    # Filter
    if email:
        users = users.filter(email__icontains=email)
    if first_name:
        users = users.filter(first_name__icontains=first_name)
    if last_name:
        users = users.filter(last_name__icontains=last_name)

    serialized = UserSerializer(users, many=True)
    return Response(serialized.data)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def test_end_point(request):
    if request.method == 'GET':
        data = f"Congratulation {request.user}, your API just responded to GET request"
        return Response({'response': data}, status=status.HTTP_200_OK)
    elif request.method == 'POST':
        text = request.POST.get('text')
        data = f'Congratulation your API just responded to POST request with text: {text}'
        return Response({'response': data}, status=status.HTTP_200_OK)
    return Response({}, status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_version(request):
    try:
        with open(VERSION_FILE_DIR, 'r') as f:
            return Response(f.readline().strip('\n'))
    except FileNotFoundError:
        return Response("unknown")


@api_view(['GET'])
@permission_classes([IsAuthenticated, can_manage_model_basic_permissions(Business._meta.model_name)])
def search_bookings(request):
    # This view was made for the interpretation business alone and is not meant to be used in a generic application
    # without making the proper modifications

    person_query = Q(is_deleted=False)
    first_name = request.GET.get('first_name')
    last_name = request.GET.get('last_name')

    if first_name and not last_name:
        person_query &= (Q(first_name__icontains=first_name) | Q(last_name__icontains=first_name))

    elif first_name:
        person_query &= Q(first_name__icontains=first_name)

    if last_name:
        person_query &= Q(last_name__icontains=last_name)

    eligible_users = UserSerializer.get_default_queryset().filter(person_query)
    eligible_services = ServiceSerializer.get_default_queryset().filter(
        is_deleted=False,
        provider__user__in=eligible_users,
    )
    eligible_affiliations = AffiliationSerializer.get_default_queryset().filter(
        is_deleted=False,
        recipient__user__in=eligible_users,
    )
    eligible_events = EventSerializer.get_default_queryset().filter(
        is_deleted=False,
        affiliates__in=eligible_affiliations,
    )

    booking_query = Q(is_deleted=False) & (Q(services__in=eligible_services) | Q(events__in=eligible_events))

    queryset = (BookingSerializer
                .get_default_queryset()
                .filter(booking_query)
                .distinct('id')
                )

    if date := request.GET.get('date'):
        queryset_dob_filtered = Booking.objects.all().filter(
            events__affiliates__recipient__user__date_of_birth__contains=date,
        )
        queryset_doi_filtered = queryset.filter_by_extra(
            related_prefix='events__',
            date_of_injury__contains=date,
        )

        queryset = queryset_dob_filtered.union(queryset_doi_filtered)

    if booking_public_id := request.GET.get('booking_id'):
        queryset = queryset.filter(public_id__contains=booking_public_id)

    serialized = BookingSerializer(queryset, many=True)
    return Response(serialized.data)


@api_view(['POST'])
@authentication_classes([BasicAuthentication])
@permission_classes([CanPushFaxNotifications])
@transaction.atomic
def handle_fax_push_notification(request):
    data = FaxPushNotification.from_request_data(request.data)

    if data.job_status_id not in (FaxStatusCode.SUCCESS, FaxStatusCode.FAILURE):
        print(f'Fax job {data.job_id} is still in progress', data.__dict__)
        return Response(status=status.HTTP_204_NO_CONTENT)

    notification = Notification.objects.get(job_id=data.job_id)
    notification.status = (
        Notification.Status.SENT
        if data.job_status_id == FaxStatusCode.SUCCESS
        else Notification.Status.FAILED
    )
    notification.status_message = data.status_description
    notification.sent_at = timezone.now()  # Notice that this is not the actual time of sending
    notification.save()

    print(f'Fax job {data.job_id} has been processed', data.__dict__)

    return Response(status=status.HTTP_204_NO_CONTENT)


def basic_view_manager(model: Type[models.Model], serializer: Type[serializers.ModelSerializer]):
    class ManageModel(APIView):
        permission_classes = [IsAuthenticated, can_manage_model_basic_permissions(model._meta.model_name)]

        @staticmethod
        def apply_nested_filters(queryset: Union[QuerySet[model], ExtraQuerySet[model]], nested_params: QueryParams):
            return queryset.filter(**nested_params.to_dict())

        @classmethod
        def apply_filters(cls, queryset: Union[QuerySet[model], ExtraQuerySet[model]], params: QueryParams):
            base_params, extra_params, nested_params = filter_params(model, params)

            if not base_params.is_empty():
                queryset = queryset.filter(**base_params.to_dict())

            if is_extendable(model) and not extra_params.is_empty():
                queryset = queryset.filter_by_extra_query_params(extra_params)

            if not nested_params.is_empty():
                queryset = cls.apply_nested_filters(queryset, nested_params)

            return queryset.distinct()

        @classmethod
        def filter_related_per_deleted(cls, queryset: QuerySet[model]):
            pass

        @classmethod
        def get(cls, request):
            query_params = prepare_query_params(request.GET)
            queryset = cls.apply_filters(model.objects.filter(is_deleted=False), query_params)
            serialized = serializer(queryset, many=True)
            return Response(serialized.data)

    return ManageModel


def user_subtype_view_manager(model: Type[models.Model], serializer: Type[serializers.ModelSerializer]):
    class ManageUserSubtypeModel(basic_view_manager(model, serializer)):
        @staticmethod
        def apply_nested_filters(queryset: Union[QuerySet[model], ExtraQuerySet[model]], nested_params: QueryParams):
            # do not apply by default
            return queryset

        @classmethod
        def apply_filters(cls, queryset, params):
            base_params, extra_params, nested_params = filter_params(model, params)

            if not base_params.is_empty():
                queryset = queryset.filter(**base_params.to_dict())

            user_params, extra_params, _ = filter_params(User, extra_params)
            if not user_params.is_empty():
                queryset = queryset.filter(**user_params.to_dict('user__'))

            if is_extendable(model) and not extra_params.is_empty():
                queryset = queryset.filter_by_extra_query_params(extra_params)

            queryset = cls.apply_nested_filters(queryset, nested_params)

            return queryset

        @classmethod
        def filter_related_per_deleted(cls, queryset: QuerySet[model]):
            return queryset.filter(
                user__in=User.objects.not_deleted(),
            )

    return ManageUserSubtypeModel

class ManageGlobalSettings(basic_view_manager(GlobalSetting, GlobalSettingSerializer)):
    @classmethod
    @expect_does_not_exist(GlobalSetting)
    def get(cls, request, global_setting_id=None):
        if global_setting_id:
            setting = GlobalSetting.objects.all().get(id=global_setting_id)
            serialized = GlobalSettingSerializer(setting)
            return Response(serialized.data)

        query_params = prepare_query_params(request.GET)

        queryset = GlobalSettingSerializer.get_default_queryset()

        queryset = cls.apply_filters(queryset, query_params)

        serialized = GlobalSettingSerializer(queryset, many=True)
        return Response(serialized.data)

    @staticmethod
    @transaction.atomic
    @expect_does_not_exist(GlobalSetting)
    def post(request, business_name = None):
        serializer = GlobalSettingCreateSerializer(data=request.data)
        business_name = request.data.pop(ApiSpecialKeys.BUSINESS)
        serializer.is_valid(raise_exception=True)
        setting_id = serializer.create(business_name)
        return Response(setting_id, status=status.HTTP_201_CREATED)

    @staticmethod
    @transaction.atomic
    @expect_does_not_exist(GlobalSetting)
    def put(request, global_setting_id=None):
        
        business_name = request.data.pop(ApiSpecialKeys.BUSINESS)
        setting = GlobalSetting.objects.get(id=global_setting_id)
        serializer = GlobalSettingUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.update(setting, business_name)
        return Response(status=status.HTTP_204_NO_CONTENT)

class ManageUsers(basic_view_manager(User, UserSerializer)):
    @classmethod
    @expect_does_not_exist(User)
    def get(cls, request, user_id=None):
        if user_id:
            user = User.objects.all().get(id=user_id)
            serialized = UserSerializer(user)
            return Response(serialized.data)

        query_params = prepare_query_params(request.GET)

        queryset = UserSerializer.get_default_queryset()

        queryset = cls.apply_filters(queryset, query_params)

        serialized = UserSerializer(queryset, many=True)
        return Response(serialized.data)

    @staticmethod
    @transaction.atomic
    def post(request, business_name=None):
        """
        Create a new user, by default assign them a recipient role and an affiliation to null
        Said assignment can be avoided by setting _recipient_data and (or both) _affiliation_datalist to empty ({} or [])
        respectively
        """
        # Create user
        # Extract roles data before the serializer deals with it
        agent_data = request.data.pop(ApiSpecialKeys.AGENT_DATA, None)

        operator_data = request.data.pop(ApiSpecialKeys.OPERATOR_DATA, None)

        payer_data = request.data.pop(ApiSpecialKeys.PAYER_DATA, {
            "companies": [],
            "method": '',
        })

        provider_data = request.data.pop(ApiSpecialKeys.PROVIDER_DATA, None)

        recipient_data = request.data.pop(ApiSpecialKeys.RECIPIENT_DATA, {
            "companies": [],
            "notes": [],
        })

        requester_data = request.data.pop(ApiSpecialKeys.REQUESTER_DATA, {
            "companies": [],
        })

        user_id = create_user(
            request.data
        ) 

        response = {"user_id": user_id}

        if agent_data:
            agent_id = create_agent_wrap(
                data=agent_data,
                user_id=user_id,
                business_name=business_name,
            )

            response["agent_id"] = agent_id

        if operator_data:
            operator_id = create_operator_wrap(
                operator_data,
                user_id=user_id,
            )

            response["operator_id"] = operator_id

        if payer_data:
            payer_id = create_payer_wrap(
                payer_data,
                user_id=user_id,
            )

            response["payer_id"] = payer_id

        if provider_data:
            service_datalist = provider_data.pop(ApiSpecialKeys.SERVICE_DATALIST, None)
            service_area_datalist = provider_data.pop(ApiSpecialKeys.SERVICE_AREA_DATALIST, None)

            provider_id = create_provider_wrap(
                provider_data,
                business_name=business_name,
                user_id=user_id,
            )

            if service_datalist:
                service_ids = create_services_wrap(
                    service_datalist,
                    business_name,
                    provider_id=provider_id,
                )
                response["service_ids"] = service_ids

            if service_area_datalist:
                service_area_ids = create_service_areas_wrap(
                    service_area_datalist,
                    provider_id=provider_id,
                )
                response["service_area_ids"] = service_area_ids

            response["provider_id"] = provider_id

        if recipient_data:
            # Create recipient and affiliation
            # Extract affiliation data before the serializer deals with it
            affiliation_datalist = recipient_data.pop(ApiSpecialKeys.AFFILIATION_DATALIST, [{"company": None}])

            recipient_id = create_recipient_wrap(
                recipient_data,
                business_name,
                user_id=user_id
            )

            affiliation_ids = create_affiliations_wrap(
                affiliation_datalist,
                business_name,
                recipient_id=recipient_id
            )

            response["recipient_id"] = recipient_id
            response["affiliation_ids"] = affiliation_ids

        if requester_data:
            requester_id = create_requester_wrap(
                requester_data,
                business_name,
                user_id=user_id
            )

            response["requester_id"] = requester_id


        # Respond with complex ids object
        return Response(response, status=status.HTTP_201_CREATED)

    @staticmethod
    @transaction.atomic
    @expect_does_not_exist(User)
    @expect_does_not_exist(Contact)
    @expect_does_not_exist(Recipient)
    def put(request, user_id=None):
        """
        Update a user; if _provider_data or _recipient_data provided, update them too
        """
        # Update user
        # Extract management data before the serializer deals with it
        business_name = request.data.pop(ApiSpecialKeys.BUSINESS, None)
        provider_data = request.data.pop(ApiSpecialKeys.PROVIDER_DATA, None)
        recipient_data = request.data.pop(ApiSpecialKeys.RECIPIENT_DATA, None)

        user = User.objects.get(id=user_id)
        update_user(
            request.data,
            user_instance=user
        )

        # Update provider
        if provider_data:
            service_datalist = provider_data.pop(ApiSpecialKeys.SERVICE_DATALIST, None)
            service_area_datalist = provider_data.pop(ApiSpecialKeys.SERVICE_AREA_DATALIST, None)

            update_provider_wrap(
                provider_data,
                business_name,
                user_id,
                provider_instance=user.as_provider
            )

            if service_datalist:
                handle_services_bulk(
                    service_datalist,
                    business_name,
                    provider_id=user.as_provider.id,
                )
            
            if service_area_datalist:
                handle_service_areas_bulk(
                    service_area_datalist,
                    provider_id=user.as_provider.id,
                )

        # Update recipient
        if recipient_data:
            update_recipient_wrap(
                recipient_data,
                business_name,
                user_id,
                recipient_instance=user.as_recipient
            )

        # Done
        return Response(status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    @transaction.atomic
    def delete(request, user_id=None):
        user = User.objects.get(id=user_id)
        user.is_deleted = True
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ManageAgents(user_subtype_view_manager(Agent, AgentWithCompaniesSerializer)):
    @staticmethod
    @transaction.atomic
    @expect_key_error
    @expect_does_not_exist(Agent)
    def post(request, business_name=None):
        serializer = AgentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        agent = serializer.create(business_name)
        return Response(agent.id, status=status.HTTP_201_CREATED)

    @classmethod
    def get(cls, request, buisiness_name=None, agent_id=None):
        if agent_id:
            agent = Agent.objects.all().not_deleted('user').get(id=agent_id)
            serialized = AgentWithCompaniesSerializer(agent)
            return Response(serialized.data)

        query_params = prepare_query_params(request.GET)

        queryset = AgentWithCompaniesSerializer.get_default_queryset()

        queryset = cls.apply_filters(queryset, query_params)

        serialized = AgentWithCompaniesSerializer(queryset, many=True)
        return Response(serialized.data)

class ManageOperators(user_subtype_view_manager(Operator, OperatorSerializer)):
    permission_classes = [CanManageOperators]
    @staticmethod
    def apply_nested_filters(queryset, nested_params):
        if nested_params.is_empty():
            return queryset

        service_params, extra_params, _ = filter_params(Service, nested_params.get('services', {}))
        if not service_params.is_empty():
            queryset = queryset.filter(**service_params.to_dict('services__'))

        if not extra_params.is_empty():
            queryset = queryset.filter_by_extra_query_params(extra_params, related_prefix='services')

        return queryset
    
    @staticmethod
    @transaction.atomic
    @expect_key_error
    @expect_does_not_exist(Operator)
    def post(request, business_name=None):
        serializer = OperatorCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        operator = serializer.create()
        return Response(operator.id, status=status.HTTP_201_CREATED)

    @classmethod
    @expect_does_not_exist(Operator)
    def get(cls, request, business_name=None, operator_id=None):
        if operator_id:
            operator = Operator.objects.all().not_deleted('user').get(id=operator_id)
            serialized = OperatorSerializer(operator)
            return Response(serialized.data)

        query_params = prepare_query_params(request.GET)

        queryset = OperatorSerializer.get_default_queryset()

        queryset = cls.apply_filters(queryset, query_params)

        serialized = OperatorSerializer(queryset, many=True)
        return Response(serialized.data)

class ManagePayers(user_subtype_view_manager(Payer, PayerSerializer)):
    @staticmethod
    @transaction.atomic
    @expect_key_error
    @expect_does_not_exist(Payer)
    def post(request):
        serializer = PayerCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payer = serializer.create()
        return Response(payer.id, status=status.HTTP_201_CREATED)

    @classmethod
    def get(cls, request, buisiness_name=None, payer_id=None):
        if payer_id:
            payer = Payer.objects.all().not_deleted('user').get(id=payer_id)
            serialized = PayerSerializer(payer)
            return Response(serialized.data)

        query_params = prepare_query_params(request.GET)

        queryset = PayerSerializer.get_default_queryset()

        queryset = cls.apply_filters(queryset, query_params)

        serialized = PayerSerializer(queryset, many=True)
        return Response(serialized.data)



class ManageProviders(user_subtype_view_manager(Provider, ProviderSerializer)):

    pagination_class = StandardResultsSetPagination

    @staticmethod
    def apply_nested_filters(queryset, nested_params):
        if nested_params.is_empty():
            return queryset

        service_params, extra_params, _ = filter_params(Service, nested_params.get('services', {}))
        if not service_params.is_empty():
            queryset = queryset.filter(**service_params.to_dict('services__'))

        if not extra_params.is_empty():
            queryset = queryset.filter_by_extra_query_params(extra_params, related_prefix='services')

        return queryset

    @classmethod
    @expect_does_not_exist(Provider)
    def get(cls, request, business_name=None, provider_id=None):
        if provider_id:
            provider = Provider.objects.all().not_deleted('user').get(id=provider_id)
            serialized = ProviderSerializer(provider)
            return Response(serialized.data)

        query_params = prepare_query_params(request.GET)

        queryset = ProviderSerializer.get_default_queryset()

        if 'page' in request.GET or 'page_size' in request.GET:
            queryset = queryset.order_by('user__first_name')

            # Apply pagination
            paginator = cls.pagination_class()
            paginated_queryset = paginator.paginate_queryset(queryset, request)
            serialized = ProviderSerializer(paginated_queryset, many=True)
            return paginator.get_paginated_response(serialized.data)
        else:
            # No pagination parameters, return all results
            queryset = cls.apply_filters(queryset, query_params)
            serialized = ProviderSerializer(queryset, many=True)
            return Response(serialized.data)

    @staticmethod
    @transaction.atomic
    @expect_does_not_exist(Provider)
    def put(request, provider_id=None):
        provider = Provider.objects.get(id=provider_id)
        business = request.data.pop(ApiSpecialKeys.BUSINESS)
        serializer = ProviderUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.update(provider, business)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ManageRecipients(user_subtype_view_manager(Recipient, RecipientSerializer)):
    @classmethod
    def get(cls, request, business_name=None, recipient_id=None):
        if recipient_id:
            recipient = Recipient.objects.all().not_deleted('user').get(id=recipient_id)
            serialized = RecipientSerializer(recipient)
            return Response(serialized.data)

        query_params = prepare_query_params(request.GET)

        queryset = RecipientSerializer.get_default_queryset()

        queryset = cls.apply_filters(queryset, query_params)

        serialized = RecipientSerializer(queryset, many=True)
        return Response(serialized.data)

    @staticmethod
    @transaction.atomic
    @expect_key_error
    @expect_does_not_exist(Recipient)
    def post(request, business_name=None):
        serializer = RecipientCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        recipient = serializer.create(business_name)
        return Response(recipient.id, status=status.HTTP_201_CREATED)

    @staticmethod
    @transaction.atomic
    @expect_does_not_exist(Recipient)
    def put(request, recipient_id=None):
        recipient = Recipient.objects.get(id=recipient_id)
        business = request.data.pop(ApiSpecialKeys.BUSINESS)
        serializer = RecipientUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.update(recipient, business)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ManageRequesters(user_subtype_view_manager(Requester, RequesterSerializer)):
    @classmethod
    @expect_does_not_exist(Requester)
    def get(cls, request, business_name=None, requester_id=None):
        if requester_id:
            requester = Requester.objects.all().not_deleted('user').get(id=requester_id)
            serialized = RequesterSerializer(requester)
            return Response(serialized.data)

        query_params = prepare_query_params(request.GET)

        queryset = RequesterSerializer.get_default_queryset()

        queryset = cls.apply_filters(queryset, query_params)

        serialized = RequesterSerializer(queryset, many=True)
        return Response(serialized.data)


class ManageAffiliations(basic_view_manager(Affiliation, AffiliationSerializer)):
    @staticmethod
    def apply_nested_filters(queryset, nested_params):
        recipient_params = nested_params.pop('recipient')
        if recipient_params:
            base_params, extra_params, _ = filter_params(Recipient, recipient_params)

            if not base_params.is_empty():
                queryset = queryset.filter(**base_params.to_dict('recipient__'))

            user_params, extra_params, _ = filter_params(User, extra_params)
            if not user_params.is_empty():
                queryset = queryset.filter(**user_params.to_dict('recipient__user__'))

            if is_extendable(Recipient) and not extra_params.is_empty():
                queryset = queryset.filter_by_extra_query_params(extra_params, related_prefix='recipient')

        company_params = nested_params.pop('company')
        if company_params:
            base_params, extra_params, _ = filter_params(Company, company_params)

            if not base_params.is_empty():
                queryset = queryset.filter(**base_params.to_dict('company__'))

            if is_extendable(Company) and not extra_params.is_empty():
                queryset = queryset.filter_by_extra_query_params(extra_params, related_prefix='company')

        return queryset

    @classmethod
    @expect_does_not_exist(Affiliation)
    def get(cls, request, affiliation_id=None):
        if affiliation_id:
            affiliation = Affiliation.objects.all().not_deleted('user').get(id=affiliation_id)
            serialized = AffiliationSerializer(affiliation)
            return Response(serialized.data)

        query_params = prepare_query_params(request.GET)

        queryset = AffiliationSerializer.get_default_queryset()

        queryset = cls.apply_filters(queryset, query_params)

        serialized = AffiliationSerializer(queryset, many=True)
        return Response(serialized.data)


    @staticmethod
    @transaction.atomic
    @expect_key_error
    @expect_does_not_exist(Affiliation)
    def post(request, business_name=None):
        serializer = AffiliationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        affiliation = serializer.create(business_name)
        return Response(affiliation.id, status=status.HTTP_201_CREATED)


class ManageBooking(basic_view_manager(Booking, BookingSerializer)):
    @classmethod
    def get(cls, request, business_name=None, booking_id=None):
        if booking_id:
            booking = Booking.objects.all().not_deleted('business').get(id=booking_id)
            serialized = BookingSerializer(booking)
            return Response(serialized.data)

        include_events = request.GET.get(ApiSpecialKeys.INCLUDE_EVENTS, False)
        recipientId = request.GET.get(ApiSpecialKeys.RECIPIENT_ID, False)
        startDate = request.GET.get(ApiSpecialKeys.START_DATE, False)
        endDate = request.GET.get(ApiSpecialKeys.END_DATE, False)

        query_params = prepare_query_params(request.GET)

        serializer = BookingSerializer if (include_events or recipientId or startDate) else BookingNoEventsSerializer
        queryset = serializer.get_default_queryset()

        if recipientId:
            queryset = queryset.filter(events__affiliates__recipient__user=recipientId)

        if startDate and endDate:
            startDate = startDate.split('T')[0]
            endDate = endDate.split('T')[0]
            queryset = queryset.filter(events__start_at__date__gte=startDate, 
                                events__start_at__date__lte=endDate)
        
        queryset = cls.apply_filters(queryset, query_params)

        serialized = serializer(queryset, many=True)
        return Response(serialized.data)

    @staticmethod
    @transaction.atomic
    @expect_key_error
    def post(request, business_name):
        event_datalist = request.data.pop(ApiSpecialKeys.EVENT_DATALIST, [])
        offer_datalist = request.data.pop(ApiSpecialKeys.OFFER_DATALIST, [])

        booking_id = create_booking(request.data, business_name, request.user)

        event_ids = create_events_wrap(
            datalist=event_datalist,
            business=business_name,
            booking_id=booking_id,
        )

        offer_ids = create_offers_wrap(
            datalist=offer_datalist,
            business=business_name,
            booking_id=booking_id,
        )


        return Response({
            "booking_id": booking_id,
            "event_ids": event_ids,
            "offer_ids": offer_ids,
        }, status=status.HTTP_201_CREATED)

    @staticmethod
    @transaction.atomic
    @expect_does_not_exist(Booking)
    def put(request, booking_id=None):
        booking = Booking.objects.get(id=booking_id)
        business = request.data.pop(ApiSpecialKeys.BUSINESS)
        event_datalist = request.data.pop(ApiSpecialKeys.EVENT_DATALIST, [])
        requester = request.data.pop('requester', None)

        handle_events_bulk(event_datalist, business, requester, booking_id)

        serializer = BookingUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.update(booking, business)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    @transaction.atomic
    @expect_does_not_exist(Event)
    def delete(request, booking_id=None):
        booking = Booking.objects.get(id=booking_id)
        booking.is_deleted = True
        booking.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

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

        if business_name:
            queryset = queryset.filter(booking__business__name=business_name)

        # Check for pagination parameters
        if 'page' in request.GET or 'page_size' in request.GET:
            # Apply pagination
            paginator = cls.pagination_class()
            paginated_queryset = paginator.paginate_queryset(queryset, request)
            serialized = serializer(paginated_queryset, many=True)
            return paginator.get_paginated_response(serialized.data)
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


class ManageEventsLight(ManageEventsMixin, basic_view_manager(Event, EventLightSerializer)):
    serializer_class = EventLightSerializer
    no_booking_serializer_class = EventNoBookingSerializer
    patch_serializer_class = EventPatchSerializer
    pagination_class = StandardResultsSetPagination


class ManageEvents(ManageEventsMixin, basic_view_manager(Event, EventSerializer)):
    serializer_class = EventSerializer
    no_booking_serializer_class = EventNoBookingSerializer
    patch_serializer_class = EventPatchSerializer
    pagination_class = StandardResultsSetPagination

class ManageExpenses(basic_view_manager(Expense, ExpenseSerializer)):
    @classmethod
    @expect_does_not_exist(Expense)
    def get(cls, request, business_name=None, expense_id=None):
        if expense_id:
            expense = Expense.objects.all().not_deleted('booking').get(id=expense_id)
            serialized = ExpenseSerializer(expense)
            return Response(serialized.data)
        try:
            query_params = prepare_query_params(request.GET)

            queryset = ExpenseSerializer.get_default_queryset()

            queryset = cls.apply_filters(queryset, query_params)

            serialized = ExpenseSerializer(queryset, many=True)
            return Response(serialized.data)
        except:
            raise NotImplementedError('fetching multiple expenses')


    @staticmethod
    @transaction.atomic
    @expect_key_error
    def post(request):
        data = request.data
        serializer = ExpenseCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        expense_id = serializer.create()
        return Response(expense_id, status=status.HTTP_201_CREATED)

    @staticmethod
    @transaction.atomic
    @expect_does_not_exist(Expense)
    def put(request, expense_id=None):
        expense = Expense.objects.get(id=expense_id)
        serializer = ExpenseUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.update(expense)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    @transaction.atomic
    @expect_does_not_exist(Expense)
    def delete(request, expense_id=None):
        Expense.objects.get(id=expense_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ManageCategories(basic_view_manager(Category, CategorySerializer)):

    pagination_class = StandardResultsSetPagination

    @classmethod
    def get(cls, request, business_name=None, category_id=None):
        if category_id:
            category = Category.objects.all().get(id=category_id)
            serialized = CategorySerializer(category)
            return Response(serialized.data)

        query_params = prepare_query_params(request.GET)

        queryset = CategorySerializer.get_default_queryset()

        queryset = cls.apply_filters(queryset, query_params)

        serializer = CategorySerializer(queryset, many=True)
    
        # Check for pagination parameters
        if 'page' in request.GET or 'page_size' in request.GET:
            # Apply pagination
            paginator = cls.pagination_class()
            paginated_queryset = paginator.paginate_queryset(queryset, request)
            serialized = serializer(paginated_queryset, many=True)
            return paginator.get_paginated_response(serialized.data)
        else:
            # No pagination parameters, return all results
            queryset = cls.apply_filters(queryset, query_params)
            serialized = serializer(queryset, many=True)
            return Response(serialized.data)

    @staticmethod
    @transaction.atomic
    @expect_key_error
    def post(request):
        data = request.data
        serializer = CategoryCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        category_id = serializer.create()
        return Response(category_id, status=status.HTTP_201_CREATED)

    @staticmethod
    @transaction.atomic
    @expect_does_not_exist(Expense)
    def put(request, category_id=None):
        category = Category.objects.get(id=category_id)
        serializer = CategoryUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.update(category)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    @transaction.atomic
    @expect_does_not_exist(Expense)
    def delete(request, category_id=None):
        Category.objects.get(id=category_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ManageCompany(basic_view_manager(Company, CompanyWithParentSerializer)):

    pagination_class = StandardResultsSetPagination

    @classmethod
    @expect_does_not_exist(Company)
    def get(cls, request, company_id=None):
        include_roles = request.GET.get(ApiSpecialKeys.INCLUDE_ROLES, False)
        serializer = CompanyWithRolesSerializer if include_roles else CompanyWithParentSerializer

        if company_id:
            company = Company.objects.all().get(id=company_id)
            serialized = serializer(company)
            return Response(serialized.data)

        query_params = prepare_query_params(request.GET)
        queryset = serializer.get_default_queryset()

        if 'page' in request.GET or 'page_size' in request.GET:
            queryset = queryset.order_by('name')

            # Apply pagination
            paginator = cls.pagination_class()
            paginated_queryset = paginator.paginate_queryset(queryset, request)
            serialized = serializer(paginated_queryset, many=True)
            return paginator.get_paginated_response(serialized.data)
        else:
            # No pagination parameters, return all results
            queryset = cls.apply_filters(queryset, query_params)
            serialized = serializer(queryset, many=True)
            return Response(serialized.data)
        
    @staticmethod
    @transaction.atomic
    @expect_key_error
    def post(request, business_name=None): 
        agents_data = request.data.pop(ApiSpecialKeys.AGENTS_DATA, [])
        company_rates_datalist = request.data.pop(ApiSpecialKeys.COMPANY_RATES_DATALIST, [])
        business_name = request.data.pop(ApiSpecialKeys.BUSINESS)
        company_relationships_data = request.data.pop(ApiSpecialKeys.COMPANY_RELATIONSHIPS_DATA, [])

        company_id = create_company(request.data, business_name)

        response = {"company_id": company_id}

        if (agents_data.__len__() > 0):
            agents_ids = handle_agents_bulk(agents_data, company_id, business_name)

            response["agents_ids"] = agents_ids

        if (company_rates_datalist.__len__() > 0):
            company_rates_ids = handle_company_rates_bulk(company_rates_datalist, business_name, company_id)

            response["company_rates_ids"] = company_rates_ids

        if (company_relationships_data.__len__() > 0):
            company_relationships_ids = handle_company_relationships_bulk(company_relationships_data, company_id)

            response["company_relationships_ids"] = company_relationships_ids
        # Respond with complex ids object
        return Response(response, status=status.HTTP_201_CREATED)

    @staticmethod
    @transaction.atomic
    @expect_does_not_exist(Company)
    @expect_does_not_exist(Contact)
    def put(request, company_id=None):
        agents_data = request.data.pop(ApiSpecialKeys.AGENTS_DATA, [])
        company_rates_data = request.data.pop(ApiSpecialKeys.COMPANY_RATES_DATALIST, [])
        business_name = request.data.pop(ApiSpecialKeys.BUSINESS)
        company_relationships_data = request.data.pop(ApiSpecialKeys.COMPANY_RELATIONSHIPS_DATA, [])

        company = Company.objects.get(id=company_id)
        serializer = CompanyUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.update(company, business_name)

        if (agents_data.__len__() > 0):
            handle_agents_bulk(agents_data, company_id, business_name)

        if (company_rates_data.__len__() > 0):
            handle_company_rates_bulk(company_rates_data, business_name, company_id)

        if (company_relationships_data.__len__() > 0):
            handle_company_relationships_bulk(company_relationships_data,  company_id)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    @transaction.atomic
    @expect_does_not_exist(Event)
    def delete(request, company_id=None):
        company = Company.objects.get(id=company_id)
        company.is_deleted = True
        company.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

class ManageCompanyRate(basic_view_manager(CompanyRate, CompanyRateSerializer)):
    @classmethod
    @expect_does_not_exist(CompanyRate)
    def get(cls, request, company_rate_id=None):
        if company_rate_id:
            company_rate = CompanyRate.objects.all().get(id=company_rate_id)
            serialized = CompanyRateSerializer(company_rate)
            return Response(serialized.data)

        query_params = prepare_query_params(request.GET)

        queryset = CompanyRateSerializer.get_default_queryset()

        queryset = cls.apply_filters(queryset, query_params)

        serialized = CompanyRateSerializer(queryset, many=True)
        return Response(serialized.data)

    @staticmethod
    @transaction.atomic
    @expect_key_error
    @expect_does_not_exist(CompanyRate)
    def post(request, business_name=None):
        data = request.data
        data['business'] = business_name
        serializer = CompanyRateCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        company_rate_id = serializer.create()
        return Response(company_rate_id, status=status.HTTP_201_CREATED)
    
    
    @staticmethod
    @transaction.atomic
    @expect_does_not_exist(ServiceArea)
    def put(request, company_rate_id=None):
        company_rate = Company.objects.get(id=company_rate_id)
        serializer = CompanyRateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.update(company_rate)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ManageService(basic_view_manager(Service, ServiceSerializer)):
    @classmethod
    @expect_does_not_exist(Service)
    def get(cls, request, service_id=None):
        if service_id:
            service = Service.objects.all().get(id=service_id)
            serialized = ServiceSerializer(service)
            return Response(serialized.data)

        query_params = prepare_query_params(request.GET)

        queryset = ServiceSerializer.get_default_queryset()

        queryset = cls.apply_filters(queryset, query_params)

        serialized = ServiceSerializer(queryset, many=True)
        return Response(serialized.data)

    @staticmethod
    @transaction.atomic
    @expect_key_error
    @expect_does_not_exist(Business)
    def post(request, business_name=None):
        data = request.data
        data['business'] = business_name
        serializer = ServiceCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        service_id = serializer.create()
        return Response(service_id, status=status.HTTP_201_CREATED)

class ManageServiceArea(basic_view_manager(ServiceArea, ServiceAreaSerializer)):
    @classmethod
    @expect_does_not_exist(ServiceArea)
    def get(cls, request, service_area_id=None):
        if service_area_id:
            service_area = ServiceArea.objects.all().get(id=service_area_id)
            serialized = ServiceAreaSerializer(service_area)
            return Response(serialized.data)

        query_params = prepare_query_params(request.GET)

        queryset = ServiceAreaSerializer.get_default_queryset()

        queryset = cls.apply_filters(queryset, query_params)

        serialized = ServiceAreaSerializer(queryset, many=True)
        return Response(serialized.data)

    @staticmethod
    def post(request):
        data = request.data
        serializer = ServiceAreaCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        service_area_id = serializer.create()
        return Response(service_area_id, status=status.HTTP_201_CREATED)
    

    @staticmethod
    @transaction.atomic
    @expect_does_not_exist(ServiceArea)
    def put(request, service_area_id=None):
        service_area = ServiceArea.objects.get(id=service_area_id)
        serializer = ServiceAreaUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.update(service_area)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @staticmethod
    @transaction.atomic
    @expect_does_not_exist(ServiceArea)
    def delete(request, service_area_id=None):
        ServiceArea.objects.get(id=service_area_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class ManageServiceRoot(basic_view_manager(ServiceRoot, ServiceRootBookingSerializer)):
    @classmethod
    def get(cls, request, business_name=None, service_root_id=None):
        if service_root_id:
            service_root = ServiceRoot.objects.all().get(id=service_root_id)
            serialized = ServiceRootBaseSerializer(service_root)
            return Response(serialized.data)
        query_params = prepare_query_params(request.GET)

        queryset = ServiceRootBookingSerializer.get_default_queryset()

        queryset = cls.apply_filters(queryset, query_params)

        serialized = ServiceRootBookingSerializer(queryset, many=True)
        return Response(serialized.data)
    
    @staticmethod
    def post(request):
        data = request.data
        serializer = ServiceRootCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        service_id = serializer.create()
        return Response(service_id, status=status.HTTP_201_CREATED)
    
    @staticmethod
    @transaction.atomic
    @expect_does_not_exist(Expense)
    def put(request, service_root_id=None):
        service_root = ServiceRoot.objects.get(id=service_root_id)
        serializer = ServiceRootUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.update(service_root)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @staticmethod
    @transaction.atomic
    @expect_does_not_exist(Expense)
    def delete(request, service_root_id=None):
        ServiceRoot.objects.get(id=service_root_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ManageNote(basic_view_manager(Note, NoteSerializer)):
    @classmethod
    def get(cls, request):
        query_params = prepare_query_params(request.GET)

        serializer = NoteSerializer

        queryset = serializer.get_default_queryset()

        queryset = cls.apply_filters(queryset, query_params)

        serialized = serializer(queryset, many=True)
        return Response(serialized.data)

    @staticmethod
    def post(request):
        data = request.data
        user: User = request.user
        data['owner'] = user
        serializer = NoteCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        note_id = serializer.create()
        return Response(note_id, status=status.HTTP_201_CREATED)


class ManageAuthorizations(basic_view_manager(Authorization, AuthorizationBaseSerializer)):
    @staticmethod
    def apply_nested_filters(queryset, nested_params):
        # Only supports filtering by event and its extras

        if nested_params.is_empty():
            return queryset

        event_params, extra_params, _ = filter_params(Event, nested_params.get('events', {}))
        if not event_params.is_empty():
            queryset = queryset.filter(**event_params.to_dict('events__'))

        if not extra_params.is_empty():
            queryset = queryset.filter_by_extra_query_params(extra_params, related_prefix='events__')

        return queryset

    @classmethod
    @expect_does_not_exist(Authorization)
    def get(cls, request, authorization_id=None):
        if authorization_id:
            authorization = AuthorizationSerializer.get_default_queryset().get(id=authorization_id)
            serialized = AuthorizationSerializer(authorization)
            return Response(serialized.data)

        query_params = prepare_query_params(request.GET)

        queryset = AuthorizationSerializer.get_default_queryset()

        queryset = cls.apply_filters(queryset, query_params)

        serialized = AuthorizationSerializer(queryset, many=True)
        return Response(serialized.data)

    @staticmethod
    @transaction.atomic
    @expect_key_error
    def post(request):
        data = request.data
        events_query = data.pop(ApiSpecialKeys.EVENTS_QUERY, None)

        if events_query:
            # If events query is present, fetch from a query which events to relate to the authorization
            #  using the same method ManageEvents uses
            query_params = prepare_query_params(events_query)
            queryset = EventSerializer.get_default_queryset()
            queryset = ManageEvents.apply_filters(queryset, query_params)

            data['events'] = queryset.values_list('id', flat=True)

        serializer = AuthorizationCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        authorization_id = serializer.create()
        return Response(authorization_id, status=status.HTTP_201_CREATED)

    @staticmethod
    @transaction.atomic
    @expect_does_not_exist(Authorization)
    def put(request, authorization_id=None):
        authorization = Authorization.objects.get(id=authorization_id)
        serializer = AuthorizationUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.update(authorization)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    @transaction.atomic
    @expect_does_not_exist(Authorization)
    def delete(request, authorization_id=None):
        Authorization.objects.get(id=authorization_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class ManageLanguages(basic_view_manager(Language, LanguageSerializer)):
    @classmethod
    def get(cls, request, language_id=None):
        if language_id:
            language = LanguageSerializer.get_default_queryset().get(id=language_id)
            serialized = LanguageSerializer(language)
            return Response(serialized.data)

        query_params = prepare_query_params(request.GET)

        queryset = LanguageSerializer.get_default_queryset()

        queryset = cls.apply_filters(queryset, query_params)

        serialized = LanguageSerializer(queryset, many=True)
        return Response(serialized.data)

    @staticmethod
    @transaction.atomic
    @expect_key_error
    def post(request):
        data = request.data
        serializer = LanguageCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        language_id = serializer.create()
        return Response(language_id, status=status.HTTP_201_CREATED)

    @staticmethod
    @transaction.atomic
    @expect_does_not_exist(Language)
    def put(request, language_id=None):
        language = Language.objects.get(id=language_id)
        serializer = LanguageUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.update(language)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    @transaction.atomic
    @expect_does_not_exist(Language)
    def delete(request, language_id=None):
        Language.objects.get(id=language_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ManageNotifications(basic_view_manager(Notification, NotificationSerializer)):
    @classmethod
    @expect_does_not_exist(Notification)
    def get(cls, request, notification_id=None):
        if notification_id:
            notification = NotificationSerializer.get_default_queryset().get(id=notification_id)
            serialized = NotificationSerializer(notification)
            return Response(serialized.data)

        query_params = prepare_query_params(request.GET)
        queryset = NotificationSerializer.get_default_queryset()
        queryset = cls.apply_filters(queryset, query_params)
        serialized = NotificationSerializer(queryset, many=True)
        return Response(serialized.data)

    @staticmethod
    @transaction.atomic
    @expect_key_error
    def post(request):
        data = request.data
        payload = data.get('payload')
        template = data.get('template')

        serializer = NotificationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Only fax supported
        render_data = build_from_template(template, payload)

        if not 'fax_number' in data:
            raise BadRequestException('Fax number missing')

        render_data['fax_number'] = data['fax_number']
        render_data['fax_name'] = data.get('fax_name', None)
        render_data['addressee'] = render_data['fax_name']

        notification_id = serializer.create(render_data=render_data)

        return Response(notification_id, status=status.HTTP_202_ACCEPTED)


class ManageOffers(basic_view_manager(Offer, OfferSerializer)):
    @classmethod
    def get(cls, request):
        query_params = prepare_query_params(request.GET)

        serializer = OfferSerializer

        queryset = serializer.get_default_queryset()

        queryset = cls.apply_filters(queryset, query_params)

        serialized = serializer(queryset, many=True)
        return Response(serialized.data)
    
    @staticmethod
    @transaction.atomic
    def post(request, business_name=None):
        data = request.data
        serializer = OfferCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        offer_id = serializer.create(business_name)
        return Response(offer_id, status=status.HTTP_201_CREATED)
    
    @staticmethod
    @transaction.atomic
    @expect_does_not_exist(Offer)
    def put(request, offer_id=None):
        business_name = request.data.pop(ApiSpecialKeys.BUSINESS)
        offer = Offer.objects.get(id=offer_id)
        serializer = OfferUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.update(offer, business_name)
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['POST'])
@transaction.atomic
def send_email(request):
    subject = request.data['subject']
    message = request.data['body']
    from_email = settings.EMAIL_HOST_USER
    recipient = [request.data['recipient']]
    if subject and message and from_email:
        try:
            msg = EmailMultiAlternatives(subject, message, from_email, to=recipient)
            msg.attach_alternative(message, "text/html")
            msg.send()
        except BadHeaderError:
            return JsonResponse({'error': 'Invalid header found.'}, status=400)
        return HttpResponse(200)
    else:
        # In reality we'd use a form class
        # to get proper validation errors.
        return JsonResponse({'error': 'Make sure all fields are entered and valid.'}, status=400)

class ManageCompanyRelationships(basic_view_manager(CompanyRelationship, CompanyRelationshipSerializer)):
    @classmethod
    @expect_does_not_exist(CompanyRelationship)
    def get(cls, request, company_relationship_id=None):
        if company_relationship_id:
            company_relationship = CompanyRelationship.objects.all().get(id=company_relationship_id)
            serialized = CompanyRelationshipSerializer(company_relationship)
            return Response(serialized.data)

        query_params = prepare_query_params(request.GET)

        queryset = CompanyRelationshipSerializer.get_default_queryset()

        queryset = cls.apply_filters(queryset, query_params)

        serialized = CompanyRelationshipSerializer(queryset, many=True)
        return Response(serialized.data)

    @staticmethod
    def post(request):
        data = request.data
        serializer = CompanyRelationshipCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        company_relationship_id = serializer.create()
        return Response(company_relationship_id, status=status.HTTP_201_CREATED)


    @staticmethod
    @transaction.atomic
    @expect_does_not_exist(CompanyRelationship)
    def put(request, company_relationship_id=None):
        company_relationship = CompanyRelationship.objects.get(id=company_relationship_id)
        serializer = CompanyRelationshipUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.update(company_relationship)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    @transaction.atomic
    @expect_does_not_exist(CompanyRelationship)
    def delete(request, company_relationship_id=None):
        CompanyRelationship.objects.get(id=company_relationship_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)