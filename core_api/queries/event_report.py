from core_api.queries.events import ApiSpecialSqlEvents

class ApiSpecialSqlEventReports():
    @staticmethod
    def get_payment_price_sql(cursor):
        parent_ct_rate_id = ApiSpecialSqlEventReports.get_rate_sql_ct_id(cursor)

        query = """
            SELECT
                CASE 
                    WHEN _reports.end_at IS NOT NULL THEN 
                        CASE 
                            WHEN 
                                MOD(FLOOR(EXTRACT(EPOCH FROM (_reports.end_at - _reports.start_at)) / 60), 60) >= _rate.bill_rate_minutes_threshold 
                                    THEN 
                                        CASE
                                            WHEN (FLOOR((EXTRACT(EPOCH FROM (_reports.end_at - _reports.start_at)) / 60) / 60) + 1) * _rate.bill_amount >= _rate.bill_min_payment
                                                THEN (FLOOR((EXTRACT(EPOCH FROM (_reports.end_at - _reports.start_at)) / 60) / 60) + 1) * _rate.bill_amount
                                            ELSE _rate.bill_min_payment
                                        END
                            ELSE
                                CASE
                                    WHEN FLOOR((EXTRACT(EPOCH FROM (_reports.end_at - _reports.start_at)) / 60) / 60) * _rate.bill_amount >= _rate.bill_min_payment
                                        THEN FLOOR((EXTRACT(EPOCH FROM (_reports.end_at - _reports.start_at)) / 60) / 60) * _rate.bill_amount
                                    ELSE _rate.bill_min_payment
                                END
                        END
                    ELSE NULL
                END
            FROM core_backend_rate _rate
                LEFT JOIN core_backend_serviceroot _root
                    ON _root.id = _rate.root_id and _root.is_deleted = False
                LEFT JOIN "core_backend_extra" _extra_rate
                    ON _extra_rate.parent_ct_id = %s AND _extra_rate.parent_id=_rate.id
        """ % parent_ct_rate_id

        return query

    @staticmethod
    def get_event_report_sql(
        cursor,
        id,
        limit,
        offset,
        start_at,
        end_at,
        items_included,
        items_excluded,
        recipient_id,
        agent_id,
        provider_id,
        start_date,
        end_date,
        provider_name,
        recipient_name,
        clinic_name,
        booking_public_id,
        field_to_sort,
        order_to_sort
    ):
        parent_ct_id = ApiSpecialSqlEvents.get_event_sql_ct_id(cursor)
        query_price = ApiSpecialSqlReports.get_payment_price_sql(cursor)
        params, where_conditions, limit_statement = ApiSpecialSqlEvents.get_event_sql_where_clause(
            id,
            limit,
            offset,
            parent_ct_id,
            start_at,
            end_at,
            items_included,
            items_excluded,
            recipient_id,
            agent_id,
            provider_id,
            start_date,
            end_date,
            provider_name,
            recipient_name,
            clinic_name,
            booking_public_id,
        )

        query = """--sql
        SELECT json_agg(result.json_data) AS result FROM (
            SELECT sub.json_data FROM (
                SELECT
                    (json_build_object(
                        'id', event.id,
                        'first_name', _users_affiliates.first_name,
                        'last_name', _users_affiliates.last_name,
                        'user_id', _users_affiliates.id,
                        'date_of_birth', _users_affiliates.date_of_birth,
                        'phone_contact', _contact_affiliates.phone,
                        'email_contact', _contact_affiliates.email,
                        'fax_contact', _contact_affiliates.fax,
                        'address', _location_affiliates.address,
                        'unit_number', _location_affiliates.unit_number,
                        'city', _location_affiliates.city,
                        'country', _location_affiliates.country,
                        'zip', _location_affiliates.zip,
                        'public_id', booking.public_id,
                        'date', event.start_at,
                        'arrive_time', _reports.arrive_at,
                        'start_time', _reports.start_at,
                        'end_time', _reports.end_at,
                        'payer_company_type', _payer_companies.type,
                        'payer_company_name', _payer_companies.name,
                        'payer_company_send_method', _payer_companies.send_method,
                        'payer_company_address', _payer_companies_locations.address,
                        'payer_company_city', _payer_companies_locations.city,
                        'payer_company_state', _payer_companies_locations.state,
                        'provider_first_name', _users_agents.first_name,
                        'provider_last_name', _users_agents.last_name,
                        'clinic', company.name,
                        'clinic_address', _company_booking_locations.address,
                        'clinic_unit_number', _company_booking_locations.unit_number,
                        'clinic_city', _company_booking_locations.city,
                        'clinic_state', _company_booking_locations.state,
                        'clinic_country', _company_booking_locations.country,
                        'clinic_zip', _company_booking_locations.zip,
                        'send_method', company.send_method,
                        'type_of_appointment', event.description,
                        'interpreter_first_name', provider_user.first_name,
                        'interpreter_last_name', provider_user.last_name,
                        'interpreter_certificate_number', COALESCE((  
                            SELECT 
                                ((data->>0)::jsonb->>0)::jsonb->>'certificate_number'
                            FROM public.core_backend_extra extra_provider 
                            WHERE POSITION('certificate_number' IN data::text) > 0 
                            AND provider.id = extra_provider.parent_id 
                            AND data::text != '"[]"'
                            LIMIT 1
                        ), ''),
                        'interpreter_certificate', COALESCE((  
                            SELECT 
                                _category.description
                            FROM public.core_backend_extra extra_provider 
                                LEFT JOIN core_backend_category _category
                                    ON _category.id = (((data->>0)::jsonb->>0)::jsonb->>'certificate_id')::integer
                            WHERE POSITION('certificate_number' IN data::text) > 0 
                            AND provider.id = extra_provider.parent_id 
                            AND data::text != '"[]"'
                            LIMIT 1
                        ), ''),
                        'modality', _booking_serviceroot.name,
                        'status_report', _reports.status,
                        'operators_first_name', _booking_user_operator.first_name,
                        'operators_last_name', _booking_user_operator.last_name,
                        'notes', COALESCE((  
                            SELECT string_agg(note, ', ')
                            FROM (
                                SELECT json_array_elements_text(
                                    COALESCE((  
                                        SELECT
                                            json_agg(_note.text)
                                        FROM "core_backend_note" _note
                                        WHERE _note.booking_id = booking.id
                                    ), '[]'::JSON)
                                ) AS note
                            ) AS notes_string
                        ), ''),
                        'contacts', _company_booking_contacts,
                        'authorized', COALESCE((  
                            SELECT json_agg((True)) -> 0
                            FROM "core_backend_authorization_events" _authorization_events
                                INNER JOIN "core_backend_authorization" _authorization
                                    ON _authorization_events.authorization_id = _authorization.id and _authorization.status = 'ACCEPTED'
                            WHERE _authorization_events.event_id = event.id
                        ), '[]'::JSON),
                        'auth_by', COALESCE((  
                            SELECT json_agg(CONCAT(_user.first_name, ' ', _user.last_name)) -> 0
                            FROM "core_backend_authorization_events" _authorization_events
                                INNER JOIN "core_backend_authorization" _authorization
                                    ON _authorization_events.authorization_id = _authorization.id and _authorization.status = 'ACCEPTED'
                                INNER JOIN "core_backend_payer" _payer
                                    ON _payer.id = _authorization.authorizer_id
                                INNER JOIN "core_backend_user" _user
                                    ON _user.id = _payer.user_id
                            WHERE _authorization_events.event_id = event.id
                        ), '[]'::JSON),
                        'language', COALESCE(_language.name),
                        'price', COALESCE(
                            (
                                %s
                                WHERE 
                                    _rate.company_id = _payer_companies.id
                                    AND REPLACE(REPLACE(_extra_rate.data::text, '\"', ''), '\\', '') = _language.name
                                    AND _rate.is_deleted = False
                                    AND booking.service_root_id = _rate.root_id
                                LIMIT 1
                            ),
                            (
                                %s
                                WHERE 
                                    _rate.company_id = _payer_companies.id
                                    AND POSITION('Common Languages' IN REPLACE(REPLACE(_extra_rate.data::text, '\"', ''), '\\', '')) > 0
                                    AND _language.common = TRUE
                                    AND _rate.is_deleted = False
                                    AND booking.service_root_id = _rate.root_id
                                LIMIT 1    
                            ),
                            (
                                %s
                                WHERE 
                                    _rate.company_id = _payer_companies.id
                                    AND POSITION('Rare Languages' IN REPLACE(REPLACE(_extra_rate.data::text, '\"', ''), '\\', '')) > 0
                                    AND _language.common = FALSE
                                    AND _rate.is_deleted = False
                                    AND booking.service_root_id = _rate.root_id
                                LIMIT 1
                            ),
                            (
                                %s
                                WHERE
                                    _rate.company_id = _payer_companies.id
                                    AND POSITION('All Languages' IN REPLACE(REPLACE(_extra_rate.data::text, '\"', ''), '\\', '')) > 0
                                    AND _rate.is_deleted = False
                                    AND booking.service_root_id = _rate.root_id
                                LIMIT 1
                            ),
                            (
                                %s
                                WHERE 
                                    REPLACE(REPLACE(_extra_rate.data::text, '\"', ''), '\\', '') = _language.name
                                    AND _rate.is_deleted = False
                                    AND booking.service_root_id = _rate.root_id
                                    AND _rate.global_setting_id = 1
                                LIMIT 1
                            ),
                            (
                                %s
                                WHERE 
                                    POSITION('Common Languages' IN REPLACE(REPLACE(_extra_rate.data::text, '\"', ''), '\\', '')) > 0
                                    AND _language.common = TRUE
                                    AND _rate.is_deleted = False
                                    AND booking.service_root_id = _rate.root_id
                                    AND _rate.global_setting_id = 1
                                LIMIT 1
                            ),
                            (
                                %s
                                WHERE 
                                    POSITION('Rare Languages' IN REPLACE(REPLACE(_extra_rate.data::text, '\"', ''), '\\', '')) > 0 
                                    AND _language.common = FALSE
                                    AND _rate.is_deleted = FALSE
                                    AND booking.service_root_id = _rate.root_id
                                    AND _rate.global_setting_id = 1
                                LIMIT 1
                            ),
                            (
                                %s
                                WHERE 
                                    POSITION('All Languages' IN REPLACE(REPLACE(_extra_rate.data::text, '\"', ''), '\\', '')) > 0
                                    AND _rate.is_deleted = False
                                    AND booking.service_root_id = _rate.root_id
                                    AND _rate.global_setting_id = 1
                                LIMIT 1
                            )
                        )
                    )::jsonb ||
                    COALESCE((
                        SELECT json_object_agg(extra.key, REPLACE(REPLACE(extra.data::text, '\"', ''), '\\', ''))
                        FROM "core_backend_extra" extra
                        WHERE extra.parent_ct_id = %s AND extra.parent_id = event.id
                    )::jsonb, '{}'::jsonb)) AS json_data,
                    ROW_NUMBER() OVER (PARTITION BY event.id ORDER BY %s %s NULLS LAST) AS rn
                FROM "core_backend_event" event
                    LEFT JOIN "core_backend_booking" booking
                        ON booking.id = event.booking_id
                    LEFT JOIN "core_backend_booking_companies" booking_companies
                        ON booking_companies.booking_id = booking.id
                    LEFT JOIN "core_backend_company" company
                        ON company.id = booking_companies.company_id
                    LEFT JOIN "core_backend_booking_services" booking_services
                        ON booking_services.booking_id = booking.id
                    LEFT JOIN "core_backend_service" service
                        ON service.id = booking_services.service_id
                    LEFT JOIN "core_backend_provider" provider
                        ON provider.id = service.provider_id
                    LEFT JOIN "core_backend_user" provider_user
                        ON provider_user.id = provider.user_id
                    LEFT JOIN "core_backend_event_affiliates" event_affiliates
                        ON event_affiliates.event_id = event.id
                    LEFT JOIN "core_backend_affiliation" affiliation
                        ON affiliation.id = event_affiliates.affiliation_id
                    LEFT JOIN "core_backend_recipient" recipient
                        ON recipient.id = affiliation.recipient_id
                    LEFT JOIN "core_backend_user" recipient_user
                        ON recipient_user.id = recipient.user_id
                    LEFT JOIN "core_backend_event_agents" event_agents
                        ON event_agents.event_id = event.id
                    LEFT JOIN "core_backend_agent" agent
                        ON agent.id = event_agents.agent_id
                    LEFT JOIN "core_backend_event_affiliates" _event_affiliates
                        ON _event_affiliates.event_id = event.id
                    LEFT JOIN "core_backend_affiliation" _affiliations
                        ON _affiliations.id = _event_affiliates.affiliation_id
                    LEFT JOIN "core_backend_recipient" _recipients_affiliates
                        ON _recipients_affiliates.id = _affiliations.recipient_id
                    LEFT JOIN "core_backend_user" _users_affiliates
                        ON _users_affiliates.id = _recipients_affiliates.user_id
                    LEFT JOIN "core_backend_user_contacts" _users_affiliates_user_contacts
                        ON _users_affiliates_user_contacts.user_id = _users_affiliates.id
                    LEFT JOIN "core_backend_contact" _contact_affiliates
                        ON _contact_affiliates.id = _users_affiliates_user_contacts.contact_id
                    LEFT JOIN "core_backend_location" _location_affiliates
                        ON _location_affiliates.id = _users_affiliates.location_id
                    LEFT JOIN "core_backend_report" _reports
                        ON _reports.event_id = event.id
                    LEFT JOIN "core_backend_company" _payer_companies
                        ON _payer_companies.id = event.payer_company_id
                    LEFT JOIN "core_backend_company_locations" _payer_companies_locations_bridge
                        ON _payer_companies_locations_bridge.company_id = _payer_companies.id
                    LEFT JOIN "core_backend_location" _payer_companies_locations
                        ON _payer_companies_locations.id = _payer_companies_locations_bridge.location_id
                    LEFT JOIN "core_backend_event_agents" _event_agents
                        ON _event_agents.event_id = event.id
                    LEFT JOIN "core_backend_agent" _agents
                        ON _agents.id = _event_agents.agent_id
                    LEFT JOIN "core_backend_user" _users_agents
                        ON _users_agents.id = _agents.user_id
                    LEFT JOIN "core_backend_company_locations" _company_booking_locations_bridge
                        ON _company_booking_locations_bridge.company_id = company.id
                    LEFT JOIN "core_backend_location" _company_booking_locations
                        ON _company_booking_locations.id = _company_booking_locations_bridge.location_id
                    LEFT JOIN "core_backend_company_contacts" _company_booking_contacts_bridge
                        ON _company_booking_contacts_bridge.company_id = company.id
                    LEFT JOIN "core_backend_contact" _company_booking_contacts
                        ON _company_booking_contacts.id = _company_booking_contacts_bridge.contact_id
                    LEFT JOIN "core_backend_serviceroot" _booking_serviceroot
                        ON _booking_serviceroot.id = booking.service_root_id
                    LEFT JOIN "core_backend_booking_operators" _booking_operators_bridge
                        ON _booking_operators_bridge.booking_id = booking.id
                    LEFT JOIN "core_backend_operator" _booking_operator
                        ON _booking_operator.id = _booking_operators_bridge.operator_id
                    LEFT JOIN "core_backend_user" _booking_user_operator
                        ON _booking_user_operator.id = _booking_operator.user_id
                    LEFT JOIN "core_backend_extra" _extra_booking
                        ON _extra_booking.parent_id = booking.id and _extra_booking.key = 'target_language_alpha3'
                    LEFT JOIN "core_backend_language" _language
                        ON _language.alpha3 = REPLACE(REPLACE(_extra_booking.data::text, '\"', ''), '\\', '')
                WHERE %s
                ORDER BY %s %s NULLS LAST
                %s
            ) sub
            WHERE sub.rn = 1
        ) result
    """ % (
        query_price,
        query_price,
        query_price,
        query_price,
        query_price,
        query_price,
        query_price,
        query_price,
        parent_ct_id,
        field_to_sort,
        order_to_sort,
        where_conditions,
        field_to_sort,
        order_to_sort,
        limit_statement
    )

        cursor.execute(query, params)
        result = cursor.fetchone()
        if len(result) == 1:
            return result[0]

        return []