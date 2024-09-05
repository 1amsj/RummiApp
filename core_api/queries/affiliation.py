class ApiSpecialSqlAffiliates:
    def get_affiliation_sql():
        return """
        SELECT JSON_AGG(t) FROM ( SELECT * FROM core_backend_affiliation affiliate
            LEFT JOIN LATERAL (
            SELECT JSON_AGG(t) -> 0 as recipient FROM (
                SELECT id, user_id, user_lateral.* FROM core_backend_recipient recipient,
                LATERAL (
                    SELECT is_superuser, username, first_name, last_name, email, date_of_birth, 
                    user_contacts_lateral.*, contacts_lateral.*, company_lateral.*, notes_lateral.*, location_lateral.*, 
                    agent_lateral.* FROM core_backend_user,
                    LATERAL (
                        SELECT JSON_AGG(t) -> 0 as user_contacts_ids FROM (
                            SELECT contact_id FROM core_backend_user_contacts
                            WHERE core_backend_user_contacts.user_id = core_backend_user.id
                        ) t
                    ) AS user_contacts_lateral,
                    LATERAL (
                        SELECT JSON_AGG(t) as contacts FROM (
                            SELECT * FROM core_backend_contact WHERE core_backend_contact.id = (user_contacts_lateral.user_contacts_ids ->> 'contact_id')::integer
                        ) t
                    ) As contacts_lateral,
                    LATERAL (
                        SELECT JSON_AGG(t) as companies FROM (
                            SELECT * FROM core_backend_company WHERE core_backend_company.id = affiliate.company_id
                        ) t
                    ) As company_lateral,
                    LATERAL (
                        SELECT JSON_AGG(t) as notes FROM (
                            SELECT * FROM core_backend_note WHERE core_backend_note.recipient_id = affiliate.recipient_id
                        ) t
                    ) As notes_lateral,
                    LATERAL (
                        SELECT JSON_AGG(t) -> 0 as location FROM (
                            SELECT * FROM core_backend_location WHERE core_backend_location.id = core_backend_user.location_id
                        ) t
                    ) As location_lateral,
                    LATERAL (
                        SELECT JSON_AGG(t) as agents_id FROM (
                            SELECT id FROM core_backend_agent WHERE core_backend_agent.user_id = core_backend_user.id
                        ) t
                    ) As agent_lateral
                    WHERE core_backend_user.id = recipient.user_id
                ) As user_lateral
                WHERE affiliate.recipient_id = recipient.id
            ) t
        ) recipient_id ON true
        WHERE recipient IS NOT NULL
        Order by id desc
        ) t"""