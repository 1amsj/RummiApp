from django.db import transaction
from rest_framework.exceptions import ValidationError

from core_api.constants import ApiSpecialKeys
from core_api.exceptions import BadRequestException, BusinessNotProvidedException
from core_backend.models import Agent, Booking, CompanyRelationship, Event, Rate, Report, Service, ServiceArea
from core_backend.models import User
from core_backend.serializers.serializers_create import AffiliationCreateSerializer, AgentCreateSerializer, \
    BookingCreateSerializer, CompanyCreateSerializer, CompanyRelationshipCreateSerializer, \
    EventCreateSerializer, OfferCreateSerializer, OperatorCreateSerializer, PayerCreateSerializer, \
    ProviderCreateSerializer, RateCreateSerializer, RecipientCreateSerializer, ReportCreateSerializer, RequesterCreateSerializer, \
    ServiceCreateSerializer, ServiceAreaCreateSerializer, UserCreateSerializer
from core_backend.serializers.serializers_update import AgentUpdateSerializer, CompanyRelationshipUpdateSerializer, EventUpdateSerializer, ProviderUpdateSerializer, RateUpdateSerializer, \
    RecipientUpdateSerializer, ReportUpdateSerializer, \
    ServiceUpdateSerializer, ServiceAreaUpdateSerializer, UserUpdateSerializer


# Creation
@transaction.atomic
def create_user(data):
    serializer = UserCreateSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    user = serializer.create()
    return user.id

@transaction.atomic
def create_rate_wrap(data, business_name):
    try:
        serializer = RateCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        rate = serializer.create(business_name)
    except ValidationError as exc:
        # Wrap errors
        raise ValidationError({
            ApiSpecialKeys.RATES_DATALIST: exc.detail,
        })
    return rate


@transaction.atomic
def create_agent_wrap(data, business_name, user_id,):
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
def create_operator_wrap(data, user_id):
    # Handle operator role creation
    try:
        data['user'] = user_id
        serializer = OperatorCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        operator = serializer.create()

    except ValidationError as exc:
        # Wrap errors
        raise ValidationError({
            ApiSpecialKeys.OPERATOR_DATA: exc.detail,
        })

    return operator.id


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
def create_provider_wrap(data, business_name, user_id):
    # Handle provider role creation
    try:
        data['user'] = user_id
        serializer = ProviderCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        provider = serializer.create(business_name)

    except ValidationError as exc:
        # Wrap errors
        raise ValidationError({
            ApiSpecialKeys.PROVIDER_DATA: exc.detail,
        })

    return provider.id


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

    try:
        booking = Booking.objects.get(id=booking_id)
        booking.created_by = User.objects.get(id=data['created_by'])
        booking.save()
    except User.DoesNotExist:
        raise ValidationError({
            'created_by': 'User not found'
        })

    return booking_id


@transaction.atomic
def create_events_wrap(datalist, business, booking_id, group_booking):
    # Handle events creation
    event_ids = []
    event_errors = []
    for event_data in datalist:
        try:
            event_data['booking'] = booking_id
            serializer = EventCreateSerializer(data=event_data)
            serializer.is_valid(raise_exception=True)
            event_id = serializer.create(business, group_booking)
            event_ids.append(event_id)

        except ValidationError as exc:
            event_errors.append(exc.detail)

    if event_errors:
        raise ValidationError({
            ApiSpecialKeys.EVENT_DATALIST: event_errors
        })

    return event_ids


def create_event(data, business_name, requester_id, group_booking):
    if not data.get('requester'):
        data['requester'] = requester_id

    serializer = EventCreateSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    return serializer.create(business_name, group_booking)


@transaction.atomic
def create_offers_wrap(datalist, business, booking_id):
    offer_ids = []
    offer_errors = []
    for offer_data in datalist:
        try:
            offer_data['booking'] = booking_id
            serializer = OfferCreateSerializer(data=offer_data)
            serializer.is_valid(raise_exception=True)
            offer_id = serializer.create(business)
            offer_ids.append(offer_id)

        except ValidationError as exc:
            offer_errors.append(exc.detail)

    if offer_errors:
        raise ValidationError({
            ApiSpecialKeys.OFFER_DATALIST: offer_errors
        })
    
    return offer_ids


