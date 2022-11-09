from typing import Type, Union

from django.db import models, transaction
from django.db.models import QuerySet
from rest_framework import generics, serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from core_api.decorators import expect_does_not_exist, expect_key_error
from core_api.serializers import CustomTokenObtainPairSerializer, RegisterSerializer
from core_api.services import prepare_query_params
from core_backend.datastructures import QueryParams
from core_backend.models import Affiliation, Agent, Booking, Business, Company, Event, ExtraQuerySet, Operator, Payer, \
    Provider, \
    Recipient, \
    Requester, Service, User
from core_backend.serializers import AffiliationSerializer, AgentSerializer, BookingCreateSerializer, BookingSerializer, \
    CompanyCreateSerializer, \
    CompanySerializer, \
    EventCreateSerializer, EventSerializer, OperatorSerializer, \
    PayerSerializer, \
    ProviderSerializer, ProviderServiceSerializer, RecipientSerializer, RequesterSerializer, ServiceCreateSerializer, \
    ServiceSerializer, UserCreateSerializer, UserSerializer
from core_backend.services import filter_params, is_extendable


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer


class UserViewSet(generics.ListAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserSerializer


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
    users = User.objects.all()

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


def can_manage_model_basic_permissions(model_name: str) -> Type[BasePermission]:
    class CanManageModel(BasePermission):
        message = 'You do not have permission to perform this operation'

        def has_permission(self, request, view):
            method = request.method
            user = request.user
            return (method == 'GET' and user.has_perm(F'core_api.view_{model_name}')) \
                or (method == 'POST' and user.has_perm(F'core_api.add_{model_name}')) \
                or (method == 'PUT' and user.has_perm(F'core_api.change_{model_name}')) \
                or (method == 'DELETE' and user.has_perm(F'core_api.delete_{model_name}'))

    return CanManageModel


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
                queryset = queryset.filter_by_extra(**extra_params.to_dict())

            queryset = cls.apply_nested_filters(queryset, nested_params)

            return queryset

        @classmethod
        def get(cls, request):
            query_params = prepare_query_params(request.GET)
            queryset = cls.apply_filters(model.objects.all(), query_params)
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
                queryset = queryset.filter_by_extra(**extra_params.to_dict())

            queryset = cls.apply_nested_filters(queryset, nested_params)

            return queryset

    return ManageUserSubtypeModel


class ManageUsers(basic_view_manager(User, UserSerializer)):
    @classmethod
    @expect_does_not_exist(User)
    def get(cls, request, user_id=None):
        if user_id:
            serialized = UserSerializer(User.objects.get(id=user_id))
            return Response(serialized.data)

        return super(ManageUsers, ManageUsers).get(request)

    @staticmethod
    @transaction.atomic
    def post(request):
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.create()
        return Response(user.id, status=status.HTTP_201_CREATED)


ManageAgents = user_subtype_view_manager(Agent, AgentSerializer)

ManageOperators = user_subtype_view_manager(Operator, OperatorSerializer)

ManagePayers = user_subtype_view_manager(Payer, PayerSerializer)


class ManageProviders(user_subtype_view_manager(Provider, ProviderServiceSerializer)):
    @staticmethod
    def apply_nested_filters(queryset, nested_params):
        if nested_params.is_empty():
            return queryset

        service_params, extra_params, _ = filter_params(Service, nested_params.get('services', {}))
        if not service_params.is_empty():
            queryset = queryset.filter(**service_params.to_dict('services__'))

        if not extra_params.is_empty():
            queryset = queryset.filter_by_extra(related_prefix='services__', **extra_params.to_dict())

        return queryset

    @classmethod
    @expect_does_not_exist(Provider)
    def get(cls, request, business_name=None, provider_id=None):
        if provider_id:
            serialized = ProviderServiceSerializer(Provider.objects.get(id=provider_id))
            return Response(serialized.data)

        query_params = prepare_query_params(request.GET)
        queryset = Provider.objects.all().prefetch_related('services', 'services__extra')
        queryset = cls.apply_filters(queryset, query_params)
        if business_name:
            queryset = queryset.filter(extra__business__name=business_name)
        serialized = ProviderSerializer(queryset, many=True)
        return Response(serialized.data)


ManageRecipients = user_subtype_view_manager(Recipient, RecipientSerializer)

ManageRequesters = user_subtype_view_manager(Requester, RequesterSerializer)


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
                queryset = queryset.filter_by_extra(**extra_params.to_dict('recipient__'))

        company_params = nested_params.pop('company')
        if company_params:
            base_params, extra_params, _ = filter_params(Company, company_params)

            if not base_params.is_empty():
                queryset = queryset.filter(**base_params.to_dict('company__'))

            if is_extendable(Company) and not extra_params.is_empty():
                queryset = queryset.filter_by_extra(**extra_params.to_dict('company__'))

        return queryset


class ManageBooking(basic_view_manager(Booking, BookingSerializer)):
    @staticmethod
    @transaction.atomic
    @expect_key_error
    def post(request, business_name):
        data = request.data
        data['business'] = business_name
        if not data.get('operators'):
            user: User = request.user
            data['operators'] = [user.as_operator.id] if user.is_operator else None

        serializer = BookingCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        booking_id = serializer.create()
        return Response(booking_id, status=status.HTTP_201_CREATED)


class ManageEvents(basic_view_manager(Event, EventSerializer)):
    @staticmethod
    @transaction.atomic
    @expect_key_error
    def post(request):
        data = request.data
        if not data.get('requester'):
            user: User = request.user
            data['requester'] = user.as_requester.id if user.is_requester else None

        serializer = EventCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        event_id = serializer.create()
        return Response(event_id, status=status.HTTP_201_CREATED)


class ManageCompany(basic_view_manager(Company, CompanySerializer)):
    @staticmethod
    @transaction.atomic
    @expect_key_error
    def post(request):
        serializer = CompanyCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        company_id = serializer.create()
        return Response(company_id, status=status.HTTP_201_CREATED)


class ManageService(basic_view_manager(Service, ServiceSerializer)):
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
