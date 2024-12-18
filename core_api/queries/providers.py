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
    ):
        params = []
        limit_statement = ''
        where_conditions = 'provider.is_deleted = FALSE'

        if id is not None:
            where_conditions += ' AND provider.id = %s'
            params.append(id)

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
        field_to_sort,
        order_to_sort
    ):
        parent_ct_id = ApiSpecialSqlProviders.get_provider_sql_ct_id(cursor)
        parent_service_ct_id = ApiSpecialSqlServices.get_service_sql_ct_id(cursor)
        params, where_conditions, limit_statement = ApiSpecialSqlProviders.get_provider_sql_where_clause(
            id,
            limit,
            offset
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
                                    'id', _contacts.id,
                                    'is_deleted', _contacts.is_deleted,
                                    'email', _contacts.email,
                                    'phone', _contacts.phone,
                                    'fax', _contacts.fax,
                                    'phone_context', _contacts.phone_context,
                                    'email_context', _contacts.email_context,
                                    'fax_context', _contacts.fax_context
                                )
                            )
                            FROM "core_backend_user_contacts" _user_contacts
                            INNER JOIN "core_backend_contact" _contacts
                                ON _user_contacts.contact_id = _contacts.id
                            WHERE _user_contacts.user_id = provider_user.id AND _contacts.is_deleted=FALSE
                        ), '[]'::json),
                        'location', (
                            SELECT 
                                json_build_object(
                                    'id', _locations.id,
                                    'is_deleted', _locations.is_deleted,
                                    'country', _locations.country,
                                    'address', _locations.address,
                                    'city', _locations.city,
                                    'state', _locations.state,
                                    'zip', _locations.zip,
                                    'unit_number', _locations.unit_number
                                )
                            FROM "core_backend_location" _locations
                            WHERE _locations.id = provider_user.location_id AND _locations.is_deleted=FALSE
                        ),
                        'notes', COALESCE((
                            SELECT
                                json_agg(json_build_object(
                                    'id', _provider_notes.id,
                                    'is_deleted', _provider_notes.is_deleted,
                                    'created_by', _provider_notes.created_by_id,
                                    'created_by_first_name', _note_created_by.first_name,
                                    'created_by_last_name', _note_created_by.last_name,
                                    'text', _provider_notes.text,
                                    'created_at', _provider_notes.created_at,
                                    'last_updated_at', _provider_notes.last_updated_at,
                                    'provider', _provider_notes.provider_id
                                ))
                            FROM "core_backend_note" _provider_notes
                                INNER JOIN "core_backend_user" _note_created_by
                                    ON _provider_notes.created_by_id = _note_created_by.id
                            WHERE _provider_notes.provider_id = provider.id AND _provider_notes.is_deleted=FALSE
                        ), '[]'::JSON),
                        'services', COALESCE((
                            SELECT
                                json_agg(json_build_object(
                                    'id', _services.id,
                                    'is_deleted', _services.is_deleted,
                                    'bill_rate', _services.bill_rate,
                                    'bill_amount', _services.bill_amount,
                                    'bill_min_payment', _services.bill_min_payment,
                                    'bill_rate_type', _services.bill_rate_type,
                                    'bill_no_show_fee', _services.bill_no_show_fee,
                                    'bill_rate_minutes_threshold', _services.bill_rate_minutes_threshold,
                                    'root', (
                                        SELECT
                                            json_build_object(
                                                'id', _root.id,
                                                'is_deleted', _root.is_deleted,
                                                'name', _root.name,
                                                'description', _root.description
                                            )
                                        FROM "core_backend_serviceroot" _root
                                        WHERE _root.id = _services.root_id AND _root.is_deleted=FALSE
                                    )
                                )::jsonb ||
                                COALESCE((
                                    SELECT
                                        json_object_agg(extra.key, REPLACE(REPLACE(extra.data::text, '\"', ''), '\\', ''))
                                    FROM "core_backend_extra" extra
                                    WHERE extra.parent_ct_id = %s AND extra.parent_id = _services.id
                                )::jsonb, '{}'::jsonb))
                            FROM "core_backend_service" _services
                            WHERE _services.provider_id = provider.id AND _services.is_deleted = FALSE
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
                                    'id', _service_areas.id,
                                    'is_deleted', _service_areas.is_deleted,
                                    'country', _service_areas.country,
                                    'state', _service_areas.state,
                                    'county', _service_areas.county,
                                    'city', _service_areas.city,
                                    'zip', _service_areas.zip
                                ))
                            FROM "core_backend_servicearea" _service_areas
                            WHERE _service_areas.provider_id = provider.id AND _service_areas.is_deleted=FALSE
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
    ):
        params, where_conditions, _ = ApiSpecialSqlProviders.get_provider_sql_where_clause(
            id,
            None,
            None,
        )

        query = """--sql
            SELECT
               COUNT(DISTINCT provider.id)
            FROM "core_backend_provider" provider
            WHERE %s
        """ % where_conditions

        cursor.execute(query, params)
        result = cursor.fetchone()
        if len(result) == 1:
            return result[0]

        return 0