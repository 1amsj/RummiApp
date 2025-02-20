class ApiSpecialSqlServiceRoot:
    
    @staticmethod
    def get_service_root_sql_ct_id(cursor):
        query = """--sql
            SELECT
                id
            FROM "django_content_type" content_type
            WHERE app_label = 'core_backend' AND model = 'serviceroot'
        """

        cursor.execute(query, [id])
        result = cursor.fetchone()
        if result is not None:
            return result[0]

        return None

    @staticmethod
    def get_service_root_sql_where_clause(
        id,
        limit,
        offset
    ):
        params = []
        limit_statement = ''
        where_conditions = 'service_root.is_deleted = FALSE'
        
        if id is not None:
            where_conditions += ' AND service_root.id = %s'
            params.append(id)
            
        if limit is not None and limit > 0 and offset is not None and offset >= 0:
            limit_statement = 'LIMIT %s OFFSET %s'
            params.append(limit)
            params.append(offset)

        return params, where_conditions, limit_statement

    @staticmethod
    def get_service_root_sql(
        cursor,
        id,
        limit,
        offset,
        field_to_sort,
        order_to_sort
    ):
        params, where_conditions, limit_statement = ApiSpecialSqlServiceRoot.get_service_root_sql_where_clause(
            id,
            limit,
            offset
        )

        query = """--sql
            SELECT json_agg(_query_result.json_data) AS result FROM (
                SELECT
                    (json_build_object(
                        'id', service_root.id,
                        'name', service_root.name,
                        'description', service_root.description,
                        'is_deleted', service_root.is_deleted,
                        'categories', COALESCE((
                            SELECT
                                json_agg(json_build_object(
                                    'id', category.id,
                                    'name', category.name,
                                    'description', category.description,
                                    'is_deleted', category.is_deleted
                                ))
                            FROM "core_backend_serviceroot_categories" service_root_categories
                                INNER JOIN "core_backend_category" category
                                    ON service_root_categories.category_id = category.id AND category.is_deleted = FALSE
                            WHERE service_root_categories.serviceroot_id = service_root.id
                        ), '[]'::json)
                    )) AS json_data
                FROM "core_backend_serviceroot" service_root
                WHERE %s
                ORDER BY %s %s NULLS LAST
                %s
            ) AS _query_result
        """ % (where_conditions, field_to_sort, order_to_sort, limit_statement)
        
        cursor.execute(query, params)
        result = cursor.fetchone()
        if len(result) == 1 and result[0] is not None:
            return result[0]

        return []
    
    @staticmethod
    def get_service_root_count_sql(
        cursor,
        id
    ):
        params, where_conditions, _ = ApiSpecialSqlServiceRoot.get_service_root_sql_where_clause(
            id,
            None,
            None
        )

        query = """--sql
            SELECT
               COUNT(DISTINCT service_root.id)
            FROM "core_backend_serviceroot" service_root
            WHERE %s
        """ % where_conditions

        cursor.execute(query, params)
        result = cursor.fetchone()
        if len(result) == 1:
            return result[0]

        return 0