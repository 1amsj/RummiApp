class ApiSpecialSqlReports:

    @staticmethod
    def get_report_sql_ct_id(cursor):
        query = """--sql
            SELECT
                id
            FROM "django_content_type" content_type
            WHERE app_label = 'core_backend' AND model = 'report'
        """
        
        cursor.execute(query, [id])
        result = cursor.fetchone()
        if result is not None:
            return result[0]
        
        return None
