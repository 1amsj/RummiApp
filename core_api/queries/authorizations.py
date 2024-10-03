class ApiSpecialSqlAuthorizations:
    def get_authorizations_sql(id, event_id):
        where_conditions = 'auth.is_deleted = FALSE'
        
        if id is not None:
            where_conditions += """ AND auth.id = """+str(id)
            
        if event_id is not None:
            where_conditions += """ AND _authorization_events.event_id = """+str(event_id)
            
        return """--sql
            SELECT JSON_AGG(JSON) FROM (
                SELECT auth.*,
                COALESCE((
                    SELECT json_agg(row_to_json(events)) FROM 
                        core_backend_authorization_events auth_events
                            INNER JOIN core_backend_event events ON auth_events.event_id = events.id
                    WHERE auth_events.authorization_id = auth.id
                ), '[]'::JSON) As events,
                COALESCE((
                    SELECT
                        row_to_json(_contacts)
                    FROM "core_backend_contact" _contacts
                    WHERE _contacts.id = auth.contact_id AND _contacts.is_deleted=FALSE
                ), '{}'::JSON) As contact,
                COALESCE((
                    SELECT row_to_json(t) FROM ( 
                    SELECT payer.*, COALESCE(id IS NOT NULL, true) AS is_payer, payer_lateral.* FROM core_backend_payer payer,
                    LATERAL (
                        SELECT username, email, first_name, last_name, national_id, ssn, date_of_birth, title, suffix,
                        user_contacts_lateral.*, contacts_lateral.*, company_lateral.*, notes_lateral.*, location_lateral.*, payer_companies_lateral.* FROM core_backend_user,
                        LATERAL (
                            SELECT json_agg(row_to_json(t)) -> 0 as user_contacts_ids FROM (
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
                    WHERE payer.id = auth.authorizer_id
                    ) t
                ), '[]'::JSON) AS authorizer,
                _authorization_events.event_id AS event_id,
                company_lateral.*
                FROM core_backend_authorization_events _authorization_events
                    INNER JOIN core_backend_authorization auth 
                        ON auth.id = _authorization_events.authorization_id,
                LATERAL(
                    SELECT row_to_json(_query_result) AS company FROM (
                        SELECT
                            company.id,
                            company.type
                        FROM "core_backend_company" company
                        WHERE auth.company_id = company.id
                        ORDER BY company.name, company.id
                    ) _query_result
                ) AS company_lateral
                WHERE %s
            ) JSON
        """ % where_conditions