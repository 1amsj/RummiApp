from django.db import transaction
from rest_framework.exceptions import ValidationError

from core_api.constants import ApiSpecialKeys
from core_api.exceptions import BusinessNotProvidedException
from core_backend.serializers import AffiliationCreateSerializer, AgentCreateSerializer, ProviderUpdateSerializer, RecipientCreateSerializer, \
    RecipientUpdateSerializer, \
    UserCreateSerializer, UserUpdateSerializer, RequesterCreateSerializer


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
