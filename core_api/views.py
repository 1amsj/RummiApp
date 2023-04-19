from typing import Type, Union

from django.db import models, transaction
from django.db.models import Q, QuerySet
from rest_framework import generics, serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from core_api.constants import INCLUDE_BOOKING_KEY, INCLUDE_EVENTS_KEY
from core_api.decorators import expect_does_not_exist, expect_key_error, expect_not_implemented
from core_api.serializers import CustomTokenObtainPairSerializer, RegisterSerializer
from core_api.services import prepare_query_params
from core_backend.datastructures import QueryParams
from core_backend.models import Affiliation, Agent, Booking, Business, Category, Company, Contact, Event, Expense, \
    ExtraQuerySet, Note, \
    Operator, \
    Payer, \
    Provider, \
    Recipient, \
    Requester, Service, ServiceRoot, User
from core_backend.serializers import AffiliationCreateSerializer, AffiliationSerializer, AgentCreateSerializer, \
    AgentSerializer, BookingCreateSerializer, BookingNoEventsSerializer, BookingSerializer, CategoryCreateSerializer, \
    CategorySerializer, CompanyCreateSerializer, CompanySerializer, CompanyUpdateSerializer, EventCreateSerializer, \
    EventNoBookingSerializer, EventSerializer, ExpenseCreateSerializer, ExpenseSerializer, NoteCreateSerializer, NoteSerializer, OperatorSerializer, \
    PayerCreateSerializer, PayerSerializer, ProviderSerializer, RecipientCreateSerializer, RecipientSerializer, \
    RequesterSerializer, ServiceCreateSerializer, ServiceRootNoBookingSerializer, ServiceSerializer, \
    UserCreateSerializer, UserSerializer, \
    UserUpdateSerializer
from core_backend.services import filter_params, is_extendable
from core_backend.settings import VERSION_FILE_DIR


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
    with open(VERSION_FILE_DIR, 'r') as f:
        return Response(f.readline().strip('\n'))


