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
    def get_services_sql(cursor, source_languague_alpha3, target_languague_alpha3, root, service_id):
        where_conditions = 'service.is_deleted = FALSE'
        where_conditions_source = ''
        where_conditions_target = ''
        
        if service_id is not None:
            where_conditions += ' AND service.id = %s' % service_id
        
        if root is not None:
            where_conditions += ' AND service.root_id = %s' % root
        
        if source_languague_alpha3 is not None:
            where_conditions_source = "AND data::text LIKE '%"+source_languague_alpha3+"%'"
            
        if target_languague_alpha3 is not None:
            where_conditions_target = " AND data::text LIKE '%"+target_languague_alpha3+"%'"
        
        query = """
        SELECT JSON_AGG(t) FROM (
            SELECT 
                service.*,
                COALESCE((
                    SELECT row_to_json(t) FROM (
                        SELECT serviceroot_root.*, categories_lateral.*
                        FROM "core_backend_serviceroot" serviceroot_root,
                        LATERAL (
                            SELECT json_agg(row_to_json(_categories)) AS categories
                            FROM core_backend_serviceroot_categories _root_categories
                                INNER JOIN core_backend_category _categories
                                    ON _categories.id = _root_categories.category_id
                            WHERE _root_categories.serviceroot_id = service.root_id
                        ) AS categories_lateral
                        WHERE serviceroot_root.id = service.root_id
                    ) t
                ), '{}') AS root,
                COALESCE((
					SELECT JSON_AGG(t) -> 0 -> 'data' FROM (
                    	SELECT data FROM core_backend_extra WHERE key = 'target_language_alpha3' and parent_id = service.root_id %s
					) t
                ), '{}') AS target_language_alpha3,
                COALESCE((
                    SELECT data FROM core_backend_extra WHERE key = 'source_language_alpha3' and parent_id = service.root_id %s
                ), '{}') AS source_language_alpha3,
                COALESCE((
                    SELECT row_to_json(t) FROM (
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
                        WHERE provider.id = service.provider_id
                    ) t
                ), '{}') AS provider,
                service.business_id AS business
            FROM "core_backend_service" service
            WHERE %s
            ORDER BY id desc
        ) t
        """ % (where_conditions_source, where_conditions_target, where_conditions)
        
        cursor.execute(query)
        services = cursor.fetchone()
        
        return services