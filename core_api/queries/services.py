class ApiSpecialSqlServices:
    @staticmethod
    def get_service_sql_ct_id(cursor):
        query = """
            SELECT
                id
            FROM "django_content_type" content_type
            WHERE app_label = 'core_backend' AND model = 'service'
        """

        cursor.execute(query, [id])
        result = cursor.fetchone()
        if result is not None:
            return result[0]

        return None
    
    @staticmethod
    def get_service_sql_where_clause(id, limit, offset, root, parent_ct_id, source_language_alpha3, target_language_alpha3):
        params = []
        limit_statement = ''
        where_conditions = 'service.is_deleted = FALSE'

        if id is not None:
            where_conditions += ' AND service.id = %s'
            params.append(id)
        
        if root is not None:
            where_conditions += ' AND service.root_id = %s'
            params.append(root)
            
        if source_language_alpha3 is not None:
            where_conditions += ' AND EXISTS ( SELECT 1 FROM "core_backend_extra" extra WHERE extra.parent_ct_id = %s AND extra.parent_id = service.id AND extra.key = %s AND extra.data::text LIKE %s)'
            params.append(parent_ct_id)
            params.append('source_language_alpha3')
            params.append(f'%{source_language_alpha3}%')
            
        if target_language_alpha3 is not None:
            where_conditions += ' AND EXISTS ( SELECT 1 FROM "core_backend_extra" extra WHERE extra.parent_ct_id = %s AND extra.parent_id = service.id AND extra.key = %s AND extra.data::text LIKE %s)'
            params.append(parent_ct_id)
            params.append('target_language_alpha3')
            params.append(f'%{target_language_alpha3}%')

        if limit is not None and limit > 0 and offset is not None and offset >= 0:
            limit_statement = 'LIMIT %s OFFSET %s'
            params.append(limit)
            params.append(offset)

        return params, where_conditions, limit_statement
    
    @staticmethod
    def get_service_sql(cursor, id, limit, offset, root, source, target):
        parent_ct_id = ApiSpecialSqlServices.get_service_sql_ct_id(cursor)
        params, where_conditions, limit_statement = ApiSpecialSqlServices.get_service_sql_where_clause(id, limit, offset, root, parent_ct_id, source, target)
        
        query = """--sql
        SELECT json_agg(_query_result.json_data) AS result FROM (
                SELECT
                    (json_build_object(
                        'id', service.id,
                        'bill_amount', service.bill_amount,
                        'bill_rate', service.bill_rate,
                        'bill_min_payment', service.bill_min_payment,
                        'bill_rate_type', service.bill_rate_type,
                        'bill_no_show_fee', service.bill_no_show_fee,
                        'bill_rate_minutes_threshold', service.bill_rate_minutes_threshold,
                        'is_deleted', service.is_deleted,
                        'root', COALESCE((
                            SELECT 
                                json_agg(json_build_object(
                                    'id', _serviceroot.id,
                                    'name', _serviceroot.name,
                                    'description', _serviceroot.description,
                                    'is_deleted', _serviceroot.is_deleted,
                                    'categories', (
                                        SELECT json_agg(json_build_object(
                                            'id', _categories.id,
                                            'name', _categories.name,
                                            'description', _categories.description,
                                            'is_deleted', _categories.is_deleted
                                        ))
                                        FROM "core_backend_serviceroot_categories" _serviceroot_categories
                                            INNER JOIN "core_backend_category" _categories
                                                ON _categories.id = _serviceroot_categories.category_id AND _categories.is_deleted = FALSE
                                        WHERE _serviceroot_categories.serviceroot_id = _serviceroot.id
                                    )
                                ))
                            FROM "core_backend_serviceroot" _serviceroot
                            WHERE _serviceroot.id = service.root_id AND _serviceroot.is_deleted = FALSE
                        ), '{}'),
                        'provider', COALESCE((
                            SELECT
                                json_build_object(
                                    'id', _provider.id,
                                    'first_name', _user.first_name,
                                    'last_name', _user.last_name,
                                    'title', _user.title,
                                    'suffix', _user.suffix,
                                    'user_id', _user.id,
                                    'is_deleted', _provider.is_deleted,
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
                                        WHERE location.id = _user.location_id
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
                                        WHERE _user_contact.user_id = _user.id
                                    ), '[]'::json),
                                    'notes', COALESCE((
                                        SELECT
                                            json_agg(
                                                json_build_object(
                                                'id', _provider_note.id,
                                                'created_by', _provider_note.created_by_id,
                                                'created_by_first_name', _note_created_by.first_name,
                                                'created_by_last_name', _note_created_by.last_name,
                                                'text', _provider_note.text,
                                                'is_deleted', _provider_note.is_deleted,
                                                'created_at', _provider_note.created_at,
                                                'last_updated_at', _provider_note.last_updated_at,
                                                'booking', _provider_note.booking_id,
                                                'company', _provider_note.company_id,
                                                'notification', _provider_note.notification_id,
                                                'payer', _provider_note.payer_id,
                                                'provider', _provider_note.provider_id,
                                                'recipient', _provider_note.recipient_id
                                                )
                                            )
                                        FROM "core_backend_note" _provider_note
                                            INNER JOIN "core_backend_user" _note_created_by
                                                ON _provider_note.created_by_id = _note_created_by.id
                                        WHERE _provider_note.provider_id = _provider.id AND _provider_note.is_deleted=FALSE
                                    ), '[]'::JSON)
                                )
                            FROM "core_backend_provider" _provider
                                INNER JOIN "core_backend_user" _user
                                    ON _user.id = _provider.user_id AND _user.is_deleted = FALSE
                            WHERE _provider.id = service.provider_id AND _provider.is_deleted = FALSE
                        ), '{}')
                    )::jsonb ||
                    COALESCE((
                        SELECT
                            json_object_agg(extra.key, REPLACE(REPLACE(extra.data::text, '\"', ''), '\\', ''))
                        FROM "core_backend_extra" extra
                        WHERE extra.parent_ct_id = %s AND extra.parent_id = service.id
                    )::jsonb, '{}'::jsonb)) AS json_data
                FROM "core_backend_service" service
                WHERE %s
                ORDER BY id desc NULLS LAST
                %s
            ) _query_result
        """ % (parent_ct_id, where_conditions, limit_statement)
        
        cursor.execute(query, params)
        result = cursor.fetchone()
        if len(result) == 1:
            return result[0]

        return []
    
    @staticmethod
    def get_service_count_sql(cursor, id, root, source, target):
        parent_ct_id = ApiSpecialSqlServices.get_service_sql_ct_id(cursor)
        params, where_conditions, _ = ApiSpecialSqlServices.get_service_sql_where_clause(id, None, None, root, parent_ct_id, source, target)

        query = """--sql
            SELECT
               COUNT(DISTINCT service.id)
            FROM "core_backend_service" service
            WHERE %s
        """ % where_conditions

        cursor.execute(query, params)
        result = cursor.fetchone()
        if len(result) == 1:
            return result[0]

        return 0