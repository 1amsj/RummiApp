from core_api.queries.services import ApiSpecialSqlServices

class ApiSpecialSqlProviders():
    @staticmethod
    def get_provider_sql_ct_id(cursor):
        query = """--sql
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
    def get_provider_sql_where_clause(
        id,
        limit,
        offset,
        first_name,
        last_name,
        phone,
        email
    ):
        params = []
        limit_statement = ''
        where_conditions = 'provider.is_deleted = FALSE'

        if id is not None:
            where_conditions += ' AND provider.id = %s'
            params.append(id)
            
        if first_name is not None:
            where_conditions += ' AND POSITION(%s IN provider_user.first_name) > 0'
            params.append(first_name)
            
        if last_name is not None:
            where_conditions += ' AND POSITION(%s IN provider_user.last_name) > 0'
            params.append(last_name)
            
        if phone is not None:
            where_conditions += """
                AND EXISTS (
                    SELECT 1
                    FROM "core_backend_user_contacts" _user_contact
                    INNER JOIN "core_backend_contact" _contact ON _user_contact.contact_id = _contact.id
                    WHERE _user_contact.user_id = provider_user.id AND _contact.phone ILIKE %s AND _contact.is_deleted = FALSE
                )"""
            params.append(f'%{phone}%')

        if email is not None:
            where_conditions += ' AND POSITION(%s IN provider_user.email) > 0'
            params.append(email)    

        if limit is not None and limit > 0 and offset is not None and offset >= 0:
            limit_statement = 'LIMIT %s OFFSET %s'
            params.append(limit)
            params.append(offset)

        return params, where_conditions, limit_statement
    
    @staticmethod
    def get_provider_sql(
        cursor,
        id,
        limit,
        offset,
        first_name,
        last_name,
        email,
        phone,
        field_to_sort,
        order_to_sort
    ):
        parent_ct_id = ApiSpecialSqlProviders.get_provider_sql_ct_id(cursor)
        parent_service_ct_id = ApiSpecialSqlServices.get_service_sql_ct_id(cursor)
        params, where_conditions, limit_statement = ApiSpecialSqlProviders.get_provider_sql_where_clause(
            id,
            limit,
            offset,
            first_name,
            last_name, 
            email,
            phone
        )

        query = """--sql
            SELECT json_agg(_query_result.json_data) AS result FROM (
                SELECT
                    (json_build_object(
                        'id', provider.id,
                        'user_id', provider.user_id,
                        'is_deleted', provider.is_deleted,
                        'first_name', provider_user.first_name,
                        'last_name', provider_user.last_name,
                        'email', provider_user.email,
                        'title', provider_user.title,
                        'suffix', provider_user.suffix,
                        'contacts', COALESCE((
                            SELECT 
                                json_agg(json_build_object(
                                    'id', _contact.id,
                                    'is_deleted', _contact.is_deleted,
                                    'email', _contact.email,
                                    'phone', _contact.phone,
                                    'fax', _contact.fax,
                                    'phone_context', _contact.phone_context,
                                    'email_context', _contact.email_context,
                                    'fax_context', _contact.fax_context
                                )
                            )
                            FROM "core_backend_user_contacts" _user_contact
                            INNER JOIN "core_backend_contact" _contact
                                ON _user_contact.contact_id = _contact.id
                            WHERE _user_contact.user_id = provider_user.id AND _contact.is_deleted=FALSE
                        ), '[]'::json),
                        'location', (
                            SELECT 
                                json_build_object(
                                    'id', _location.id,
                                    'is_deleted', _location.is_deleted,
                                    'country', _location.country,
                                    'address', _location.address,
                                    'city', _location.city,
                                    'state', _location.state,
                                    'zip', _location.zip,
                                    'unit_number', _location.unit_number
                                )
                            FROM "core_backend_location" _location
                            WHERE _location.id = provider_user.location_id AND _location.is_deleted=FALSE
                        ),
                        'notes', COALESCE((
                            SELECT
                                json_agg(json_build_object(
                                    'id', _provider_note.id,
                                    'is_deleted', _provider_note.is_deleted,
                                    'created_by', _provider_note.created_by_id,
                                    'created_by_first_name', _note_created_by.first_name,
                                    'created_by_last_name', _note_created_by.last_name,
                                    'text', _provider_note.text,
                                    'created_at', _provider_note.created_at,
                                    'last_updated_at', _provider_note.last_updated_at,
                                    'provider', _provider_note.provider_id
                                ))
                            FROM "core_backend_note" _provider_note
                                INNER JOIN "core_backend_user" _note_created_by
                                    ON _provider_note.created_by_id = _note_created_by.id
                            WHERE _provider_note.provider_id = provider.id AND _provider_note.is_deleted=FALSE
                        ), '[]'::JSON),
                        'services', COALESCE((
                            SELECT
                                json_agg(json_build_object(
                                    'id', _service.id,
                                    'is_deleted', _service.is_deleted,
                                    'bill_rate', _service.bill_rate,
                                    'bill_amount', _service.bill_amount,
                                    'bill_min_payment', _service.bill_min_payment,
                                    'bill_rate_type', _service.bill_rate_type,
                                    'bill_no_show_fee', _service.bill_no_show_fee,
                                    'bill_rate_minutes_threshold', _service.bill_rate_minutes_threshold,
                                    'root', (
                                        SELECT
                                            json_build_object(
                                                'id', _root.id,
                                                'is_deleted', _root.is_deleted,
                                                'name', _root.name,
                                                'description', _root.description
                                            )
                                        FROM "core_backend_serviceroot" _root
                                        WHERE _root.id = _service.root_id AND _root.is_deleted=FALSE
                                    )
                                )::jsonb ||
                                COALESCE((
                                    SELECT
                                        json_object_agg(extra.key, REPLACE(REPLACE(extra.data::text, '"', ''), '\\', ''))
                                    FROM "core_backend_extra" extra
                                    WHERE extra.parent_ct_id = %s AND extra.parent_id = _service.id
                                )::jsonb, '{}'::jsonb))
                            FROM "core_backend_service" _service
                            WHERE _service.provider_id = provider.id AND _service.is_deleted = FALSE
                        )::jsonb, '[]'::jsonb),
                        'certifications', COALESCE((
                            SELECT
                                REPLACE(REPLACE(REPLACE(extra.data::text, '\"[', '['), ']\"', ']'), '\\', '')
                            FROM "core_backend_extra" extra
                            WHERE extra.parent_ct_id = %s AND extra.parent_id = provider.id AND extra.key = 'certifications'
                        )::jsonb, '[]'::jsonb),
                        'service_areas', COALESCE((
                            SELECT
                                json_agg(json_build_object(
                                    'id', _service_area.id,
                                    'is_deleted', _service_area.is_deleted,
                                    'country', _service_area.country,
                                    'state', _service_area.state,
                                    'county', _service_area.county,
                                    'city', _service_area.city,
                                    'zip', _service_area.zip
                                ))
                            FROM "core_backend_servicearea" _service_area
                            WHERE _service_area.provider_id = provider.id AND _service_area.is_deleted=FALSE
                        ), '[]'::json)
                    )::jsonb ||
                    COALESCE((
                        SELECT
                            json_object_agg(extra.key, REPLACE(REPLACE(extra.data::text, '\"', ''), '\\', ''))
                        FROM "core_backend_extra" extra
                        WHERE extra.parent_ct_id = %s AND extra.parent_id = provider.id AND extra.key != 'certifications'
                    )::jsonb, '{}'::jsonb)) AS json_data
                FROM "core_backend_provider" provider
                    INNER JOIN "core_backend_user" provider_user
                        ON provider.user_id = provider_user.id
                WHERE %s
                ORDER BY %s %s NULLS LAST, provider.id
                %s
            ) _query_result
        """ % (parent_service_ct_id, parent_ct_id, parent_ct_id, where_conditions, field_to_sort, order_to_sort, limit_statement)

        cursor.execute(query, params)
        result = cursor.fetchone()
        if len(result) == 1:
            return result[0]

        return []
    
    @staticmethod
    def get_provider_count_sql(
        cursor,
        id,
        first_name,
        last_name,
        email,
        phone
    ):
        params, where_conditions, _ = ApiSpecialSqlProviders.get_provider_sql_where_clause(
            id,
            None,
            None,
            first_name,
            last_name, 
            email,
            phone
            
        )

        query = """--sql
            SELECT
               COUNT(DISTINCT provider.id)
            FROM "core_backend_provider" provider
                INNER JOIN "core_backend_user" provider_user
                    ON provider.user_id = provider_user.id
            WHERE %s
        """ % where_conditions

        cursor.execute(query, params)
        result = cursor.fetchone()
        if len(result) == 1:
            return result[0]

        return 0