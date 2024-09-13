class ApiSpecialSqlCompanies():
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

        query = '' # TODO make this query

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