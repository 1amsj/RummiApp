class ApiSpecialSqlEvents():
    @staticmethod
    def get_event_sql_ct_id(cursor):
        query = """
            SELECT
                id
            FROM "django_content_type" content_type
            WHERE app_label = 'core_backend' AND model = 'event'
        """

        cursor.execute(query, [id])
        result = cursor.fetchone()
        if result is not None:
            return result[0]

        return None

    @staticmethod
    def get_event_sql_where_clause(id, limit, offset, start_at, end_at, status, recipient_id, agent_id):
        params = []
        limit_statement = ''
        where_conditions = 'event.is_deleted = FALSE'

        if id is not None:
            where_conditions += ' AND event.id = %s'
            params.append(id)
            
        if start_at is not None:
            where_conditions += ' AND event.start_at >= %s'
            params.append(start_at)
            
        if end_at is not None:
            where_conditions += ' AND event.end_at <= %s'
            params.append(end_at)
            
        if status is not None:
            where_conditions += ' AND booking.status = %s'
            params.append(status)
            
        if recipient_id is not None and agent_id is None:
            where_conditions += ' AND recipient.id = %s'
            params.append(recipient_id)
        
        if agent_id is not None and recipient_id is None:
            where_conditions += ' AND agent.id = %s'
            params.append(agent_id)
            
        if recipient_id is not None and agent_id is not None:
            where_conditions += ' AND (recipient.id = %s OR agent.id = %s)'
            params.append(recipient_id)
            params.append(agent_id)

        if limit is not None and limit > 0 and offset is not None and offset >= 0:
            limit_statement = 'LIMIT %s OFFSET %s'
            params.append(limit)
            params.append(offset)

        return params, where_conditions, limit_statement
    
    @staticmethod
    def get_event_sql(cursor, id, limit, offset, start_at, end_at, status, recipient_id, agent_id):
        parent_ct_id = ApiSpecialSqlEvents.get_event_sql_ct_id(cursor)
        params, where_conditions, limit_statement = ApiSpecialSqlEvents.get_event_sql_where_clause(id, limit, offset, start_at, end_at, status, recipient_id, agent_id)

        query = """--sql
            SELECT json_agg(_query_result.json_data) AS result FROM (
                SELECT
                    (json_build_object(
                        'id', event.id,
                        'is_deleted', event.is_deleted,
                        'start_at', event.start_at,
                        'end_at', event.end_at,
                        'arrive_at', event.arrive_at,
                        'description', event.description,
                        'booking', (
                            SELECT
                                json_build_object(
                                    'id', _booking.id,
                                    'status', _booking.status,
                                    'parent_id', _booking.parent_id,
                                    'public_id', _booking.public_id,
                                    'created_at', _booking.created_at,
                                    'is_deleted', _booking.is_deleted,
                                    'business_id', _booking.business_id,
                                    'created_by_id', _booking.created_by_id,
                                    'service_root_id', _booking.service_root_id,
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
                                                        )
                                                    FROM "core_backend_provider" _providers
                                                        INNER JOIN "core_backend_user" _users
                                                            ON _users.id = _providers.user_id
                                                    WHERE _providers.id = _services.provider_id
                                                )
                                            ))
                                        FROM "core_backend_booking_services" _booking_services
                                            INNER JOIN "core_backend_service" _services
                                                ON _services.id = _booking_services.service_id
                                        WHERE _booking_services.booking_id = _booking.id
                                    ), '[]'::JSON),
                                    'companies', COALESCE((
                                        SELECT
                                            json_agg(json_build_object(
                                                'id', _companies.id,
                                                'name', _companies.name,
                                                'is_deleted', _companies.is_deleted,
                                                'type', _companies.type,
                                                'agents', COALESCE((
                                                    SELECT
                                                        json_agg(json_build_object(
                                                            'id', _agents.id,
                                                            'first_name', _users.first_name,
                                                            'last_name', _users.last_name,
                                                            'user_id', _users.id
                                                        ))
                                                    FROM "core_backend_agent_companies" _agent_companies
                                                        INNER JOIN "core_backend_agent" _agents
                                                            ON _agents.id = _agent_companies.agent_id
                                                        INNER JOIN "core_backend_user" _users
                                                            ON _users.id = _agents.user_id
                                                    WHERE _agent_companies.company_id = _companies.id
                                                ), '[]'::JSON)
                                            ))
                                        FROM "core_backend_booking_companies" _booking_companies
                                            INNER JOIN "core_backend_company" _companies
                                                ON _companies.id = _booking_companies.company_id
                                        WHERE _booking_companies.booking_id = _booking.id
                                    ), '[]'::JSON),
                                    'operators', COALESCE((
                                        SELECT
                                            json_agg(json_build_object(
                                                'id', _operators.id,
                                                'first_name', _users.first_name,
                                                'last_name', _users.last_name,
                                                'user_id', _users.id
                                            ))
                                        FROM "core_backend_booking_operators" _booking_operators
                                            INNER JOIN "core_backend_operator" _operators
                                                ON _operators.id = _booking_operators.operator_id
                                            INNER JOIN "core_backend_user" _users
                                                ON _users.id = _operators.user_id
                                        WHERE _booking_operators.booking_id = _booking.id
                                    ), '[]'::JSON)
                                )
                            FROM "core_backend_booking" _booking
                            WHERE _booking.id = event.booking_id
                        ),
                        'affiliates', COALESCE((
                            SELECT
                                json_agg(json_build_object(
                                    'id', _affiliations.id,
                                    'company', _affiliations.company_id,
                                    'is_deleted', _affiliations.is_deleted,
                                    'recipient', (
                                        SELECT
                                            json_build_object(
                                                'id', _recipients.id,
                                                'first_name', _users.first_name,
                                                'last_name', _users.last_name,
                                                'user_id', _users.id
                                            )
                                        FROM "core_backend_recipient" _recipients
                                            INNER JOIN "core_backend_user" _users
                                                ON _users.id = _recipients.user_id
                                        WHERE _recipients.id = _affiliations.recipient_id
                                    )
                                ))
                            FROM "core_backend_event_affiliates" _event_affiliates
                                INNER JOIN "core_backend_affiliation" _affiliations
                                    ON _affiliations.id = _event_affiliates.affiliation_id
                            WHERE _event_affiliates.event_id = event.id
                        ), '[]'::JSON),
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
                                ))
                            FROM "core_backend_report" _reports
                            WHERE _reports.event_id = event.id
                        ), '[]'::JSON)
                    )::jsonb ||
                    (
                        SELECT
                            json_object_agg(extra.key, extra.data)
                        FROM "core_backend_extra" extra
                        WHERE extra.parent_ct_id = %s AND extra.parent_id=event.id
                    )::jsonb) AS json_data
                FROM "core_backend_event" event
                    INNER JOIN "core_backend_booking" booking
                        ON booking.id = event.booking_id
                    INNER JOIN "core_backend_event_affiliates" event_affiliates
                        ON event_affiliates.event_id = event.id
                    INNER JOIN "core_backend_affiliation" affiliation
                        ON affiliation.id = event_affiliates.affiliation_id
                    INNER JOIN "core_backend_recipient" recipient
                        ON recipient.id = affiliation.recipient_id
                    INNER JOIN "core_backend_booking_companies" booking_companies
                        ON booking_companies.booking_id = booking.id
                    INNER JOIN "core_backend_company" company
                        ON company.id = booking_companies.company_id
                    INNER JOIN "core_backend_agent_companies" agent_companies
                        ON agent_companies.company_id = company.id
                    INNER JOIN "core_backend_agent" agent
                        ON agent.id = agent_companies.agent_id
                WHERE %s
                ORDER BY event.start_at DESC, event.id
                %s
            ) _query_result
        """ % (parent_ct_id, where_conditions, limit_statement)

        cursor.execute(query, params)
        result = cursor.fetchone()
        if len(result) == 1:
            return result[0]

        return []
    
    @staticmethod
    def get_event_count_sql(cursor, id, start_at, end_at, status, recipient_id, agent_id):
        params, where_conditions, _ = ApiSpecialSqlEvents.get_event_sql_where_clause(id, None, None, start_at, end_at, status, recipient_id, agent_id)

        query = """--sql
            SELECT
               COUNT(DISTINCT event.id)
            FROM "core_backend_event" event
                INNER JOIN "core_backend_booking" booking
                    ON booking.id = event.booking_id
                INNER JOIN "core_backend_event_affiliates" event_affiliates
                    ON event_affiliates.event_id = event.id
                INNER JOIN "core_backend_affiliation" affiliation
                    ON affiliation.id = event_affiliates.affiliation_id
                INNER JOIN "core_backend_recipient" recipient
                    ON recipient.id = affiliation.recipient_id
                INNER JOIN "core_backend_booking_companies" booking_companies
                    ON booking_companies.booking_id = booking.id
                INNER JOIN "core_backend_company" company
                    ON company.id = booking_companies.company_id
                INNER JOIN "core_backend_agent_companies" agent_companies
                    ON agent_companies.company_id = company.id
                INNER JOIN "core_backend_agent" agent
                    ON agent.id = agent_companies.agent_id
            WHERE %s
        """ % where_conditions

        cursor.execute(query, params)
        result = cursor.fetchone()
        if len(result) == 1:
            return result[0]

        return 0