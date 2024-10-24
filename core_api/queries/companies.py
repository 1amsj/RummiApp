class ApiSpecialSqlCompanies():
    
    @staticmethod
    def get_companies_sql_ct_id(cursor):
        query = """
            SELECT
                id
            FROM "django_content_type" content_type
            WHERE app_label = 'core_backend' AND model = 'company'
        """

        cursor.execute(query, [id])
        result = cursor.fetchone()
        if result is not None:
            return result[0]

        return None
    @staticmethod
    def get_company_sql_where_clause(id, name, type, send_method, on_hold, limit, offset):
        params = []
        limit_statement = ''
        where_conditions = 'company.is_deleted = FALSE'

        if id is not None:
            where_conditions += ' AND company.id = %s'
            params.append(id)

        if name is not None:
            where_conditions += ' AND company.name ILIKE %s'
            params.append(name)

        if type is not None:
            where_conditions += ' AND company.type = %s'
            params.append(type)

        if send_method is not None:
            where_conditions += ' AND company.send_method = %s'
            params.append(send_method)

        if on_hold is not None:
            where_conditions += ' AND company.on_hold = %s'
            params.append(on_hold)

        if limit is not None and limit > 0 and offset is not None and offset >= 0:
            limit_statement = 'LIMIT %s OFFSET %s'
            params.append(limit)
            params.append(offset)

        return params, where_conditions, limit_statement

    @staticmethod
    def get_company_sql(cursor, id, name, type, send_method, on_hold, limit, offset):
        params, where_conditions, limit_statement = ApiSpecialSqlCompanies.get_company_sql_where_clause(id, name, type, send_method, on_hold, limit, offset)

        query = """
            SELECT json_agg(row_to_json(_query_result)) AS result FROM (
                SELECT
                    company.id,
                    COALESCE((
                        SELECT
                            json_agg(row_to_json(_contacts))
                        FROM "core_backend_company_contacts" _company_contacts
                            INNER JOIN "core_backend_contact" _contacts
                                ON _contacts.id = _company_contacts.contact_id
                        WHERE _company_contacts.company_id = company.id AND _contacts.is_deleted=FALSE
                    ), '[]'::JSON) AS contacts,
                    COALESCE((
                        SELECT
                            json_agg(row_to_json(_locations))
                        FROM "core_backend_company_locations" _company_locations
                            INNER JOIN "core_backend_location" _locations
                                ON _locations.id = _company_locations.location_id
                        WHERE _company_locations.company_id = company.id AND _locations.is_deleted=FALSE
                    ), '[]'::JSON) AS locations,
                    COALESCE((
                        SELECT
                            json_agg(
                                json_build_object(
                                'id', _company_note.id,
                                'created_by', _company_note.created_by_id,
                                'created_by_first_name', _note_created_by.first_name,
                                'created_by_last_name', _note_created_by.last_name,
                                'text', _company_note.text,
                                'is_deleted', _company_note.is_deleted,
                                'created_at', _company_note.created_at,
                                'last_updated_at', _company_note.last_updated_at,
                                'booking', _company_note.booking_id,
                                'company', _company_note.company_id,
                                'notification', _company_note.notification_id,
                                'payer', _company_note.payer_id,
                                'provider', _company_note.provider_id,
                                'recipient', _company_note.recipient_id
                                )
                            )
                        FROM "core_backend_note" _company_note
                            INNER JOIN "core_backend_user" _note_created_by
                                ON _company_note.created_by_id = _note_created_by.id
                        WHERE _company_note.company_id = company.id AND _company_note.is_deleted=FALSE
                    ), '[]'::JSON) AS notes,
                    (
                        SELECT
                            json_build_object(
                            'id', _company.id,
                            'contacts', COALESCE((
                                SELECT
                                    json_agg(row_to_json(_contacts))
                                FROM "core_backend_company_contacts" _company_contacts
                                    INNER JOIN "core_backend_contact" _contacts
                                        ON _contacts.id = _company_contacts.contact_id
                                WHERE _company_contacts.company_id = _company.id AND _contacts.is_deleted=FALSE
                            ), '[]'::JSON),
                            'locations', COALESCE((
                                SELECT
                                    json_agg(row_to_json(_locations))
                                FROM "core_backend_company_locations" _company_locations
                                    INNER JOIN "core_backend_location" _locations
                                        ON _locations.id = _company_locations.location_id
                                WHERE _company_locations.company_id = _company.id AND _locations.is_deleted=FALSE
                            ), '[]'::JSON),
                            'notes',     COALESCE((
                                SELECT
                                    json_agg(
                                        json_build_object(
                                        'id', _company_note.id,
                                        'created_by', _company_note.created_by_id,
                                        'created_by_first_name', _note_created_by.first_name,
                                        'created_by_last_name', _note_created_by.last_name,
                                        'text', _company_note.text,
                                        'is_deleted', _company_note.is_deleted,
                                        'created_at', _company_note.created_at,
                                        'last_updated_at', _company_note.last_updated_at,
                                        'booking', _company_note.booking_id,
                                        'company', _company_note.company_id,
                                        'notification', _company_note.notification_id,
                                        'payer', _company_note.payer_id,
                                        'provider', _company_note.provider_id,
                                        'recipient', _company_note.recipient_id
                                        )
                                    )
                                FROM "core_backend_note" _company_note
                                    INNER JOIN "core_backend_user" _note_created_by
                                        ON _company_note.created_by_id = _note_created_by.id
                                WHERE _company_note.company_id = _company.id AND _company_note.is_deleted=FALSE
                            ), '[]'::JSON),
                            'parent_company_id', _company.parent_company_id,
                            'is_deleted', _company.is_deleted,
                            'name', _company.name,
                            'type', _company.type,
                            'send_method', _company.send_method,
                            'on_hold', _company.on_hold,
                            'aliases', _company.aliases
                            )
                        FROM "core_backend_company" _company
                        WHERE _company.id = company.parent_company_id
                    ) AS parent_company,
                    COALESCE((
                        SELECT
                            json_agg(row_to_json(_company_rate))
                        FROM "core_backend_rate" _company_rate
                        WHERE _company_rate.company_id = company.id AND _company_rate.is_deleted=FALSE
                    ), '[]'::JSON) AS rates,
                    COALESCE((
                        SELECT
                            json_agg(row_to_json(_company_relationship))
                        FROM "core_backend_companyrelationship" _company_relationship
                        WHERE _company_relationship.company_from_id = company.id AND _company_relationship.is_deleted=FALSE
                    ), '[]'::JSON) AS company_relationships_from,
                    company.is_deleted,
                    company.name,
                    company.type,
                    company.send_method,
                    company.on_hold,
                    company.aliases
                FROM "core_backend_company" company
                WHERE %s
                ORDER BY company.name, company.id
                %s
            ) _query_result
        """ % (where_conditions, limit_statement)

        cursor.execute(query, params)
        result = cursor.fetchone()
        if len(result) == 1:
            return result[0]

        return []

    @staticmethod
    def get_company_with_roles_sql(cursor, id, name, type, send_method, on_hold, limit, offset):
        params, where_conditions, limit_statement = ApiSpecialSqlCompanies.get_company_sql_where_clause(id, name, type, send_method, on_hold, limit, offset)

        query = """
            SELECT json_agg(row_to_json(_query_result)) AS result FROM (
                SELECT
                    company.id,
                    COALESCE((
                        SELECT
                            json_agg(row_to_json(_contacts))
                        FROM "core_backend_company_contacts" _company_contacts
                            INNER JOIN "core_backend_contact" _contacts
                                ON _contacts.id = _company_contacts.contact_id
                        WHERE _company_contacts.company_id = company.id AND _contacts.is_deleted=FALSE
                    ), '[]'::JSON) AS contacts,
                    COALESCE((
                        SELECT
                            json_agg(row_to_json(_locations))
                        FROM "core_backend_company_locations" _company_locations
                            INNER JOIN "core_backend_location" _locations
                                ON _locations.id = _company_locations.location_id
                        WHERE _company_locations.company_id = company.id AND _locations.is_deleted=FALSE
                    ), '[]'::JSON) AS locations,
                    COALESCE((
                        SELECT
                            json_agg(
                                json_build_object(
                                'id', _company_note.id,
                                'created_by', _company_note.created_by_id,
                                'created_by_first_name', _note_created_by.first_name,
                                'created_by_last_name', _note_created_by.last_name,
                                'text', _company_note.text,
                                'is_deleted', _company_note.is_deleted,
                                'created_at', _company_note.created_at,
                                'last_updated_at', _company_note.last_updated_at,
                                'booking', _company_note.booking_id,
                                'company', _company_note.company_id,
                                'notification', _company_note.notification_id,
                                'payer', _company_note.payer_id,
                                'provider', _company_note.provider_id,
                                'recipient', _company_note.recipient_id
                                )
                            )
                        FROM "core_backend_note" _company_note
                            INNER JOIN "core_backend_user" _note_created_by
                                ON _company_note.created_by_id = _note_created_by.id
                        WHERE _company_note.company_id = company.id AND _company_note.is_deleted=FALSE
                    ), '[]'::JSON) AS notes,
                    COALESCE((
                        SELECT JSON_AGG(t) FROM ( 
                        SELECT payer.*, COALESCE(id IS NOT NULL, true) AS is_payer, payer_lateral.* FROM core_backend_payer payer,
                        LATERAL (
                            SELECT username, email, first_name, last_name, national_id, ssn, date_of_birth, title, suffix,
                            user_contacts_lateral.*, contacts_lateral.*, company_lateral.*, notes_lateral.*, location_lateral.*, payer_companies_lateral.* FROM core_backend_user,
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
                                SELECT payer_id AS payer_id, company_id as company_id FROM core_backend_payer_companies WHERE payer_id = payer.id
                            ) AS payer_companies_lateral,
                            LATERAL (
                                SELECT JSON_AGG(t) as companies FROM (
                                SELECT * FROM core_backend_company WHERE core_backend_company.id = company_id
                                ) t
                            ) As company_lateral,
                            LATERAL (
                                SELECT JSON_AGG(t) as notes FROM (
                                SELECT * FROM core_backend_note WHERE core_backend_note.payer_id = payer_id
                                ) t
                            ) As notes_lateral,
                            LATERAL (
                                SELECT JSON_AGG(t) as location FROM (
                                SELECT * FROM core_backend_location WHERE core_backend_location.id = core_backend_user.location_id
                                ) t
                            ) As location_lateral
                            WHERE core_backend_user.id = payer.user_id
                        ) AS payer_lateral
                        WHERE company_id = company.id
                        ) t
                    ), '[]'::JSON) AS payers,
                    COALESCE((
                        SELECT JSON_AGG(t) as agents FROM (
                            SELECT ARRAY[core_backend_agent_companies.agent_id] as agents_id, 
                            ARRAY[core_backend_agent_companies.id] as companies, 
                            agent_lateral.*, user_lateral.*, user_contacts_lateral.*,
                            location_lateral.*, contacts_lateral.*, requester_lateral.*, payer_lateral.*
                            FROM core_backend_agent_companies,
                            LATERAL (
                                SELECT agent_id as id, role, is_deleted, user_id AS userId, user_id FROM core_backend_agent WHERE id = core_backend_agent_companies.agent_id
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
                            WHERE core_backend_agent_companies.company_id = company.id
                        ) t
                    ), '[]'::JSON) AS agents,
                    COALESCE((
                        SELECT JSON_AGG(t) FROM ( 
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
                                WHERE company_id = company.id
                            ) t
                    ), '[]'::JSON) AS requesters,
                    (
                        SELECT
                            json_build_object(
                            'id', _company.id,
                            'contacts', COALESCE((
                                SELECT
                                    json_agg(row_to_json(_contacts))
                                FROM "core_backend_company_contacts" _company_contacts
                                    INNER JOIN "core_backend_contact" _contacts
                                        ON _contacts.id = _company_contacts.contact_id
                                WHERE _company_contacts.company_id = _company.id AND _contacts.is_deleted=FALSE
                            ), '[]'::JSON),
                            'locations', COALESCE((
                                SELECT
                                    json_agg(row_to_json(_locations))
                                FROM "core_backend_company_locations" _company_locations
                                    INNER JOIN "core_backend_location" _locations
                                        ON _locations.id = _company_locations.location_id
                                WHERE _company_locations.company_id = _company.id AND _locations.is_deleted=FALSE
                            ), '[]'::JSON),
                            'notes',     COALESCE((
                                SELECT
                                    json_agg(
                                        json_build_object(
                                        'id', _company_note.id,
                                        'created_by', _company_note.created_by_id,
                                        'created_by_first_name', _note_created_by.first_name,
                                        'created_by_last_name', _note_created_by.last_name,
                                        'text', _company_note.text,
                                        'is_deleted', _company_note.is_deleted,
                                        'created_at', _company_note.created_at,
                                        'last_updated_at', _company_note.last_updated_at,
                                        'booking', _company_note.booking_id,
                                        'company', _company_note.company_id,
                                        'notification', _company_note.notification_id,
                                        'payer', _company_note.payer_id,
                                        'provider', _company_note.provider_id,
                                        'recipient', _company_note.recipient_id
                                        )
                                    )
                                FROM "core_backend_note" _company_note
                                    INNER JOIN "core_backend_user" _note_created_by
                                        ON _company_note.created_by_id = _note_created_by.id
                                WHERE _company_note.company_id = _company.id AND _company_note.is_deleted=FALSE
                            ), '[]'::JSON),
                            'parent_company_id', _company.parent_company_id,
                            'is_deleted', _company.is_deleted,
                            'name', _company.name,
                            'type', _company.type,
                            'send_method', _company.send_method,
                            'on_hold', _company.on_hold,
                            'aliases', _company.aliases
                            )
                        FROM "core_backend_company" _company
                        WHERE _company.id = company.parent_company_id
                    ) AS parent_company,
                    COALESCE((
                        SELECT
                            json_agg(row_to_json(_company_rate))
                        FROM "core_backend_rate" _company_rate
                        WHERE _company_rate.company_id = company.id AND _company_rate.is_deleted=FALSE
                    ), '[]'::JSON) AS rates,
                    COALESCE((
                        SELECT
                            json_agg(row_to_json(_company_relationship))
                        FROM "core_backend_companyrelationship" _company_relationship
                        WHERE _company_relationship.company_from_id = company.id AND _company_relationship.is_deleted=FALSE
                    ), '[]'::JSON) AS company_relationships_from,
                    company.is_deleted,
                    company.name,
                    company.type,
                    company.send_method,
                    company.on_hold,
                    company.aliases
                FROM "core_backend_company" company
                WHERE %s
                ORDER BY company.name, company.id
                %s
            ) _query_result
        """ % (where_conditions, limit_statement)

        cursor.execute(query, params)
        result = cursor.fetchone()
        if len(result) == 1:
            return result[0]

        return []

    @staticmethod
    def get_company_count_sql(cursor, id, name, type, send_method, on_hold):
        params, where_conditions, _ = ApiSpecialSqlCompanies.get_company_sql_where_clause(id, name, type, send_method, on_hold, None, None)

        query = """
            SELECT
               COUNT(*)
            FROM "core_backend_company" company
            WHERE %s
        """ % where_conditions

        cursor.execute(query, params)
        result = cursor.fetchone()
        if len(result) == 1:
            return result[0]

        return 0