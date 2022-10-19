from typing import Type

from django.db import models, transaction
from django.db.models import QuerySet
from rest_framework import generics, serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from core_api.constants import NO_EXACT_MATCH_SUFFIX
from core_api.decorators import expect_does_not_exist, expect_key_error
from core_api.exceptions import BadRequestException
from core_api.serializers import CustomTokenObtainPairSerializer, RegisterSerializer
from core_api.services import contact_get_or_create, location_get_or_create, prepare_query_params
from core_backend.exceptions import ModelNotExtendableException
from core_backend.models import Agent, Booking, Company, Contact, Event, Location, Operator, Payer, Provider, Recipient, \
    Requester, Service, User
from core_backend.serializers import AgentSerializer, CompanySerializer, OperatorSerializer, PayerSerializer, \
    ProviderServiceSerializer, RecipientSerializer, RequesterSerializer, UserSerializer
from core_backend.services import filter_attrs, filter_queryset, iter_base_attrs, iter_extra_attrs, manage_extra_attrs


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
        def apply_filters(queryset: QuerySet[model], params: dict) -> QuerySet[model]:
            return filter_queryset(model, queryset, params)

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
        def apply_filters(queryset, params):
            user_params, remaining_params = filter_attrs(User, params)
            queryset = super(ManageUserSubtypeModel, ManageUserSubtypeModel).apply_filters(queryset, remaining_params)
            user_params = {
                ('user__' + k): v
                for (k, v) in user_params.items()
            }
            if user_params:
                queryset = queryset.filter(**user_params)
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


ManageAgents = user_subtype_view_manager(Agent, AgentSerializer)

ManageOperators = user_subtype_view_manager(Operator, OperatorSerializer)

ManagePayers = user_subtype_view_manager(Payer, PayerSerializer)


class ManageProviders(user_subtype_view_manager(Provider, ProviderServiceSerializer)):
    @staticmethod
    def apply_filters(queryset, params):
        # TODO redo when making DSL query for GET
        provider_params = {}
        service_params = {}
        for (k, v) in params.items():
            field = k.split('.')[-1]
            (service_params if 'services.' in k else provider_params)[field] = v

        queryset = super(ManageProviders, ManageProviders).apply_filters(queryset, provider_params)

        service_base_params = {
            F'services__{k}': v
            for (k, v) in iter_base_attrs(Service, service_params)
        }
        if service_base_params:
            queryset = queryset.filter(**service_base_params)

        try:
            for (k, v) in iter_extra_attrs(Service, service_params):
                split_k = k.split('__')
                query_value = 'services__extra__value' + NO_EXACT_MATCH_SUFFIX if len(split_k) > 1 else ''
                queryset = queryset.filter(**{"services__extra__key": split_k[0], query_value: v})

        except ModelNotExtendableException:
            pass

        return queryset

    @classmethod
    @expect_does_not_exist(Provider)
    def get(cls, request, business=None, provider_id=None):
        if provider_id:
            serialized = ProviderServiceSerializer(Provider.objects.get(id=provider_id))
            return Response(serialized.data)

        query_params = prepare_query_params(request.GET)
        queryset = Provider.objects.all().prefetch_related('services', 'services__extra')
        queryset = cls.apply_filters(queryset, query_params)
        if business:
            queryset = queryset.filter(extra__business__name=business)
        serialized = ProviderServiceSerializer(queryset, many=True)

        return Response(serialized.data)


ManageRecipients = user_subtype_view_manager(Recipient, RecipientSerializer)

ManageRequesters = user_subtype_view_manager(Requester, RequesterSerializer)


class ManageCompany(basic_view_manager(Company, CompanySerializer)):
    @staticmethod
    @transaction.atomic
    @expect_key_error
    @expect_does_not_exist(Contact)
    @expect_does_not_exist(Location)
    def post(request):
        company = Company.objects.create(
            name=request.data['name'],
            type=request.data['type'],
            send_method=request.data['send_method'],
            on_hold=request.data.get('on_hold', False),
            contact=contact_get_or_create(request.data['contact']),
            location=location_get_or_create(request.data.get('location')),
        )
        return Response(company.id, status=status.HTTP_201_CREATED)


class ManageBooking(APIView):
    class CanManageBooking(BasePermission):
        message = 'You do not have permission to perform this operation'

        def has_permission(self, request, view):
            method = request.method
            user = request.user
            return (method == 'GET' and user.has_perm('core_api.view_booking')) \
                or (method == 'POST' and user.has_perm('core_api.add_booking')) \
                or (method == 'PUT' and user.has_perm('core_api.change_booking')) \
                or (method == 'DELETE' and user.has_perm('core_api.delete_booking'))

    permission_classes = [IsAuthenticated, CanManageBooking]

    @staticmethod
    def get(request):
        ...

    @staticmethod
    @transaction.atomic
    @expect_key_error
    def post(request, business):
        user: User = request.user

        operator_ids = request.data.get('operators', [user.as_operator.id] if user.is_operator else None)
        service_ids = request.data['services']

        booking = Booking.objects.create()
        booking.operators.add(*operator_ids)
        booking.services.add(*service_ids)
        manage_extra_attrs(business, booking, request.data)

        events = request.data.get('events', [])
        for e in events:
            agent_ids = e.get('agents')
            payer_id = e['payer']
            recipient_ids = e.get('recipients')
            requester_id = e.get('requester', user.as_requester.id if user.is_requester else None)
            location_id = e.get('location')
            meeting_url = e.get('meeting_url')
            start_at = e['start_at']
            end_at = e['end_at']
            observations = e.get('observations', '')

            if not location_id and not meeting_url:
                raise BadRequestException('Either location or meeting_url must be specified')

            event = Event.objects.create(
                booking=booking,
                payer_id=payer_id,
                requester_id=requester_id,
                location_id=location_id,
                meeting_url=meeting_url,
                start_at=start_at,
                end_at=end_at,
                observations=observations,
            )
            if agent_ids:
                event.agents.add(*agent_ids)
            if recipient_ids:
                event.recipients.add(*recipient_ids)

        return Response(status=status.HTTP_201_CREATED)

    @staticmethod
    @transaction.atomic
    def put(request):
        ...

    @staticmethod
    @transaction.atomic
    def delete(request):
        ...
