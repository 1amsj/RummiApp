from django.db import transaction
from rest_framework.exceptions import ValidationError

from core_api.constants import ApiSpecialKeys
from core_api.exceptions import BusinessNotProvidedException
from core_backend.models import User
from core_api.exceptions import BadRequestException, BusinessNotProvidedException
from core_backend.models import Event
from core_backend.serializers.serializers_create import AffiliationCreateSerializer, AgentCreateSerializer, BookingCreateSerializer, \
    EventCreateSerializer, PayerCreateSerializer, \
    RecipientCreateSerializer, RequesterCreateSerializer, UserCreateSerializer
from core_backend.serializers.serializers_update import EventUpdateSerializer, ProviderUpdateSerializer, \
    RecipientUpdateSerializer, \
    UserUpdateSerializer


# Creation
@transaction.atomic
def create_user(data):
    serializer = UserCreateSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    user = serializer.create()
    return user.id


@transaction.atomic
def create_agent_wrap(data, user_id, business_name):
    # Handle recipient role creation
    try:
        data['user'] = user_id
        serializer = AgentCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        agent = serializer.create(business_name)

    except ValidationError as exc:
        # Wrap errors
        raise ValidationError({
            ApiSpecialKeys.AGENT_DATA: exc.detail,
        })

    return agent.id


@transaction.atomic
def create_payer_wrap(data, user_id):
    # Handle payer role creation
    try:
        data['user'] = user_id
        serializer = PayerCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        payer = serializer.create()

    except ValidationError as exc:
        # Wrap errors
        raise ValidationError({
            ApiSpecialKeys.PAYER_DATA: exc.detail,
        })

    return payer.id


@transaction.atomic
def create_recipient_wrap(data, business_name, user_id):
    if not business_name:
        raise BusinessNotProvidedException

    # Handle recipient role creation
    try:
        data['user'] = user_id
        serializer = RecipientCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        recipient = serializer.create(business_name)

    except ValidationError as exc:
        # Wrap errors
        raise ValidationError({
            ApiSpecialKeys.RECIPIENT_DATA: exc.detail,
        })

    return recipient.id


@transaction.atomic
def create_requester_wrap(data, business_name, user_id):
    if not business_name:
        raise BusinessNotProvidedException
    try:
        data['user'] = user_id
        serializer = RequesterCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        requester = serializer.create(business_name)

    except ValidationError as exc:
        raise ValidationError({
            ApiSpecialKeys.REQUESTER_DATA: exc.detail,
        })

    return requester.id


@transaction.atomic
def create_affiliations_wrap(datalist, business_name, recipient_id):
    if not business_name:
        raise BusinessNotProvidedException

    # Handle affiliations creation
    affiliation_ids = []
    affiliation_errors = []
    for affiliation_data in datalist:
        try:
            affiliation_data['recipient'] = recipient_id
            serializer = AffiliationCreateSerializer(data=affiliation_data)
            serializer.is_valid(raise_exception=True)
            affiliation = serializer.create(business_name)
            affiliation_ids.append(affiliation.id)

        except ValidationError as exc:
            affiliation_errors.append(exc.detail)

    if affiliation_errors:
        raise ValidationError({
            ApiSpecialKeys.AFFILIATION_DATALIST: affiliation_errors
        })

    return affiliation_ids


@transaction.atomic
def create_booking(data, business_name, user):
    data['business'] = business_name

    if not data.get('operators'):
        user: User = user
        data['operators'] = [user.as_operator.id] if user.is_operator else None

    serializer = BookingCreateSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    booking_id = serializer.create()
    return booking_id;


@transaction.atomic
def create_events_wrap(datalist, business, booking_id):
    # Handle events creation
    event_ids = []
    event_errors = []
    for event_data in datalist:
        try:
            event_data['booking'] = booking_id
            serializer = EventCreateSerializer(data=event_data)
            serializer.is_valid(raise_exception=True)
            event_id = serializer.create(business)
            event_ids.append(event_id)

        except ValidationError as exc:
            event_errors.append(exc.detail)

    if event_errors:
        raise ValidationError({
            ApiSpecialKeys.EVENT_DATALIST: event_errors
        })

    return event_ids


def create_event(data, business_name, requester_id):
    if not data.get('requester'):
        data['requester'] = requester_id

    serializer = EventCreateSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    return serializer.create(business_name)


# Update
@transaction.atomic
def update_user(data, user_instance):
    serializer = UserUpdateSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    serializer.update(user_instance)


@transaction.atomic
def update_provider_wrap(data, business_name, user_id, provider_instance):
    if not business_name:
        raise BusinessNotProvidedException

    # Handle provider role update
    try:
        data['user'] = user_id
        serializer = ProviderUpdateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.update(provider_instance, business_name)

    except ValidationError as exc:
        # Wrap errors
        raise ValidationError({
            ApiSpecialKeys.PROVIDER_DATA: exc.detail,
        })


@transaction.atomic
def update_recipient_wrap(data, business_name, user_id, recipient_instance):
    if not business_name:
        raise BusinessNotProvidedException

    # Handle recipient role update
    try:
        data['user'] = user_id
        serializer = RecipientUpdateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.update(recipient_instance, business_name)

    except ValidationError as exc:
        # Wrap errors
        raise ValidationError({
            ApiSpecialKeys.RECIPIENT_DATA: exc.detail,
        })


@transaction.atomic
def update_event_wrap(data, business_name, event_instance):
    if not business_name:
        raise BusinessNotProvidedException
    
    try:
        serializer = EventUpdateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.update(event_instance, business_name)

    except ValidationError as exc:
        # Wrap errors
        raise ValidationError({
            ApiSpecialKeys.EVENT_DATALIST: exc.detail,
        })


# Bulk
@transaction.atomic
def handle_events_bulk(datalist: list, business_name, requester_id):
    """
    Create, update or delete the events in bulk, depending on whether the payload includes an ID or not
    """
    # TODO It is noteworthy that currently this is not a true bulk operation.
    #  Also, events get created event even if an error was found before,
    #  this might make the transaction rollback expensive.

    event_ids = []
    event_errors = []
    error_found = False

    for data in datalist:
        event_id = data.pop('id', None)
        deleted_flag = data.pop(ApiSpecialKeys.DELETED_FLAG, False)

        if not event_id and deleted_flag:
            raise BadRequestException('Event flagged as deleted but no ID provided')

        try:
            if not event_id:
                event_id = create_event(
                    data,
                    business_name,
                    requester_id
                )
            elif not deleted_flag:
                update_event_wrap(
                    data,
                    business_name,
                    event_instance=Event.objects.get(id=event_id)
                )
            else:
                Event.objects.get(id=event_id).delete()

            # Append empty error to object so that the indexes of the errors correspond to the indexes of the data
            event_errors.append({})
            event_ids.append(event_id)

        except ValidationError as exc:
            error_found = True
            event_errors.append(exc.detail)

    if error_found:
        raise ValidationError(event_errors)

    return event_ids
