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
    def get_booking_sql_where_clause(id, limit, offset):
        params = []
        limit_statement = ''
        where_conditions = 'booking.is_deleted = FALSE'

        if id is not None:
            where_conditions += ' AND booking.id = %s'
            params.append(id)

        if limit is not None and limit > 0 and offset is not None and offset >= 0:
            limit_statement = 'LIMIT %s OFFSET %s'
            params.append(limit)
            params.append(offset)

        return params, where_conditions, limit_statement
    
    @staticmethod
    def get_booking_sql(cursor, id, limit, offset):
        parent_ct_id = ApiSpecialSqlBookings.get_booking_sql_ct_id(cursor)
        params, where_conditions, limit_statement = ApiSpecialSqlBookings.get_booking_sql_where_clause(id, limit, offset)

        query = """
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
                            WHERE _booking_services.booking_id = booking.id
                        ), '[]'::JSON),
                        'companies', COALESCE((
                            SELECT
                                json_agg(json_build_object(
                                    'id', _companies.id,
                                    'name', _companies.name,
                                    'is_deleted', _companies.is_deleted,
                                    'type', _companies.type
                                ))
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
                                    'user_id', _users.id
                                ))
                            FROM "core_backend_booking_operators" _booking_operators
                                INNER JOIN "core_backend_operator" _operators
                                    ON _operators.id = _booking_operators.operator_id
                                INNER JOIN "core_backend_user" _users
                                    ON _users.id = _operators.user_id
                            WHERE _booking_operators.booking_id = booking.id
                        ), '[]'::JSON)
                    )::jsonb ||
                    (
                        SELECT
                            json_object_agg(extra.key, extra.data)
                        FROM "core_backend_extra" extra
                        WHERE extra.parent_ct_id = %s AND extra.parent_id=booking.id
                    )::jsonb) AS json_data
                FROM "core_backend_booking" booking
                WHERE %s
                ORDER BY booking.public_id DESC, booking.id
                %s
            ) _query_result
        """ % (parent_ct_id, where_conditions, limit_statement)

        cursor.execute(query, params)
        result = cursor.fetchone()
        if len(result) == 1:
            return result[0]

        return []
    
    @staticmethod
    def get_booking_count_sql(cursor, id):
        params, where_conditions, _ = ApiSpecialSqlBookings.get_booking_sql_where_clause(id, None, None)

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