@transaction.atomic
def create_reports_wrap(datalist, event_id):
    report_ids = []
    report_errors = []
    for report_data in datalist:
        try:
            report_data['event'] = event_id
            serializer = ReportCreateSerializer(data=report_data)
            serializer.is_valid(raise_exception=True)
            report_id = serializer.create()
            report_ids.append(report_id)

        except ValidationError as exc:
            report_errors.append(exc.detail)

    if report_errors:
        raise ValidationError({
            ApiSpecialKeys.REPORT_DATALIST: report_errors
        })
    
    return report_ids


def create_report(data, business, event_id):
    if not data.get('event'):
        data['event'] = event_id

    serializer = ReportCreateSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    return serializer.create(business)


def create_service(data, business_name, provider_id):
    if not data.get('provider'):
        data['provider'] = provider_id
    if not data.get('business'):
        data['business'] = business_name

    serializer = ServiceCreateSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    return serializer.create()

def create_service_area(data, provider_id):
    if not data.get('provider'):
        data['provider'] = provider_id

    serializer = ServiceAreaCreateSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    return serializer.create()

def create_company_relationship(data, company_id):
    if not data.get('company'):
        data['company'] = company_id

    serializer = CompanyRelationshipCreateSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    return serializer.create()


@transaction.atomic
def create_services_wrap(datalist, business_name, provider_id):
    service_ids = []
    service_errors = []
    for service_data in datalist:
        try:
            service_data['business'] = business_name
            service_data['provider'] = provider_id
            serializer = ServiceCreateSerializer(data=service_data)
            serializer.is_valid(raise_exception=True)
            service_id = serializer.create()
            service_ids.append(service_id)

        except ValidationError as exc:
            service_errors.append(exc.detail)

    if service_errors:
        raise ValidationError({
            ApiSpecialKeys.SERVICE_DATALIST: service_errors
        })

    return service_ids


@transaction.atomic
def create_service_areas_wrap(datalist, provider_id):
    service_area_ids = []
    service_area_errors = []
    for service_area_data in datalist:
        try:
            service_area_data['provider'] = provider_id
            serializer = ServiceAreaCreateSerializer(data=service_area_data)
            serializer.is_valid(raise_exception=True)
            service_area_id = serializer.create()
            service_area_ids.append(service_area_id)
        
        except ValidationError as exc:
            service_area_errors.append(exc.detail)
    
    if service_area_errors:
        raise ValidationError({
            ApiSpecialKeys.SERVICE_AREA_DATALIST: service_area_errors
        })
    
    return service_area_ids


@transaction.atomic
def create_company(data, business_name):
    serializer = CompanyCreateSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    company = serializer.create(business_name)
    return company.id

@transaction.atomic
def create_company_relationships_wrap(data, company_id):
    try:
        data["company_from"] = company_id
        serializer = CompanyRelationshipCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        company_relationship = serializer.create()
        
    except ValidationError as exc:
        raise ValidationError({
            ApiSpecialKeys.COMPANY_RELATIONSHIPS_DATA: exc.detail,
    })
    
    return company_relationship.id

# Update
@transaction.atomic
def update_rate_wrap(data, business_name, rate_instance):
        # Handle service update
    try:
        serializer = RateUpdateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.update(rate_instance, business_name)

    except ValidationError as exc:
        # Wrap errors
        raise ValidationError({
            ApiSpecialKeys.RATES_DATALIST: exc.detail,
        })

@transaction.atomic
def update_user(data, user_instance):
    serializer = UserUpdateSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    serializer.update(user_instance)


@transaction.atomic
def update_agent_wrap(data, business_name, agent_instance):
    if not business_name:
        raise BusinessNotProvidedException

    # Handle provider role update
    try:
        serializer = AgentUpdateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.update(agent_instance, business_name)

    except ValidationError as exc:
        # Wrap errors
        raise ValidationError({
            ApiSpecialKeys.AGENT_DATA: exc.detail,
        })


