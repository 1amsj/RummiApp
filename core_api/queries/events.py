class ApiSpecialSqlEvents():
    @staticmethod
    def get_event_sql_ct_id(cursor):
        query = """
            SELECT
                id
            FROM "django_content_type" content_type
            WHERE app_label = 'core_backend' AND model = 'event'
        """

        cursor.execute(query, [id])
        result = cursor.fetchone()
        if result is not None:
            return result[0]

        return None

    @staticmethod
    def get_event_sql_where_clause(id, limit, offset):
        params = []
        limit_statement = ''
        where_conditions = 'event.is_deleted = FALSE'

        if id is not None:
            where_conditions += ' AND event.id = %s'
            params.append(id)

        if limit is not None and limit > 0 and offset is not None and offset >= 0:
            limit_statement = 'LIMIT %s OFFSET %s'
            params.append(limit)
            params.append(offset)

        return params, where_conditions, limit_statement
    
    @staticmethod
    def get_event_sql(cursor, id, limit, offset):
        parent_ct_id = ApiSpecialSqlEvents.get_event_sql_ct_id(cursor)
        params, where_conditions, limit_statement = ApiSpecialSqlEvents.get_event_sql_where_clause(id, limit, offset)

        query = """
            SELECT json_agg(_query_result.json_data) AS result FROM (
                SELECT
                    (json_build_object(
                    'id', event.id,
                    'is_deleted', event.is_deleted,
                    'start_at', event.start_at,
                    'end_at', event.end_at,
                    'arrive_at', event.arrive_at,
                    'description', event.description,
                    'booking_id', event.booking_id
                    )::jsonb ||
                    (
                        SELECT
                            json_object_agg(extra.key, extra.data #>> '{}')
                        FROM "core_backend_extra" extra
                        WHERE extra.parent_ct_id = %s AND extra.parent_id=event.id
                    )::jsonb) AS json_data
                FROM "core_backend_event" event
                WHERE %s
                ORDER BY event.start_at DESC, event.id
                %s
            ) _query_result
        """ % (parent_ct_id, where_conditions, limit_statement)

        cursor.execute(query, params)
        result = cursor.fetchone()
        if len(result) == 1:
            return result[0]

        return []
    
    @staticmethod
    def get_event_count_sql(cursor, id):
        params, where_conditions, _ = ApiSpecialSqlEvents.get_event_sql_where_clause(id, None, None)

        query = """
            SELECT
               COUNT(*)
            FROM "core_backend_event" event
            WHERE %s
        """ % where_conditions

        cursor.execute(query, params)
        result = cursor.fetchone()
        if len(result) == 1:
            return result[0]

        return 0