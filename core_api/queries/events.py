class ApiSpecialSqlEvents():

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
        params, where_conditions, limit_statement = ApiSpecialSqlEvents.get_event_sql_where_clause(id, limit, offset)

        query = """
            SELECT json_agg(row_to_json(_query_result)) AS result FROM (
                SELECT
                    event.id,
                    event.is_deleted,
                    event.start_at,
                    event.end_at,
                    event.arrive_at,
                    event.description
                FROM "core_backend_event" event
                WHERE %s
                ORDER BY event.start_at, event.id DESC
                %s
            ) _query_result
        """ % (where_conditions, limit_statement)

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