@transaction.atomic
def update_provider_wrap(data, business_name, user_id, provider_instance):
    if not business_name:
        raise BusinessNotProvidedException

    # Handle provider role update
    try:
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
def update_service_wrap(data, business_name, provider_id, service_instance):
    if not business_name:
        raise BusinessNotProvidedException

    # Handle service update
    try:
        data['provider'] = provider_id
        data['business'] = business_name
        serializer = ServiceUpdateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.update(service_instance)

    except ValidationError as exc:
        # Wrap errors
        raise ValidationError({
            ApiSpecialKeys.SERVICE_DATALIST: exc.detail,
        })

@transaction.atomic
def update_service_area_wrap(data, provider_id, service_area_instance):
    # Handle service area update
    try:
        data['provider'] = provider_id
        serializer = ServiceAreaUpdateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.update(service_area_instance)
    
    except ValidationError as exc:
        # Wrap errors
        raise ValidationError({
            ApiSpecialKeys.SERVICE_AREA_DATALIST: exc.detail,
        })

@transaction.atomic
def update_company_relationship_wrap(data, company_id, company_relationship_instance):
    try:
        data["company_from"] = company_id
        serializer = CompanyRelationshipUpdateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.update(company_relationship_instance)

    except ValidationError as exc:
        raise ValidationError({
            ApiSpecialKeys.COMPANY_RELATIONSHIPS_DATA: exc.detail,
        })


@transaction.atomic
def update_event_wrap(data, business_name, group_booking, event_instance):
    if not business_name:
        raise BusinessNotProvidedException

    try:
        serializer = EventUpdateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.update(event_instance, business_name, group_booking)

    except ValidationError as exc:
        # Wrap errors
        raise ValidationError({
            ApiSpecialKeys.EVENT_DATALIST: exc.detail,
        })


@transaction.atomic
def update_report_wrap(data, report_instance, business):
    try:
        serializer = ReportUpdateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.update(report_instance, business)

    except ValidationError as exc:
        # Wrap errors
        raise ValidationError({
            ApiSpecialKeys.REPORT_DATALIST: exc.detail,
        })

