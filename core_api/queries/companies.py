from core_api.queries.rates import ApiSpecialSqlRates


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
        parent_rate_ct_id = ApiSpecialSqlRates.get_rate_sql_ct_id(cursor)
        params, where_conditions, limit_statement = ApiSpecialSqlCompanies.get_company_sql_where_clause(id, name, type, send_method, on_hold, limit, offset)

        query = """--sql
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
                        SELECT 
                            json_agg(json_build_object(
                                'id', payer.id,
                                'method', payer.method,
                                'user_id', payer.user_id,
                                'is_deleted', payer.is_deleted,
                                'is_payer', COALESCE(payer.id IS NOT NULL, true),
                                'username', users.username,
                                'email', users.email,
                                'first_name', users.first_name,
                                'last_name', users.last_name,
                                'national_id', users.national_id,
                                'date_of_birth', users.date_of_birth,
                                'ssn', users.ssn,
                                'tittle', users.title,
                                'suffix', users.suffix,
                                'contacts', COALESCE((
                                    SELECT
                                        json_agg(json_build_object(
                                            'id', contact.id,
                                            'email', contact.email,
                                            'phone', contact.phone,
                                            'fax', contact.fax,
                                            'is_deleted', contact.is_deleted,
                                            'email_context', contact.email_context,
                                            'fax_context', contact.fax_context,
                                            'phone_context', contact.phone_context
                                        ))
                                    FROM "core_backend_user_contacts" _user_contacts
                                        INNER JOIN "core_backend_contact" contact
                                            ON _user_contacts.contact_id = contact.id
                                    WHERE _user_contacts.user_id = users.id
                                ), '[]'::JSON),
                                'companies', COALESCE((
                                    SELECT
                                        json_agg(json_build_object(
                                            'id', companies_for_payer.id,
                                            'name', companies_for_payer.name,
                                            'type', companies_for_payer.type,
                                            'send_method', companies_for_payer.send_method,
                                            'on_hold', companies_for_payer.on_hold,
                                            'is_deleted', companies_for_payer.is_deleted,
                                            'parent_company_id', companies_for_payer.parent_company_id,
                                            'aliases', companies_for_payer.aliases
                                        ))
                                    FROM "core_backend_payer_companies" _payer_company
                                        INNER JOIN "core_backend_company" companies_for_payer
                                            ON _payer_company.company_id = companies_for_payer.id
                                    WHERE _payer_company.payer_id = payer.id
                                ), '[]'::JSON),
                                'location', COALESCE((
                                    SELECT
                                        json_agg(json_build_object(
                                            'id', locations.id,
                                            'address', locations.address,
                                            'city', locations.city,
                                            'state', locations.state,
                                            'country', locations.country,
                                            'zip', locations.zip,
                                            'is_deleted', locations.is_deleted,
                                            'unit_number', locations.unit_number
                                        ))
                                    FROM "core_backend_location" locations
                                    WHERE locations.id = users.location_id
                                ), '[]'::JSON),
                                'notes', COALESCE((
                                    SELECT
                                        json_agg(json_build_object(
                                            'id', notes.id, 
                                            'is_deleted', notes.is_deleted,
                                            'created_at', notes.created_at,
                                            'text', notes.text
                                        ))
                                    FROM "core_backend_note" notes
                                    WHERE notes.payer_id = payer.id
                                ))
                            ))
                        FROM "core_backend_payer_companies" _company_payer
                            INNER JOIN "core_backend_payer" payer 
                                ON payer.id = _company_payer.payer_id
                            INNER JOIN "core_backend_user" users
                                ON payer.user_id = users.id
                        WHERE _company_payer.company_id = company.id
                    ), '[]'::JSON) AS payers,
                    COALESCE((
                        SELECT
                            json_agg(json_build_object(
                                'id', agent_id,
                                'role', agent.role,
                                'user_id', agent.user_id,
                                'is_deleted', agent.is_deleted,
                                'username', users.username,
                                'email', users.email,
                                'first_name', users.first_name,
                                'last_name', users.last_name,
                                'national_id', users.national_id,
                                'date_of_birth', users.date_of_birth,
                                'ssn', users.ssn,
                                'tittle', users.title,
                                'suffix', users.suffix,
                                'contacts', COALESCE((
                                    SELECT
                                        json_agg(json_build_object(
                                            'id', contact.id,
                                            'email', contact.email,
                                            'phone', contact.phone,
                                            'fax', contact.fax,
                                            'is_deleted', contact.is_deleted,
                                            'email_context', contact.email_context,
                                            'fax_context', contact.fax_context,
                                            'phone_context', contact.phone_context
                                        ))
                                    FROM "core_backend_user_contacts" _user_contacts
                                        INNER JOIN "core_backend_contact" contact
                                            ON _user_contacts.contact_id = contact.id
                                    WHERE _user_contacts.user_id = users.id
                                ), '[]'::JSON),
                                'location', COALESCE((
                                    SELECT
                                        json_agg(json_build_object(
                                            'id', locations.id,
                                            'address', locations.address,
                                            'city', locations.city,
                                            'state', locations.state,
                                            'country', locations.country,
                                            'zip', locations.zip,
                                            'is_deleted', locations.is_deleted,
                                            'unit_number', locations.unit_number
                                        ))
                                    FROM "core_backend_location" locations
                                    WHERE locations.id = users.location_id
                                ), '[]'::JSON),
                                'companies', COALESCE((
                                    SELECT
                                        json_agg(
                                            companies_for_agent.id
                                        )
                                    FROM "core_backend_agent_companies" _agent_company
                                        INNER JOIN "core_backend_company" companies_for_agent
                                            ON _agent_company.company_id = companies_for_agent.id
                                    WHERE _agent_company.agent_id = agent.id
                                ), '[]'::JSON),
                                'agents_id', COALESCE((
                                    SELECT
                                        json_agg(
                                            _agent.id
                                        )
                                    FROM "core_backend_agent" _agent
                                    WHERE _agent.id = agent.id
                                ), '[]'::JSON),
                                'is_payer', COALESCE((
                                    SELECT 
                                        COALESCE(_payer.id IS NOT NULL, true)
                                    FROM "core_backend_payer" _payer
                                    WHERE _payer.user_id = users.id
                                )),
                                'is_agent', COALESCE(agent.id IS NOT NULL, true)
                            ))
                        FROM "core_backend_agent_companies" _company_agent
                            INNER JOIN "core_backend_agent" agent 
                                ON agent.id = _company_agent.agent_id
                            INNER JOIN "core_backend_user" users
                                ON agent.user_id = users.id
                        WHERE _company_agent.company_id = company.id
                    ), '[]'::JSON) AS agents,
                    COALESCE((
                        SELECT
                            json_agg(json_build_object(
                                'id', requester_id,
                                'user_id', requester.user_id,
                                'is_deleted', requester.is_deleted,
                                'username', users.username,
                                'email', users.email,
                                'first_name', users.first_name,
                                'last_name', users.last_name,
                                'national_id', users.national_id,
                                'date_of_birth', users.date_of_birth,
                                'ssn', users.ssn,
                                'tittle', users.title,
                                'suffix', users.suffix,
                                'contacts', COALESCE((
                                    SELECT
                                        json_agg(json_build_object(
                                            'id', contact.id,
                                            'email', contact.email,
                                            'phone', contact.phone,
                                            'fax', contact.fax,
                                            'is_deleted', contact.is_deleted,
                                            'email_context', contact.email_context,
                                            'fax_context', contact.fax_context,
                                            'phone_context', contact.phone_context
                                        ))
                                    FROM "core_backend_user_contacts" _user_contacts
                                        INNER JOIN "core_backend_contact" contact
                                            ON _user_contacts.contact_id = contact.id
                                    WHERE _user_contacts.user_id = users.id
                                ), '[]'::JSON),
                                'location', COALESCE((
                                    SELECT
                                        json_build_object(
                                            'id', locations.id,
                                            'address', locations.address,
                                            'city', locations.city,
                                            'state', locations.state,
                                            'country', locations.country,
                                            'zip', locations.zip,
                                            'is_deleted', locations.is_deleted,
                                            'unit_number', locations.unit_number
                                        )
                                    FROM "core_backend_location" locations
                                    WHERE locations.id = users.location_id
                                ), '{}'::JSON),
                                'companies', COALESCE((
                                    SELECT
                                        json_agg(json_build_object(
                                            'id', companies_for_requester.id,
                                            'name', companies_for_requester.name,
                                            'type', companies_for_requester.type,
                                            'send_method', companies_for_requester.send_method,
                                            'on_hold', companies_for_requester.on_hold,
                                            'is_deleted', companies_for_requester.is_deleted,
                                            'parent_company_id', companies_for_requester.parent_company_id,
                                            'aliases', companies_for_requester.aliases
                                        ))
                                    FROM "core_backend_requester_companies" _requester_company
                                        INNER JOIN "core_backend_company" companies_for_requester
                                            ON _requester_company.company_id = companies_for_requester.id
                                    WHERE _requester_company.requester_id = requester.id
                                ), '[]'::JSON),
                                'is_requester', COALESCE(requester.id IS NOT NULL, true)
                            ))
                        FROM "core_backend_requester_companies" _company_requester
                            INNER JOIN "core_backend_requester" requester 
                                ON requester.id = _company_requester.requester_id
                            INNER JOIN "core_backend_user" users
                                ON requester.user_id = users.id
                        WHERE _company_requester.company_id = company.id
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
                            json_agg(
                                json_build_object(
                                    'id', _company_rate.id,
                                    'bill_amount', _company_rate.bill_amount,
                                    'bill_rate', _company_rate.bill_rate,
                                    'bill_rate_type', _company_rate.bill_rate_type,
                                    'bill_rate_minutes_threshold', _company_rate.bill_rate_minutes_threshold,
                                    'bill_min_payment', _company_rate.bill_min_payment,
                                    'bill_no_show_fee', _company_rate.bill_no_show_fee,
                                    'root', COALESCE((
                                        SELECT 
                                            json_build_object(
                                                'id', _serviceroot.id,
                                                'description', _serviceroot.description,
                                                'name', _serviceroot.name,
                                                'categories', COALESCE((
                                                    SELECT
                                                        json_agg(
                                                            json_build_object(
                                                                'id', _categories.id,
                                                                'description', _categories.description,
                                                                'name', _categories.name
                                                            )
                                                        )
                                                    FROM "core_backend_serviceroot_categories" _serviceroot_categories
                                                        INNER JOIN "core_backend_category" _categories
                                                            ON _categories.id = _serviceroot_categories.category_id
                                                    WHERE _serviceroot_categories.serviceroot_id = _serviceroot.id
                                                ), '[]'::JSON)
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
                        WHERE _company_rate.company_id = company.id
                        ), '[]'::JSON
                    ) AS rates,
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
        """ % (parent_rate_ct_id, where_conditions, limit_statement)

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