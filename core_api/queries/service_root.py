class ApiSpecialSqlServiceRoot:
    def get_service_root_sql():
        return """
        SELECT JSON_AGG(t) FROM (
            SELECT serviceroot.*, 
            COALESCE((
                SELECT json_agg(row_to_json(_categories))
                FROM core_backend_serviceroot_categories _root_categories
                    INNER JOIN core_backend_category _categories
                        ON _categories.id = _root_categories.category_id
                WHERE _root_categories.serviceroot_id = serviceroot.id
            ), '[]'::JSON) AS categories,
            COALESCE((
                SELECT JSON_AGG(t) FROM (
                    SELECT _service.*, root_lateral.*, target_language_alpha3_lateral.*, 
                    source_language_alpha3_lateral.*, provider_lateral.*
                    FROM core_backend_service _service,
                        LATERAL(
                            SELECT JSON_AGG(t) AS root FROM (
                                SELECT serviceroot_root.*, categories_lateral.*
                                FROM "core_backend_serviceroot" serviceroot_root,
                                LATERAL (
                                    SELECT json_agg(row_to_json(_categories)) AS categories
                                    FROM core_backend_serviceroot_categories _root_categories
                                        INNER JOIN core_backend_category _categories
                                            ON _categories.id = _root_categories.category_id
                                    WHERE _root_categories.serviceroot_id = serviceroot.id
                                ) AS categories_lateral
                                WHERE serviceroot_root.id = serviceroot.id
                            ) t
                        ) AS root_lateral,
                        LATERAL(
                            SELECT data as target_language_alpha3 FROM core_backend_extra WHERE key = 'target_language_alpha3' and parent_id = serviceroot.id
                        ) AS target_language_alpha3_lateral,
                        LATERAL(
                            SELECT data as source_language_alpha3 FROM core_backend_extra WHERE key = 'source_language_alpha3' and parent_id = serviceroot.id
                        ) AS source_language_alpha3_lateral,
                        LATERAL(
                            SELECT JSON_AGG(t) AS provider FROM (
                                SELECT provider.*, provider_lateral.* FROM core_backend_provider provider, 
                                LATERAL (
                                    SELECT username, email, first_name, last_name, national_id, ssn, date_of_birth, title, suffix
                                    ,
                                    contacts_lateral.*
                                    , 
                                    user_contacts_lateral.*, 
                                    location_lateral.*, 
                                    companies_lateral.*
                                    FROM core_backend_user
                                    ,
                                    LATERAL (
                                        SELECT ARRAY[core_backend_provider_companies.id] AS companies, provider_id FROM core_backend_provider_companies
                                        WHERE provider_id = provider.id
                                    ) as companies_lateral
                                    ,
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
                                    ) AS contacts_lateral,
                                    LATERAL (
                                        SELECT JSON_AGG(t) -> 0 as location FROM (
                                            SELECT * FROM core_backend_location WHERE core_backend_location.id = core_backend_user.location_id
                                        ) t
                                    ) as location_lateral
                                    WHERE core_backend_user.id = provider.user_id
                                ) AS provider_lateral
                                WHERE provider.id = _service.provider_id
                            ) t
                        ) AS provider_lateral
                    WHERE _service.root_id = serviceroot.id
                ) t
            ), '[]'::JSON) AS services,
            COALESCE((
                SELECT array_agg(booking.id) as bookings_id FROM core_backend_booking booking WHERE booking.service_root_id = serviceroot.id
            )) AS bookings
            FROM "core_backend_serviceroot" serviceroot
            WHERE serviceroot.is_deleted = false
        ) t
        """