# Bulk
@transaction.atomic
def handle_events_bulk(datalist: list, business_name, requester_id, group_booking, booking_id=None):
    """
    Create, update or delete the events in bulk, depending on whether the payload includes an ID or not
    """
    # TODO It is noteworthy that currently this is not a true bulk operation.
    #  Also, events get created even if an error was found before,
    #  this might make the transaction rollback expensive.
    event_ids = []
    event_errors = []
    error_found = False

    for data in datalist:
        event_id = data.pop('id', None)
        deleted_flag = data.pop(ApiSpecialKeys.DELETED_FLAG, False)
        report_datalist = data.pop(ApiSpecialKeys.REPORT_DATALIST, None)

        if not event_id and deleted_flag:
            raise BadRequestException('Event flagged as deleted but no ID provided')

        try:
            if not event_id:
                data['booking'] = booking_id

                event_id = create_event(
                    data,
                    business_name,
                    requester_id, 
                    group_booking
                )

                if report_datalist:
                    handle_reports_bulk(
                        report_datalist,
                        business_name,
                        event_id=event_id
                    )

            elif not deleted_flag:
                update_event_wrap(
                    data,
                    business_name,
                    group_booking,
                    event_instance=Event.objects.get(id=event_id)
                )

                if report_datalist:
                    handle_reports_bulk(
                        report_datalist,
                        business_name,
                        event_id=event_id
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


@transaction.atomic
def handle_reports_bulk(datalist: list, business, event_id):
    """
    Create, update or delete the reports in bulk, depending on whether the payload includes an ID or not
    """
    # TODO It is noteworthy that currently this is not a true bulk operation.
    #  Also, reports get created even if an error was found before,
    #  this might make the transaction rollback expensive.

    report_ids = []
    report_errors = []
    error_found = False

    for data in datalist:
        report_id = data.pop('id', None)
        deleted_flag = data.pop(ApiSpecialKeys.DELETED_FLAG, False)

        if not report_id and deleted_flag:
            raise BadRequestException('Event flagged as deleted but no ID provided')

        try:
            data['event'] = event_id

            if not report_id:
                report_id = create_report(
                    data,
                    business,
                    event_id
                )
            elif not deleted_flag:
                update_report_wrap(
                    data,
                    report_instance=Report.objects.get(id=report_id),
                    business=business
                )
            else:
                Report.objects.get(id=report_id).delete()

            # Append empty error to object so that the indexes of the errors correspond to the indexes of the data
            report_errors.append({})
            report_ids.append(report_id)

        except ValidationError as exc:
            error_found = True
            report_errors.append(exc.detail)

    if error_found:
        raise ValidationError(report_errors)

    return report_ids


@transaction.atomic
def handle_services_bulk(datalist: list, business_name, provider_id):
    """
    Create, update or delete the services in bulk, depending on whether the payload includes an ID or not
    """
    # TODO It is noteworthy that currently this is not a true bulk operation.
    #  Also, services get created even if an error was found before,
    #  this might make the transaction rollback expensive.

    service_ids = []
    service_errors = []
    error_found = False

    for data in datalist:
        service_id = data.pop('id', None)
        deleted_flag = data.pop(ApiSpecialKeys.DELETED_FLAG, False)

        if not service_id and deleted_flag:
            raise BadRequestException('Service flagged as deleted but no ID provided')

        try:
            if not service_id:
                service_id = create_service(
                    data,
                    business_name,
                    provider_id
                )
            elif not deleted_flag:
                update_service_wrap(
                    data,
                    business_name,
                    provider_id,
                    service_instance=Service.objects.get(id=service_id)
                )
            else:
                Service.objects.get(id=service_id).delete()

            # Append empty error to object so that the indexes of the errors correspond to the indexes of the data
            service_errors.append({})
            service_ids.append(service_id)

        except ValidationError as exc:
            error_found = True
            service_errors.append(exc.detail)

    if error_found:
        raise ValidationError(service_errors)

    return service_ids

@transaction.atomic
def handle_service_areas_bulk(datalist: list, provider_id):
    """
    Create, update or delete the service areas in bulk, depending on whether the payload includes an ID or not
    """
    # TODO It is noteworthy that currently this is not a true bulk operation.
    #  Also, service areas get created even if an error was found before,
    #  this might make the transaction rollback expensive.

    service_area_ids = []
    service_area_errors = []
    error_found = False

    for data in datalist:
        service_area_id = data.pop('id', None)
        deleted_flag = data.pop(ApiSpecialKeys.DELETED_FLAG, False)

        if not service_area_id and deleted_flag:
            raise BadRequestException('Service Area flagged as deleted but no ID provided')
        try:
            if not service_area_id:
                service_area_id = create_service_area(
                    data,
                    provider_id
                )
            elif not deleted_flag:
                update_service_area_wrap(
                    data,
                    provider_id,
                    service_area_instance=ServiceArea.objects.get(id=service_area_id)
                )
            else:
                ServiceArea.objects.get(id=service_area_id).delete()
            
            # Append empty error to object so that the indexes of the errors correspond to the indexes of the data
            service_area_errors.append({})
            service_area_ids.append(service_area_id)
        
        except ValidationError as exc:
            error_found = True
            service_area_errors.append(exc.detail)
    
    if error_found:
        raise ValidationError(service_area_errors)
    
    return service_area_ids


@transaction.atomic
def handle_agents_bulk(datalist: list, company_id, business_name):
    """
    Create, update or delete the agents in bulk, depending on whether the payload includes an ID or not
    """
    # TODO It is noteworthy that currently this is not a true bulk operation.
    #  Also, agents get created even if an error was found before,
    #  this might make the transaction rollback expensive.

    agents_ids = []
    agents_errors = []
    error_found = False

    for data in datalist:
        agent_id = data.pop('agent_id', None)
        deleted_flag = data.pop(ApiSpecialKeys.DELETED_FLAG, False)
        agent = data.pop('agent', None)
        data['companies'] = agent.get('companies', []) if agent else []
        data['companies'].append(company_id)

        if not agent_id and deleted_flag:
            raise BadRequestException('Agent flagged as deleted but no ID provided')

        try:
            if not agent_id:
                data['username'] = data.get('firstName', '') + '_' + data.get('lastName', '')
                
                user_id = create_user(data)

                agent_id = create_agent_wrap(
                    data,
                    business_name,
                    user_id=user_id
                )
            elif not deleted_flag:
                update_agent_wrap(
                    data,
                    business_name,
                    agent_instance=Agent.objects.get(id=agent_id)
                )
            else:
                Agent.objects.get(id=agent_id).delete()
            
            # Append empty error to object so that the indexes of the errors correspond to the indexes of the data
            agents_errors.append({})
            agents_ids.append(agent_id)
        
        except ValidationError as exc:
            error_found = True
            agents_errors.append(exc.detail)
    
    if error_found:
        raise ValidationError(agents_errors)
    
    return agents_ids

@transaction.atomic
def handle_company_relationships_bulk(datalist: list, company_id):
    """
    Create, update or delete the company relationships in bulk, depending on whether the payload includes an ID or not
    """
    # TODO It is noteworthy that currently this is not a true bulk operation.
    #  Also, company relationships get created even if an error was found before,
    #  this might make the transaction rollback expensive.

    company_relationship_ids = []
    company_relationship_errors = []
    error_found = False

    for data in datalist:
        company_relationship_id = data.pop('id', None)
        deleted_flag = data.pop(ApiSpecialKeys.DELETED_FLAG, False)

        if not company_relationship_id and deleted_flag:
            raise BadRequestException('Company Relationship flagged as deleted but no ID provided')
        try:
            if not company_relationship_id:
                company_relationship_id = create_company_relationships_wrap(
                    data,
                    company_id
                )
            elif not deleted_flag:
                update_company_relationship_wrap(
                    data,
                    company_id,
                    company_relationship_instance=CompanyRelationship.objects.get(id=company_relationship_id)           
                )
            else:
                CompanyRelationship.objects.get(id=company_relationship_id).delete()
            
            company_relationship_errors.append({})
            company_relationship_ids.append(company_relationship_id)
        
        except ValidationError as exc:
            error_found = True
            company_relationship_errors.append(exc.detail)
    
    if error_found:
        raise ValidationError(company_relationship_errors)
    
    return company_relationship_ids

@transaction.atomic
def handle_rates_bulk(datalist: list, business_name, company_id = None, global_setting_id = None):
    """
    Create, update or delete rates in bulk, depending on whether the payload includes an ID or not
    """
    # TODO It is noteworthy that currently this is not a true bulk operation.
    #  Also, company rates get created even if an error was found before,
    #  this might make the transaction rollback expensive.

    rates_ids = []
    rates_errors = []
    error_found = False

    for data in datalist:
        rate_id = data.pop('id', None)
        deleted_flag = data.pop(ApiSpecialKeys.DELETED_FLAG, False)

        if company_id:
            data['company'] = company_id

        if global_setting_id:
            data['global_setting'] = global_setting_id

        if not rate_id and deleted_flag:
            raise BadRequestException('Company rate flagged as deleted but no ID provided')

        try:
            if not rate_id:
                rate_id = create_rate_wrap(
                    data,
                    business_name
                )
            elif not deleted_flag:
                update_rate_wrap(
                    data,
                    business_name,
                    rate_instance=Rate.objects.get(id=rate_id)
                )
            else:
                Rate.objects.get(id=rate_id).delete()

            # Append empty error to object so that the indexes of the errors correspond to the indexes of the data
            rates_errors.append({})
            rates_ids.append(rate_id)

        except ValidationError as exc:
            error_found = True
            rates_errors.append(exc.detail)

    if error_found:
        raise ValidationError(rates_errors)

    return rates_ids