@api_view(['GET'])
@permission_classes([IsAuthenticated, can_manage_model_basic_permissions(Business._meta.model_name)])
def search_bookings(request):
    # This view was made for the interpretation business alone and is not meant to be used in a generic application
    # without making the proper modifications
    person_query = Q(is_deleted=False)
    if first_name := request.GET.get('first_name'):
        person_query = person_query and Q(first_name__icontains=first_name)
    if last_name := request.GET.get('last_name'):
        person_query = person_query and Q(last_name__icontains=last_name)

    eligible_users = User.objects.filter(person_query)
    eligible_services = Service.objects.filter(
        is_deleted=False,
        provider__user__in=eligible_users,
    )
    eligible_affiliations = Affiliation.objects.filter(
        is_deleted=False,
        recipient__user__in=eligible_users,
    )
    eligible_events = Event.objects.filter(
        is_deleted=False,
        affiliates__in=eligible_affiliations,
    )

    queryset = Booking.objects.filter(
        is_deleted=False,
        services__in=eligible_services,
        events__in=eligible_events,
    )

    if date := request.GET.get('date'):
        queryset = queryset.filter_by_extra(
            date_of_injury__contains=date,
        )

    queryset = queryset.distinct('id')

    serialized = BookingSerializer(queryset, many=True)
    return Response(serialized.data)


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
                queryset = queryset.filter_by_extra(**extra_params.to_dict())

            queryset = cls.apply_nested_filters(queryset, nested_params)

            return queryset

        @classmethod
        def filter_related_per_deleted(cls, queryset: QuerySet[model]):
            return queryset.filter(
                user__in=User.objects.not_deleted(),
            )

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

    @staticmethod
    @transaction.atomic
    @expect_does_not_exist(User)
    @expect_does_not_exist(Contact)
    def put(request, user_id=None):
        user = User.objects.get(id=user_id)
        serializer = UserUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.update(user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    @transaction.atomic
    @expect_does_not_exist(Event)
    def delete(request, user_id=None):
        user = User.objects.get(id=user_id)
        user.is_deleted = True
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ManageAgents(user_subtype_view_manager(Agent, AgentSerializer)):

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
            serialized = AgentSerializer(agent)
            return Response(serialized.data)
        
        query_params = prepare_query_params(request.GET)

        queryset = AgentSerializer.get_default_queryset()

        queryset = cls.apply_filters(queryset, query_params)

        serialized = AgentSerializer(queryset, many=True)
        return Response(serialized.data)

class ManageOperators(user_subtype_view_manager(Operator, OperatorSerializer)):
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
            provider = Provider.objects.all().not_deleted('user').get(id=provider_id)
            serialized = ProviderSerializer(provider)
            return Response(serialized.data)

        query_params = prepare_query_params(request.GET)

        queryset = ProviderSerializer.get_default_queryset()

        queryset = cls.apply_filters(queryset, query_params)

        serialized = ProviderSerializer(queryset, many=True)
        return Response(serialized.data)


class ManageRecipients(user_subtype_view_manager(Recipient, RecipientSerializer)):
   
    @staticmethod
    @transaction.atomic
    @expect_key_error
    @expect_does_not_exist(Recipient)
    def post(request, business_name=None):
        serializer = RecipientCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        recipient = serializer.create(business_name)
        return Response(recipient.id, status=status.HTTP_201_CREATED)

    @classmethod
    def get(cls, request, buisiness_name=None, recipient_id=None):
        if recipient_id:
            recipient = Recipient.objects.all().not_deleted('user').get(id=recipient_id)
            serialized = RecipientSerializer(recipient)
            return Response(serialized.data)
        
        query_params = prepare_query_params(request.GET)

        queryset = RecipientSerializer.get_default_queryset()

        queryset = cls.apply_filters(queryset, query_params)

        serialized = RecipientSerializer(queryset, many=True)
        return Response(serialized.data)

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

        include_events = request.GET.get(INCLUDE_EVENTS_KEY, False)
        query_params = prepare_query_params(request.GET)

        serializer = BookingSerializer if include_events else BookingNoEventsSerializer

        queryset = serializer.get_default_queryset()

        queryset = cls.apply_filters(queryset, query_params)

        serialized = serializer(queryset, many=True)
        return Response(serialized.data)

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

    @staticmethod
    @transaction.atomic
    @expect_does_not_exist(Booking)
    def put(request, booking_id=None):
        booking = Booking.objects.get(id=booking_id)
        business = request.data.pop('business')
        serializer = BookingCreateSerializer(data=request.data)
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


class ManageEvents(basic_view_manager(Event, EventSerializer)):
    @classmethod
    @expect_does_not_exist(Event)
    def get(cls, request, business_name=None, event_id=None):
        if event_id:
            event = Event.objects.all().not_deleted('booking').get(id=event_id)
            serialized = EventSerializer(event)
            return Response(serialized.data)
        
        include_booking = request.GET.get(INCLUDE_BOOKING_KEY, False)
        query_params = prepare_query_params(request.GET)
        
        serializer = EventSerializer if include_booking else EventNoBookingSerializer

        queryset = serializer.get_default_queryset()

        if business_name:
            queryset = queryset.filter(booking__business__name=business_name)
        
        queryset = cls.apply_filters(queryset, query_params)
        
        serialized = serializer(queryset, many=True)
        return Response(serialized.data)

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

    @staticmethod
    @transaction.atomic
    @expect_does_not_exist(Event)
    def put(request, event_id=None):
        event = Event.objects.get(id=event_id)
        serializer = EventCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.update(event)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    @transaction.atomic
    @expect_does_not_exist(Event)
    def delete(request, event_id=None):
        event = Event.objects.get(id=event_id)
        event.is_deleted = True
        event.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


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
        serializer = ExpenseCreateSerializer(data=request.data)
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
    @classmethod
    def get(cls, request, business_name=None, category_id=None):
        if category_id:
            category = Category.objects.all().get(id=category_id)
            serialized = CategorySerializer(category)
            return Response(serialized.data)
        
        query_params = prepare_query_params(request.GET)

        queryset = CategorySerializer.get_default_queryset()

        queryset = cls.apply_filters(queryset, query_params)

        serialized = CategorySerializer(queryset, many=True)
        return super().get(request), Response(serialized.data)

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
        serializer = CategoryCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.update(category)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    @transaction.atomic
    @expect_does_not_exist(Expense)
    def delete(request, category_id=None):
        Category.objects.get(id=category_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ManageCompany(basic_view_manager(Company, CompanySerializer)):
    @classmethod
    @expect_does_not_exist(Company)
    def get(cls, request, business_name=None, company_id=None):
        if company_id:
            company = Company.objects.all().not_deleted('business').get(id=company_id)
            serialized = CompanySerializer(company)
            return Response(serialized.data)
        
        query_params = prepare_query_params(request.GET)
        
        queryset = CompanySerializer.get_default_queryset()
        
        queryset = cls.apply_filters(queryset, query_params)
        
        serialized = CompanySerializer(queryset, many=True)
        return Response(serialized.data)

    @staticmethod
    @transaction.atomic
    @expect_key_error
    def post(request):
        serializer = CompanyCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        company_id = serializer.create()
        return Response(company_id, status=status.HTTP_201_CREATED)

    @staticmethod
    @transaction.atomic
    @expect_does_not_exist(Company)
    @expect_does_not_exist(Contact)
    def put(request, company_id=None):
        company = Company.objects.get(id=company_id)
        serializer = CompanyUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.update(company)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    @transaction.atomic
    @expect_does_not_exist(Event)
    def delete(request, company_id=None):
        company = Company.objects.get(id=company_id)
        company.is_deleted = True
        company.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


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


class ManageServiceRoot(basic_view_manager(ServiceRoot, ServiceRootNoBookingSerializer)):
    @classmethod
    def get(cls, request):
        query_params = prepare_query_params(request.GET)

        queryset = ServiceRootNoBookingSerializer.get_default_queryset()

        queryset = cls.apply_filters(queryset, query_params)

        serialized = ServiceRootNoBookingSerializer(queryset, many=True)
        return Response(serialized.data)


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
    