class ApiSpecialSqlContentTypeIds:
    @staticmethod
    def get_booking_sql_ct_id(cursor):
        query = """
            SELECT id
            FROM "django_content_type" content_type
            WHERE app_label = 'core_backend' AND model = 'booking'
        """
        cursor.execute(query)  # no parameters needed
        result = cursor.fetchone()
        return result[0] if result is not None else None

    @staticmethod
    def get_provider_sql_ct_id(cursor):
        query = """
            SELECT id
            FROM "django_content_type" content_type
            WHERE app_label = 'core_backend' AND model = 'provider'
        """
        cursor.execute(query)
        result = cursor.fetchone()
        return result[0] if result is not None else None

    @staticmethod
    def get_service_sql_ct_id(cursor):
        query = """
            SELECT id
            FROM "django_content_type" content_type
            WHERE app_label = 'core_backend' AND model = 'service'
        """
        cursor.execute(query)
        result = cursor.fetchone()
        return result[0] if result is not None else None

    @staticmethod
    def get_event_sql_ct_id(cursor):
        query = """
            SELECT id
            FROM "django_content_type" content_type
            WHERE app_label = 'core_backend' AND model = 'event'
        """
        cursor.execute(query)
        result = cursor.fetchone()
        return result[0] if result is not None else None

    @staticmethod
    def get_operator_sql_ct_id(cursor):
        query = """
            SELECT id
            FROM "django_content_type" content_type
            WHERE app_label = 'core_backend' AND model = 'operator'
        """
        cursor.execute(query)
        result = cursor.fetchone()
        return result[0] if result is not None else None

    @staticmethod
    def get_companies_sql_ct_id(cursor):
        query = """
            SELECT id
            FROM "django_content_type" content_type
            WHERE app_label = 'core_backend' AND model = 'company'
        """
        cursor.execute(query)
        result = cursor.fetchone()
        return result[0] if result is not None else None

    @staticmethod
    def get_rate_sql_ct_id(cursor):
        query = """
            SELECT id
            FROM "django_content_type" content_type
            WHERE app_label = 'core_backend' AND model = 'rate'
        """
        cursor.execute(query)
        result = cursor.fetchone()
        return result[0] if result is not None else None
    
    @staticmethod
    def get_invoice_sql_ct_id(cursor):
        query = """--sql
            SELECT
                id
            FROM "django_content_type" content_type
            WHERE app_label = 'core_backend' AND model = 'invoice'
        """

        cursor.execute(query, [id])
        result = cursor.fetchone()
        if result is not None:
            return result[0]

        return None