from core_api.queries.companies import ApiSpecialSqlCompanies
from core_api.queries.events import ApiSpecialSqlEvents
from core_api.queries.operators import ApiSpecialSqlOperators
from core_api.queries.rates import ApiSpecialSqlRates
from core_api.queries.reports import ApiSpecialSqlReports
from core_api.queries.service_root import ApiSpecialSqlServiceRoot
from core_api.queries.services import ApiSpecialSqlServices

class ApiSpecialSqlBookings():
    @staticmethod
    def get_booking_sql_ct_id(cursor):
        query = """
            SELECT
                id
            FROM "django_content_type" content_type
            WHERE app_label = 'core_backend' AND model = 'booking'
        """

        cursor.execute(query, [id])
        result = cursor.fetchone()
        if result is not None:
            return result[0]

        return None
    
    @staticmethod
    def get_provider_sql_ct_id(cursor):
        query = """
            SELECT
                id
            FROM "django_content_type" content_type
            WHERE app_label = 'core_backend' AND model = 'provider'
        """

        cursor.execute(query, [id])
        result = cursor.fetchone()
        if result is not None:
            return result[0]

        return None

    @staticmethod
    def get_booking_sql_where_clause(id, limit, offset, parent_id):
        params = []
        limit_statement = ''
        where_conditions = 'booking.is_deleted = FALSE'

        if id is not None:
            where_conditions += ' AND booking.id = %s'
            params.append(id)
        
        if parent_id is not None:
            where_conditions += ' AND booking.parent_id = %s'
            params.append(parent_id)

        if limit is not None and limit > 0 and offset is not None and offset >= 0:
            limit_statement = 'LIMIT %s OFFSET %s'
            params.append(limit)
            params.append(offset)

        return params, where_conditions, limit_statement
    
    @staticmethod
    def get_booking_sql(cursor, id, limit, offset, parent_id):
        parent_booking_ct_id = ApiSpecialSqlBookings.get_booking_sql_ct_id(cursor)
        parent_event_ct_id = ApiSpecialSqlEvents.get_event_sql_ct_id(cursor)
        parent_service_ct_id = ApiSpecialSqlServices.get_service_sql_ct_id(cursor)
        parent_provider_ct_id = ApiSpecialSqlBookings.get_provider_sql_ct_id(cursor)
        parent_companies_ct_id = ApiSpecialSqlCompanies.get_companies_sql_ct_id(cursor)
        parent_operator_ct_id = ApiSpecialSqlOperators.get_operator_sql_ct_id(cursor)
        parent_service_root_ct_id = ApiSpecialSqlServiceRoot.get_service_root_sql_ct_id(cursor)
        parent_report_ct_id = ApiSpecialSqlReports.get_report_sql_ct_id(cursor)
        parent_rate_ct_id = ApiSpecialSqlRates.get_rate_sql_ct_id(cursor)
        params, where_conditions, limit_statement = ApiSpecialSqlBookings.get_booking_sql_where_clause(id, limit, offset, parent_id)

        query = """--sql
            SELECT json_agg(_query_result.json_data) AS result FROM (
                SELECT
                    (json_build_object(
                        'id', booking.id,
                        'status', booking.status,
                        'parent_id', booking.parent_id,
                        'public_id', booking.public_id,
                        'created_at', booking.created_at,
                        'is_deleted', booking.is_deleted,
                        'business_id', booking.business_id,
                        'created_by_id', booking.created_by_id,
                        'service_root_id', booking.service_root_id,
                        'services', COALESCE((
                            SELECT
                                json_agg(json_build_object(
                                    'id', _services.id,
                                    'root_id', _services.root_id,
                                    'bill_rate', _services.bill_rate,
                                    'is_deleted', _services.is_deleted,
                                    'bill_amount', _services.bill_amount,
                                    'business_id', _services.business_id,
                                    'bill_rate_type', _services.bill_rate_type,
                                    'bill_min_payment', _services.bill_min_payment,
                                    'bill_no_show_fee', _services.bill_no_show_fee,
                                    'bill_rate_minutes_threshold', _services.bill_rate_minutes_threshold,
                                    'provider', (
                                        SELECT
                                            json_build_object(
                                                'id', _providers.id,
                                                'salary', _providers.salary,
                                                'is_deleted', _providers.is_deleted,
                                                'payment_via', _providers.payment_via,
                                                'contract_type', _providers.contract_type,
                                                'payment_account', _providers.payment_account,
                                                'payment_routing', _providers.payment_routing,
                                                'minimum_bookings', _providers.minimum_bookings,
                                                'payment_account_type', _providers.payment_account_type,
                                                'first_name', _users.first_name,
                                                'last_name', _users.last_name,
                                                'user_id', _users.id
                                            )::jsonb ||
                                            COALESCE(
                                                (
                                                    SELECT
                                                        json_object_agg(extra.key, REPLACE(REPLACE(extra.data::text, '\"', ''), '\\', ''))
                                                    FROM "core_backend_extra" extra
                                                    WHERE extra.parent_ct_id = %s AND extra.parent_id = _providers.id
                                                )::jsonb,
                                                '{}'::jsonb
                                            )::jsonb
                                        FROM "core_backend_provider" _providers
                                            INNER JOIN "core_backend_user" _users
                                                ON _users.id = _providers.user_id
                                        WHERE _providers.id = _services.provider_id
                                    )
                                )::jsonb ||
                                (
                                    SELECT
                                        json_object_agg(extra.key, REPLACE(REPLACE(extra.data::text, '\"', ''), '\\', ''))
                                    FROM "core_backend_extra" extra
                                    WHERE extra.parent_ct_id = %s AND extra.parent_id = _services.id
                                )::jsonb)
                            FROM "core_backend_booking_services" _booking_services
                                INNER JOIN "core_backend_service" _services
                                    ON _services.id = _booking_services.service_id
                            WHERE _booking_services.booking_id = booking.id
                        ), '[]'::JSON),
                        'companies', COALESCE((
                            SELECT
                                json_agg(json_build_object(
                                    'id', _companies.id,
                                    'name', _companies.name,
                                    'is_deleted', _companies.is_deleted,
                                    'type', _companies.type
                                )::jsonb ||
                                COALESCE(
                                    (
                                        SELECT
                                            json_object_agg(extra.key, REPLACE(REPLACE(extra.data::text, '\"', ''), '\\', ''))
                                        FROM "core_backend_extra" extra
                                        WHERE extra.parent_ct_id = %s AND extra.parent_id = _booking_companies.company_id
                                    )::jsonb,
                                    '{}'::jsonb
                                )::jsonb)
                            FROM "core_backend_booking_companies" _booking_companies
                                INNER JOIN "core_backend_company" _companies
                                    ON _companies.id = _booking_companies.company_id
                            WHERE _booking_companies.booking_id = booking.id
                        ), '[]'::JSON),
                        'operators', COALESCE((
                            SELECT
                                json_agg(json_build_object(
                                    'id', _operators.id,
                                    'first_name', _users.first_name,
                                    'last_name', _users.last_name,
                                    'user_id', _users.id,
                                    'is_deleted', _operators.is_deleted,
                                    'hiring_date', _operators.hiring_date,
                                    'title', _users.title,
                                    'suffix', _users.suffix,
                                    'date_of_birth', _users.date_of_birth,
                                    'location', (
                                        SELECT 
                                        json_build_object(
                                            'id', location.id,
                                            'country', location.country,
                                            'address', location.address,
                                            'city', location.city,
                                            'state', location.state,
                                            'zip', location.zip,
                                            'unit_number', location.unit_number
                                        )
                                        FROM "core_backend_location" location
                                        WHERE location.id = _users.location_id
                                    ),
                                    'contacts', COALESCE((
                                        SELECT json_agg(
                                        json_build_object(
                                            'id', contact.id,
                                            'email', contact.email,
                                            'phone', contact.phone,
                                            'fax', contact.fax,
                                            'phone_context', contact.phone_context,
                                            'email_context', contact.email_context,
                                            'fax_context', contact.fax_context
                                        )
                                        )
                                        FROM "core_backend_user_contacts" _user_contact
                                        INNER JOIN "core_backend_contact" contact
                                            ON _user_contact.contact_id = contact.id
                                        WHERE _user_contact.user_id = _users.id
                                    ), '[]'::json)
                                )::jsonb ||
                                COALESCE(
                                    (
                                        SELECT
                                            json_object_agg(extra.key, REPLACE(REPLACE(extra.data::text, '\"', ''), '\\', ''))
                                        FROM "core_backend_extra" extra
                                        WHERE extra.parent_ct_id = %s AND extra.parent_id = _booking_operators.operator_id
                                    )::jsonb,
                                    '{}'::jsonb
                                )::jsonb)
                            FROM "core_backend_booking_operators" _booking_operators
                                INNER JOIN "core_backend_operator" _operators
                                    ON _operators.id = _booking_operators.operator_id
                                INNER JOIN "core_backend_user" _users
                                    ON _users.id = _operators.user_id
                            WHERE _booking_operators.booking_id = booking.id
                        ), '[]'::JSON),
                        'service_root', (
                            SELECT
                                json_build_object(
                                    'id', _serviceroot.id,
                                    'name', _serviceroot.name,
                                    'is_deleted', _serviceroot.is_deleted,
                                    'description', _serviceroot.description,
                                    'categories', COALESCE((
                                        SELECT json_agg(row_to_json(_categories))
                                        FROM core_backend_serviceroot_categories _root_categories
                                            INNER JOIN core_backend_category _categories
                                                ON _categories.id = _root_categories.category_id
                                        WHERE _root_categories.serviceroot_id = _serviceroot.id
                                    ), '[]'::JSON)
                                )::jsonb ||
                                COALESCE(
                                    (
                                        SELECT
                                            json_object_agg(extra.key, REPLACE(REPLACE(extra.data::text, '\"', ''), '\\', ''))
                                        FROM "core_backend_extra" extra
                                        WHERE extra.parent_ct_id = %s AND extra.parent_id = _serviceroot.id
                                    )::jsonb,
                                    '{}'::jsonb
                                )::jsonb
                            FROM "core_backend_serviceroot" _serviceroot
                            WHERE _serviceroot.id = booking.service_root_id
                        ),
                        'children', COALESCE((
                            SELECT
                                json_agg(json_build_object(
                                    'id', booking_children.id,
                                    'public_id', booking_children.public_id
                                ))
                                FROM "core_backend_booking" booking_children
                                WHERE booking_children.parent_id = booking.id
                        ), '[]'::JSON),
                        'notes', COALESCE((
                            SELECT
                                json_agg(json_build_object(
                                    'id', note.id,
                                    'created_at', note.created_at,
                                    'last_updated_at', note.last_updated_at,
                                    'created_by', user_note.id,
                                    'created_by_first_name', user_note.first_name,
                                    'created_by_last_name', user_note.last_name,
                                    'text', note.text
                                ))
                                FROM "core_backend_note" note
                                    LEFT JOIN "core_backend_user" user_note
                                        ON user_note.id = note.created_by_id
                                WHERE note.booking_id = booking.id
                        ), '[]'::JSON),
                        'events', COALESCE((
                            SELECT
                                json_agg(json_build_object(
                                    'id', event.id,
                                    'is_deleted', event.is_deleted,
                                    'start_at', event.start_at,
                                    'end_at', event.end_at,
                                    'arrive_at', event.arrive_at,
                                    'description', event.description,
                                    'affiliates', COALESCE((
                                        SELECT JSON_AGG(json_build_object(
                                            'id', affiliation.id,
                                            'company', affiliation.company_id,
                                            'recipient', json_build_object(
                                                'id', recipient.id,
                                                'is_deleted', recipient.is_deleted,
                                                'user_id', recipient.user_id,
                                                'first_name', recipientUser.first_name,
                                                'last_name', recipientUser.last_name,
                                                'date_of_birth', recipientUser.date_of_birth,
                                                'title', recipientUser.title,
                                                'suffix', recipientUser.suffix,
                                                'notes', COALESCE((
                                                    SELECT
                                                        json_agg(json_build_object(
                                                            'id', _patient_notes.id,
                                                            'created_at', _patient_notes.created_at,
                                                            'last_updated_at', _patient_notes.last_updated_at,
                                                            'created_by', _user_note.id,
                                                            'created_by_first_name', _user_note.first_name,
                                                            'created_by_last_name', _user_note.last_name,
                                                            'text', _patient_notes.text
                                                        ))
                                                        FROM "core_backend_note" _patient_notes
                                                            LEFT JOIN "core_backend_user" _user_note
                                                                ON _user_note.id = _patient_notes.created_by_id
                                                        WHERE _patient_notes.recipient_id = recipient.id
                                                ), '[]'::JSON)
                                            ),
                                            'is_deleted', affiliation.is_deleted
                                        )) FROM core_backend_event_affiliates affiliates
                                        LEFT JOIN core_backend_affiliation affiliation on affiliation.id = affiliates.affiliation_id
                                        LEFT JOIN core_backend_recipient recipient on recipient.id = affiliation.recipient_id
                                        LEFT JOIN core_backend_user recipientUser on recipientUser.id = recipient.user_id
                                        WHERE affiliates.event_id = event.id
                                    ), '[]'::JSON),
                                    'agents', COALESCE((
                                        SELECT json_agg(json_build_object(
                                            'id', agent.id,
                                            'role', agent.role,
                                            'is_deleted', agent.is_deleted,
                                            'user_id', agent.user_id,
                                            'first_name', user_agent.first_name,
                                            'last_name', user_agent.last_name,
                                            'date_of_birth', user_agent.date_of_birth,
                                            'ssn', user_agent.ssn,
                                            'email', user_agent.email,
                                            'title', user_agent.title,
                                            'suffix', user_agent.suffix,
                                            'agent_id', ARRAY[agent.id],
                                            'companies', COALESCE((
                                                SELECT 
                                                    ARRAY[agent_companies.company_id]
                                                FROM "core_backend_agent_companies" agent_companies
                                                WHERE agent_companies.agent_id = agent.id
                                            )),
                                            'contacts', COALESCE((
                                                SELECT json_agg(json_build_object(
                                                    'id', contact.id,
                                                    'email', contact.email,
                                                    'phone', contact.phone,
                                                    'fax', contact.fax,
                                                    'phone_context', contact.phone_context,
                                                    'email_context', contact.email_context,
                                                    'fax_context', contact.fax_context
                                                ))    
                                                FROM "core_backend_user_contacts" user_contacts
                                                    LEFT JOIN "core_backend_contact" contact
                                                        ON user_contacts.contact_id = contact.id
                                                WHERE user_contacts.user_id = user_agent.id
                                            ), '[]'::JSON),
                                            'location', COALESCE((
                                                SELECT json_agg(json_build_object(
                                                    'id', _location.id,
                                                    'is_deleted', _location.is_deleted,
                                                    'address', _location.address,
                                                    'city', _location.city,
                                                    'state', _location.state,
                                                    'country', _location.country,
                                                    'zip', _location.zip,
                                                    'unit_number', _location.unit_number,
                                                    'is_deleted', _location.is_deleted
                                                ))
                                                FROM "core_backend_location" _location
                                                WHERE user_agent.location_id = _location.id
                                            ), '[]'::JSON),
                                            'is_requester', COALESCE(requester.id IS NOT NULL, true)
                                        ))
                                        FROM "core_backend_event_agents" event_agents
                                            LEFT JOIN "core_backend_agent" agent
                                                ON agent.id = event_agents.agent_id
                                            LEFT JOIN "core_backend_user" user_agent
                                                ON user_agent.id = agent.user_id
                                            LEFT JOIN "core_backend_requester" requester
                                                ON requester.user_id = user_agent.id
                                        WHERE event_agents.event_id = event.id
                                    ), '[]'::JSON),
                                    'authorizations', COALESCE((
                                        SELECT json_agg(json_build_object(
                                            'id', authorization_events.authorization_id,
                                            'last_updated_at', _authorization.last_updated_at,
                                            'is_deleted', _authorization.is_deleted,
                                            'contact_via', _authorization.contact_via,
                                            'status', _authorization.status,
                                            'events', COALESCE((
                                                SELECT json_agg(row_to_json(events)) FROM 
                                                    core_backend_authorization_events auth_events
                                                        INNER JOIN core_backend_event events ON auth_events.event_id = events.id
                                                WHERE auth_events.authorization_id = _authorization.id
                                            ), '[]'::JSON),
                                            'contact', COALESCE((
                                                SELECT
                                                    row_to_json(_contacts)
                                                FROM "core_backend_contact" _contacts
                                                WHERE _contacts.id = _authorization.contact_id AND _contacts.is_deleted=FALSE
                                            ), '{}'::JSON),
                                            'company', COALESCE((
                                                SELECT
                                                    json_agg(json_build_object(
                                                        'id', company_authorization.id,
                                                        'type', company_authorization.type
                                                    ))
                                                FROM "core_backend_company" company_authorization
                                                WHERE company_authorization.id = _authorization.company_id
                                            ), '[]'::JSON),
                                            'authorizer', COALESCE((
                                                SELECT
                                                    json_agg(json_build_object(
                                                        'id', _authorization.authorizer_id,
                                                        'is_deleted', payer_authorization.is_deleted,
                                                        'method', payer_authorization.method,
                                                        'user_id', payer_authorization.user_id,
                                                        'first_name', user_authorization.first_name,
                                                        'last_name', user_authorization.last_name,
                                                        'username', user_authorization.username,
                                                        'date_of_birth', user_authorization.date_of_birth,
                                                        'ssn', user_authorization.ssn,
                                                        'email', user_authorization.email,
                                                        'title', user_authorization.title,
                                                        'suffix', user_authorization.suffix,
                                                        'is_payer', COALESCE(payer_authorization.id IS NOT NULL, true),
                                                        'contacts', COALESCE((
                                                            SELECT json_agg(json_build_object(
                                                                'id', contact.id,
                                                                'email', contact.email,
                                                                'phone', contact.phone,
                                                                'fax', contact.fax,
                                                                'phone_context', contact.phone_context,
                                                                'email_context', contact.email_context,
                                                                'fax_context', contact.fax_context
                                                            ))    
                                                            FROM "core_backend_user_contacts" user_contacts
                                                                LEFT JOIN "core_backend_contact" contact
                                                                    ON user_contacts.contact_id = contact.id
                                                            WHERE user_contacts.user_id = user_authorization.id
                                                        ), '[]'::JSON),
                                                        'location', COALESCE((
                                                            SELECT json_agg(json_build_object(
                                                                'id', _location.id,
                                                                'is_deleted', _location.is_deleted,
                                                                'address', _location.address,
                                                                'city', _location.city,
                                                                'state', _location.state,
                                                                'country', _location.country,
                                                                'zip', _location.zip,
                                                                'unit_number', _location.unit_number,
                                                                'is_deleted', _location.is_deleted
                                                            ))
                                                            FROM "core_backend_location" _location
                                                            WHERE user_authorization.location_id = _location.id
                                                        ), '[]'::JSON),
                                                        'companies', COALESCE((
                                                            SELECT json_agg((
                                                                company
                                                            ))
                                                            FROM "core_backend_payer_companies" payer_companies
                                                                INNER JOIN "core_backend_company" company
                                                                    ON company.id = payer_companies.company_id
                                                            WHERE payer_companies.payer_id = payer_authorization.id
                                                        ), '[]'::JSON)
                                                    ))
                                                FROM "core_backend_payer" payer_authorization
                                                    INNER JOIN "core_backend_user" user_authorization
                                                        ON user_authorization.id = payer_authorization.user_id
                                                WHERE payer_authorization.id = _authorization.authorizer_id
                                            ), '[]'::JSON)
                                        )) 
                                        FROM "core_backend_authorization_events" authorization_events
                                            LEFT JOIN "core_backend_authorization" _authorization
                                                ON _authorization.id = authorization_events.authorization_id
                                        WHERE authorization_events.event_id = event.id
                                    ), '[]'::JSON),
                                    'payer', COALESCE((
                                        SELECT
                                            json_build_object(
                                                'id', event.payer_id,
                                                'is_deleted', payer.is_deleted,
                                                'method', payer.method,
                                                'user_id', payer.user_id,
                                                'first_name', user_payer.first_name,
                                                'last_name', user_payer.last_name,
                                                'username', user_payer.username,
                                                'date_of_birth', user_payer.date_of_birth,
                                                'ssn', user_payer.ssn,
                                                'email', user_payer.email,
                                                'title', user_payer.title,
                                                'suffix', user_payer.suffix,
                                                'is_payer', COALESCE(payer.id IS NOT NULL, true),
                                                'contacts', COALESCE((
                                                    SELECT json_agg(json_build_object(
                                                        'id', contact.id,
                                                        'email', contact.email,
                                                        'phone', contact.phone,
                                                        'fax', contact.fax,
                                                        'phone_context', contact.phone_context,
                                                        'email_context', contact.email_context,
                                                        'fax_context', contact.fax_context
                                                    ))    
                                                    FROM "core_backend_user_contacts" user_contacts
                                                        LEFT JOIN "core_backend_contact" contact
                                                            ON user_contacts.contact_id = contact.id
                                                    WHERE user_contacts.user_id = user_payer.id
                                                ), '[]'::JSON),
                                                'location', COALESCE((
                                                    SELECT json_agg(json_build_object(
                                                        'id', _location.id,
                                                        'is_deleted', _location.is_deleted,
                                                        'address', _location.address,
                                                        'city', _location.city,
                                                        'state', _location.state,
                                                        'country', _location.country,
                                                        'zip', _location.zip,
                                                        'unit_number', _location.unit_number,
                                                        'is_deleted', _location.is_deleted
                                                    ))
                                                    FROM "core_backend_location" _location
                                                    WHERE user_payer.location_id = _location.id
                                                ), '[]'::JSON),
                                                'companies', COALESCE((
                                                    SELECT json_agg((
                                                        company
                                                    ))
                                                    FROM "core_backend_payer_companies" payer_companies
                                                        INNER JOIN "core_backend_company" company
                                                            ON company.id = payer_companies.company_id
                                                    WHERE payer_companies.payer_id = payer.id
                                                ), '[]'::JSON),
                                                'notes', COALESCE((
                                                    SELECT json_agg((
                                                        note_payer
                                                    ))
                                                    FROM "core_backend_note" note_payer
                                                    WHERE note_payer.payer_id = payer.id
                                                ), '[]'::JSON)
                                            )
                                        FROM "core_backend_payer" payer
                                            INNER JOIN "core_backend_user" user_payer
                                                ON user_payer.id = payer.user_id
                                        WHERE payer.id = event.payer_id
                                    ), '{}'::JSON),
                                    'payer_company', COALESCE((
                                        SELECT
                                            json_build_object(
                                                'id', event.payer_company_id,
                                                'is_deleted', _payer_companies.is_deleted,
                                                'name', _payer_companies.name,
                                                'on_hold', _payer_companies.on_hold,
                                                'parent_company_id', _payer_companies.parent_company_id,
                                                'type', _payer_companies.type,
                                                'send_method', _payer_companies.send_method,
                                                'rates', COALESCE((
                                                    SELECT
                                                        json_agg(json_build_object(
                                                            'bill_amount', _company_rate.bill_amount,
                                                            'bill_rate', _company_rate.bill_rate,
                                                            'bill_rate_type', _company_rate.bill_rate_type,
                                                            'root', COALESCE((
                                                                SELECT 
                                                                    json_build_object(
                                                                        'id', _serviceroot.id
                                                                    )
                                                                FROM "core_backend_serviceroot" _serviceroot
                                                                WHERE _serviceroot.id = _company_rate.root_id
                                                            ), '{}'::JSON)
                                                        )::jsonb ||
                                                        (
                                                            SELECT
                                                                json_object_agg(extra.key, REPLACE(REPLACE(extra.data::text, '\"', ''), '\\', ''))
                                                            FROM "core_backend_extra" extra
                                                            WHERE extra.parent_ct_id = %s AND extra.parent_id= _company_rate.id
                                                        )::jsonb)
                                                    FROM "core_backend_rate" _company_rate
                                                    WHERE _company_rate.company_id = _payer_companies.id
                                                    ), '[]'::JSON
                                                )
                                            )
                                        FROM "core_backend_company" _payer_companies
                                        WHERE _payer_companies.id = event.payer_company_id
                                    ), '{}'::JSON),
                                    'reports', COALESCE((
                                        SELECT
                                            json_agg(json_build_object(
                                                'id', _reports.id,
                                                'is_deleted', _reports.is_deleted,
                                                'status', _reports.status,
                                                'arrive_at', _reports.arrive_at,
                                                'arrive_at', _reports.arrive_at,
                                                'start_at', _reports.start_at,
                                                'end_at', _reports.end_at,
                                                'observations', _reports.observations
                                            )::jsonb ||
                                            COALESCE((
                                                SELECT
                                                    json_object_agg(extra.key, REPLACE(REPLACE(extra.data::text, '\"', ''), '\\', ''))
                                                FROM "core_backend_extra" extra
                                                WHERE extra.parent_ct_id = %s AND extra.parent_id = _reports.id
                                            )::jsonb, '{}'::jsonb))
                                        FROM "core_backend_report" _reports
                                        WHERE _reports.event_id = event.id
                                    ), '[]'::JSON),
                                    'requester', COALESCE((
                                        SELECT
                                            json_build_object(
                                                'id', event.requester_id,
                                                'is_deleted', requester.is_deleted,
                                                'user_id', requester.user_id,
                                                'first_name', user_requester.first_name,
                                                'last_name', user_requester.last_name,
                                                'username', user_requester.username,
                                                'date_of_birth', user_requester.date_of_birth,
                                                'ssn', user_requester.ssn,
                                                'email', user_requester.email,
                                                'title', user_requester.title,
                                                'suffix', user_requester.suffix,
                                                'is_requester', COALESCE(requester.id IS NOT NULL, true),
                                                'contacts', COALESCE((
                                                    SELECT json_agg(json_build_object(
                                                        'id', contact.id,
                                                        'email', contact.email,
                                                        'phone', contact.phone,
                                                        'fax', contact.fax,
                                                        'phone_context', contact.phone_context,
                                                        'email_context', contact.email_context,
                                                        'fax_context', contact.fax_context
                                                    ))    
                                                    FROM "core_backend_user_contacts" user_contacts
                                                        LEFT JOIN "core_backend_contact" contact
                                                            ON user_contacts.contact_id = contact.id
                                                    WHERE user_contacts.user_id = user_requester.id
                                                ), '[]'::JSON),
                                                'location', COALESCE((
                                                    SELECT json_agg(json_build_object(
                                                        'id', _location.id,
                                                        'is_deleted', _location.is_deleted,
                                                        'address', _location.address,
                                                        'city', _location.city,
                                                        'state', _location.state,
                                                        'country', _location.country,
                                                        'zip', _location.zip,
                                                        'unit_number', _location.unit_number,
                                                        'is_deleted', _location.is_deleted
                                                    ))
                                                    FROM "core_backend_location" _location
                                                    WHERE user_requester.location_id = _location.id
                                                ), '[]'::JSON),
                                                'companies', COALESCE((
                                                    SELECT json_agg((
                                                        company
                                                    ))
                                                    FROM "core_backend_requester_companies" requester_companies
                                                        INNER JOIN "core_backend_company" company
                                                            ON company.id = requester_companies.company_id
                                                    WHERE requester_companies.requester_id = requester.id
                                                ), '[]'::JSON)
                                            )
                                        FROM "core_backend_requester" requester
                                            INNER JOIN "core_backend_user" user_requester
                                                ON user_requester.id = requester.user_id
                                        WHERE requester.id = event.requester_id
                                    ), '[]'::JSON)
                                )::jsonb ||
                                (
                                    SELECT
                                        json_object_agg(extra.key, REPLACE(REPLACE(extra.data::text, '\"', ''), '\\', ''))
                                    FROM "core_backend_extra" extra
                                    WHERE extra.parent_ct_id = %s AND extra.parent_id = event.id
                                )::jsonb)
                            FROM "core_backend_event" event
                            WHERE event.booking_id = booking.id
                        ), '[]'::JSON)
                    )::jsonb ||
                    COALESCE((
                        SELECT
                            json_object_agg(extra.key, REPLACE(REPLACE(extra.data::text, '\"', ''), '\\', ''))
                        FROM "core_backend_extra" extra
                        WHERE extra.parent_ct_id = %s AND extra.parent_id=booking.id
                    )::jsonb, '{}'::jsonb)) AS json_data
                FROM "core_backend_booking" booking
                    INNER JOIN "core_backend_event" _event 
                        ON booking.id = _event.booking_id
                WHERE %s
                ORDER BY booking.public_id DESC, booking.id
                %s
            ) _query_result
        """ % (
                parent_provider_ct_id,
                parent_service_ct_id,
                parent_companies_ct_id, 
                parent_operator_ct_id,
                parent_service_root_ct_id,
                parent_rate_ct_id,
                parent_report_ct_id,
                parent_event_ct_id, 
                parent_booking_ct_id, 
                where_conditions, 
                limit_statement
               )

        cursor.execute(query, params)
        result = cursor.fetchone()
        if len(result) == 1:
            return result[0]

        return []
    
    def get_bookings_sql(cursor, id, limit, offset, parent_id):
        parent_booking_ct_id = ApiSpecialSqlBookings.get_booking_sql_ct_id(cursor)
        parent_event_ct_id = ApiSpecialSqlEvents.get_event_sql_ct_id(cursor)
        parent_service_ct_id = ApiSpecialSqlServices.get_service_sql_ct_id(cursor)
        parent_provider_ct_id = ApiSpecialSqlBookings.get_provider_sql_ct_id(cursor)
        parent_companies_ct_id = ApiSpecialSqlCompanies.get_companies_sql_ct_id(cursor)
        params, where_conditions, limit_statement = ApiSpecialSqlBookings.get_booking_sql_where_clause(id, limit, offset, parent_id)

        query = """--sql
            SELECT json_agg(_query_result.json_data) AS result FROM (
                SELECT
                    (json_build_object(
                        'id', booking.id,
                        'status', booking.status,
                        'parent_id', booking.parent_id,
                        'public_id', booking.public_id,
                        'created_at', booking.created_at,
                        'is_deleted', booking.is_deleted,
                        'business_id', booking.business_id,
                        'services', COALESCE((
                            SELECT
                                json_agg(json_build_object(
                                    'id', _services.id,
                                    'root_id', _services.root_id,
                                    'provider', (
                                        SELECT
                                            json_build_object(
                                                'id', _providers.id,
                                                'salary', _providers.salary,
                                                'is_deleted', _providers.is_deleted,
                                                'payment_via', _providers.payment_via,
                                                'contract_type', _providers.contract_type,
                                                'payment_account', _providers.payment_account,
                                                'payment_routing', _providers.payment_routing,
                                                'minimum_bookings', _providers.minimum_bookings,
                                                'payment_account_type', _providers.payment_account_type,
                                                'first_name', _users.first_name,
                                                'last_name', _users.last_name,
                                                'user_id', _users.id
                                            )::jsonb ||
                                            COALESCE(
                                                (
                                                    SELECT
                                                        json_object_agg(extra.key, REPLACE(REPLACE(extra.data::text, '\"', ''), '\\', ''))
                                                    FROM "core_backend_extra" extra
                                                    WHERE extra.parent_ct_id = %s AND extra.parent_id = _providers.id
                                                )::jsonb,
                                                '{}'::jsonb
                                            )::jsonb
                                        FROM "core_backend_provider" _providers
                                            INNER JOIN "core_backend_user" _users
                                                ON _users.id = _providers.user_id
                                        WHERE _providers.id = _services.provider_id
                                    )
                                )::jsonb ||
                                (
                                    SELECT
                                        json_object_agg(extra.key, REPLACE(REPLACE(extra.data::text, '\"', ''), '\\', ''))
                                    FROM "core_backend_extra" extra
                                    WHERE extra.parent_ct_id = %s AND extra.parent_id = _services.id
                                )::jsonb)
                            FROM "core_backend_booking_services" _booking_services
                                INNER JOIN "core_backend_service" _services
                                    ON _services.id = _booking_services.service_id
                            WHERE _booking_services.booking_id = booking.id
                        ), '[]'::JSON),
                        'companies', COALESCE((
                            SELECT
                                json_agg(json_build_object(
                                    'id', _companies.id,
                                    'name', _companies.name,
                                    'is_deleted', _companies.is_deleted,
                                    'type', _companies.type
                                )::jsonb ||
                                COALESCE(
                                    (
                                        SELECT
                                            json_object_agg(extra.key, REPLACE(REPLACE(extra.data::text, '\"', ''), '\\', ''))
                                        FROM "core_backend_extra" extra
                                        WHERE extra.parent_ct_id = %s AND extra.parent_id = _booking_companies.company_id
                                    )::jsonb,
                                    '{}'::jsonb
                                )::jsonb)
                            FROM "core_backend_booking_companies" _booking_companies
                                INNER JOIN "core_backend_company" _companies
                                    ON _companies.id = _booking_companies.company_id
                            WHERE _booking_companies.booking_id = booking.id
                        ), '[]'::JSON),
                        'children', COALESCE((
                            SELECT
                                json_agg(json_build_object(
                                    'id', booking_children.id,
                                    'public_id', booking_children.public_id
                                ))
                                FROM "core_backend_booking" booking_children
                                WHERE booking_children.parent_id = booking.id
                        ), '[]'::JSON),
                        'events', COALESCE((
                            SELECT
                                json_agg(json_build_object(
                                    'id', event.id,
                                    'is_deleted', event.is_deleted,
                                    'start_at', event.start_at,
                                    'affiliates', COALESCE((
                                        SELECT JSON_AGG(json_build_object(
                                            'id', affiliation.id,
                                            'company', affiliation.company_id,
                                            'recipient', json_build_object(
                                                'id', recipient.id,
                                                'is_deleted', recipient.is_deleted,
                                                'user_id', recipient.user_id,
                                                'first_name', recipientUser.first_name,
                                                'last_name', recipientUser.last_name,
                                                'date_of_birth', recipientUser.date_of_birth,
                                                'title', recipientUser.title,
                                                'suffix', recipientUser.suffix
                                            ),
                                            'is_deleted', affiliation.is_deleted
                                        )) FROM core_backend_event_affiliates affiliates
                                        LEFT JOIN core_backend_affiliation affiliation on affiliation.id = affiliates.affiliation_id
                                        LEFT JOIN core_backend_recipient recipient on recipient.id = affiliation.recipient_id
                                        LEFT JOIN core_backend_user recipientUser on recipientUser.id = recipient.user_id
                                        WHERE affiliates.event_id = event.id
                                    ), '[]'::JSON),
                                    'agents', COALESCE((
                                        SELECT JSON_AGG(t) as agents FROM (
                                            SELECT ARRAY[core_backend_event_agents.agent_id] as agents_id, 
                                            ARRAY[core_backend_event_agents.id] as companies, 
                                            agent_lateral.*, user_lateral.*, user_contacts_lateral.*,
                                            location_lateral.*, contacts_lateral.*, requester_lateral.*, payer_lateral.*
                                            FROM core_backend_event_agents,
                                            LATERAL (
                                                SELECT agent_id as id, role, is_deleted, user_id AS userId, user_id FROM core_backend_agent WHERE id = core_backend_event_agents.agent_id
                                            ) as agent_lateral,
                                            LATERAL (
                                                SELECT username, email, first_name, last_name, national_id, ssn, date_of_birth, title, suffix, location_id FROM core_backend_user
                                                WHERE core_backend_user.id = userId
                                            ) AS user_lateral,
                                            LATERAL (
                                                SELECT JSON_AGG(t) -> 0 as user_contacts_ids FROM (
                                                SELECT contact_id FROM core_backend_user_contacts WHERE core_backend_user_contacts.user_id = userId
                                                ) t
                                            ) AS user_contacts_lateral,
                                            LATERAL (
                                                SELECT JSON_AGG(t) as contacts FROM (
                                                SELECT * FROM core_backend_contact WHERE core_backend_contact.id = (user_contacts_lateral.user_contacts_ids ->> 'contact_id')::integer
                                                ) t
                                            ) As contacts_lateral,
                                            LATERAL (
                                                SELECT JSON_AGG(t) as location FROM (
                                                SELECT * FROM core_backend_location WHERE core_backend_location.id = location_id
                                                ) t
                                            ) As location_lateral,
                                            LATERAL (
                                                SELECT id as requester_id, COALESCE(id IS NOT NULL, true) as is_requester FROM core_backend_requester WHERE core_backend_requester.user_id = userId
                                            ) AS requester_lateral,
                                            LATERAL (
                                                SELECT id as payer_id, COALESCE(id IS NOT NULL, true) as is_payer FROM core_backend_payer WHERE core_backend_payer.user_id = userId
                                            ) AS payer_lateral
                                            WHERE core_backend_event_agents.event_id = event.id
                                        ) t
                                    ), '[]'::JSON),
                                    'requester', COALESCE((
                                        SELECT row_to_json(t) FROM ( 
                                            SELECT requester.*, COALESCE(id IS NULL, false) AS is_requester, requester_lateral.* FROM core_backend_requester requester,
                                                LATERAL (
                                                    SELECT username, email, first_name, last_name, national_id, ssn, date_of_birth, title, suffix,
                                                    user_contacts_lateral.*, contacts_lateral.*, company_lateral.*, location_lateral.*, requester_companies_lateral.* FROM core_backend_user,
                                                    LATERAL (
                                                        SELECT JSON_AGG(t) -> 0 as user_contacts_ids FROM (
                                                        SELECT contact_id FROM core_backend_user_contacts WHERE core_backend_user_contacts.user_id = core_backend_user.id
                                                        ) t
                                                    ) AS user_contacts_lateral,
                                                    LATERAL (
                                                        SELECT JSON_AGG(t) as contacts FROM (
                                                        SELECT * FROM core_backend_contact WHERE core_backend_contact.id = (user_contacts_lateral.user_contacts_ids ->> 'contact_id')::integer
                                                        ) t
                                                    ) As contacts_lateral,  
                                                    LATERAL (
                                                        SELECT requester_id AS requester_id, company_id as company_id FROM core_backend_requester_companies WHERE requester_id = requester.id
                                                    ) AS requester_companies_lateral,
                                                    LATERAL (
                                                        SELECT JSON_AGG(t) as companies FROM (
                                                        SELECT * FROM core_backend_company WHERE core_backend_company.id = company_id
                                                        ) t
                                                    ) As company_lateral,
                                                    LATERAL (
                                                        SELECT JSON_AGG(t) as location FROM (
                                                        SELECT * FROM core_backend_location WHERE core_backend_location.id = core_backend_user.location_id
                                                        ) t
                                                    ) As location_lateral
                                                WHERE core_backend_user.id = requester.user_id
                                            ) AS requester_lateral
                                            WHERE requester.id = event.requester_id
                                        ) t
                                    ), '[]'::JSON)
                                )::jsonb ||
                                (
                                    SELECT
                                        json_object_agg(extra.key, REPLACE(REPLACE(extra.data::text, '\"', ''), '\\', ''))
                                    FROM "core_backend_extra" extra
                                    WHERE extra.parent_ct_id = %s AND extra.parent_id = event.id
                                )::jsonb)
                            FROM "core_backend_event" event
                            WHERE event.booking_id = booking.id
                        ), '[]'::JSON)
                    )::jsonb ||
                    COALESCE((
                        SELECT
                            json_object_agg(extra.key, REPLACE(REPLACE(extra.data::text, '\"', ''), '\\', ''))
                        FROM "core_backend_extra" extra
                        WHERE extra.parent_ct_id = %s AND extra.parent_id=booking.id
                    )::jsonb, '{}'::jsonb)) AS json_data
                FROM "core_backend_booking" booking
                    INNER JOIN "core_backend_event" _event 
                        ON booking.id = _event.booking_id
                WHERE %s
                ORDER BY booking.public_id DESC, booking.id
                %s
            ) _query_result
        """ % (
                parent_provider_ct_id,
                parent_service_ct_id,
                parent_companies_ct_id, 
                parent_event_ct_id, 
                parent_booking_ct_id, 
                where_conditions, 
                limit_statement
               )

        cursor.execute(query, params)
        result = cursor.fetchone()
        if len(result) == 1:
            return result[0]

        return []
    
    @staticmethod
    def get_booking_count_sql(cursor, id, parent_id):
        params, where_conditions, _ = ApiSpecialSqlBookings.get_booking_sql_where_clause(id, None, None, parent_id)

        query = """
            SELECT
               COUNT(*)
            FROM "core_backend_booking" booking
            WHERE %s
        """ % where_conditions

        cursor.execute(query, params)
        result = cursor.fetchone()
        if len(result) == 1:
            return result[0]

        return 0