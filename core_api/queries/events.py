class ApiSpecialSqlEvents():
    
    def get_event_sql(event_id):
        return """
            SELECT json_build_object(
                'id', event.id,
                'is_deleted', event.is_deleted,
                'start_at', event.start_at,
                'end_at', event.end_at,
                'arrive_at', event.arrive_at,
                'description', event.description
            )
            FROM core_backend_event event
            WHERE event.id = """ + str(event_id) + """
        """