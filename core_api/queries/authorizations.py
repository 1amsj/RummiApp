class ApiSpecialSqlAuthorizations:
    def get_authorizations_sql(cursor, id, event_id):
        where_conditions = 'auth.is_deleted = FALSE'
        
        if id is not None:
            where_conditions += """ AND auth.id = """+str(id)
            
        if event_id is not None:
            where_conditions += """ AND _authorization_events.event_id = """+str(event_id)
            
        query = """--sql
            SELECT 
                json_agg(json_build_object(
                    'id', auth.id,
                    'is_deleted', auth.is_deleted,
                    'contact_via', auth.contact_via,
                    'last_updated_at', auth.last_updated_at,
                    'status', auth.status,
                    'events', COALESCE((
                        SELECT json_agg(json_build_object(
                            'id', events.id,
                            'meeting_url', events.meeting_url,
                            'start_at', events.start_at,
                            'end_at', events.end_at,
                            'observations', events.observations,
                            'booking_id', events.booking_id,
                            'location_id', events.location_id,
                            'payer_id', events.payer_id,
                            'requester_id', events.requester_id,
                            'is_deleted', events.is_deleted,
                            'payer_company_id', events.payer_company_id,
                            'arrive_at', events.arrive_at,
                            'description', events.description,
                            'unique_field', events.unique_field
                        ))
                        FROM  "core_backend_authorization_events" auth_events
                            INNER JOIN "core_backend_event" events ON auth_events.event_id = events.id
                                WHERE auth_events.authorization_id = auth.id
                    ), '[]'::JSON),
                    'contact', COALESCE((
                        SELECT json_build_object(
                            'id', _contacts.id,
                            'email', _contacts.email,
                            'phone', _contacts.phone,
                            'fax', _contacts.fax,
                            'is_deleted', _contacts.is_deleted,
                            'email_context', _contacts.email_context,
                            'fax_context', _contacts.fax_context,
                            'phone_context', _contacts.phone_context
                        )
                        FROM "core_backend_contact" _contacts
                            WHERE _contacts.id = auth.contact_id AND _contacts.is_deleted=FALSE
                    ), '{}'::JSON),
                    'authorizer', COALESCE((
                        SELECT json_build_object(
                            'id', payer.id,
                            'method', payer.method,
                            'user_id', payer.user_id,
                            'is_deleted', payer.is_deleted,
                            'is_payer', COALESCE(payer.id IS NOT NULL, true),
                            'username', _user.username,
                            'email', _user.email,
                            'first_name', _user.first_name,
                            'last_name', _user.last_name,
                            'national_id', _user.national_id,
                            'ssn', _user.ssn,
                            'date_of_birth', _user.date_of_birth,
                            'title', _user.title,
                            'suffix', _user.suffix,
                            'contacts', COALESCE((
                                SELECT json_agg(json_build_object(
                                    'id', _contact.id,
                                    'email', _contact.email,
                                    'phone', _contact.phone,
                                    'fax', _contact.fax,
                                    'is_deleted', _contact.is_deleted,
                                    'email_context', _contact.email_context,
                                    'fax_context', _contact.fax_context,
                                    'phone_context', _contact.phone_context
                                ))  
                                FROM "core_backend_user_contacts" user_contacts
                                    INNER JOIN "core_backend_contact" _contact on _contact.id = user_contacts.contact_id
                                        WHERE user_contacts.user_id = payer.user_id
                            ), '[]'::JSON),
                            'companies', COALESCE((
                                SELECT json_agg(json_build_object(
                                    'id', _companies.id,
                                    'name', _companies.name,
                                    'type', _companies.type,
                                    'send_method', _companies.send_method,
                                    'on_hold', _companies.on_hold,
                                    'is_deleted', _companies.is_deleted,
                                    'parent_company_id', _companies.parent_company_id,
                                    'aliases', _companies.aliases
                                ))
                                FROM "core_backend_payer_companies" payer_companies
                                    INNER JOIN "core_backend_company" _companies on _companies.id = payer_companies.company_id
                                        WHERE payer_companies.payer_id = payer.id
                            ), '[]'::JSON),
                            'notes', COALESCE((
                                SELECT json_agg(json_build_object(
                                    'id', _note.id,
                                    'is_deleted', _note.is_deleted,
                                    'created_at', _note.created_at,
                                    'text', _note.text,
                                    'payer_id', _note.payer_id
                                ))
                                FROM "core_backend_note" _note
                                    WHERE _note.payer_id = payer_id
                            ), '[]'::JSON),
                            'location', COALESCE((
                                SELECT json_agg(json_build_object(
                                    'id', _location.id,
                                    'address', _location.address,
                                    'city', _location.city,
                                    'state', _location.state,
                                    'country', _location.country,
                                    'zip', _location.zip,
                                    'is_deleted', _location.is_deleted,
                                    'unit_number', _location.unit_number
                                ))
                                FROM "core_backend_location" _location
                                    WHERE _location.id = _user.location_id
                            ), '[]'::JSON)
                        ) 
                        FROM "core_backend_payer" payer
                            INNER JOIN "core_backend_user" _user ON _user.id = payer.user_id
                                WHERE payer.id = auth.authorizer_id
                    ), '{}'::JSON),
                    'company', COALESCE((
                        SELECT json_build_object(
                            'id', _company.id,
                            'type', _company.type    
                        )    
                        FROM "core_backend_company" _company
                            WHERE auth.company_id = _company.id
                    ), '{}'::JSON),
                    'event_id', _authorization_events.event_id
                )::jsonb) AS json_data
            FROM "core_backend_authorization_events" _authorization_events
                INNER JOIN "core_backend_authorization" auth 
                    ON auth.id = _authorization_events.authorization_id
            WHERE %s
        """ % where_conditions
        
        cursor.execute(query)
        result = cursor.fetchone()
        if len(result) == 1 and event_id == None:
            return result[0][0]

        return result[0]