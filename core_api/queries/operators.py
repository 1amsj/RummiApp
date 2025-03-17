class ApiSpecialSqlOperators():
  
    @staticmethod
    def get_operator_sql_ct_id(cursor):
        query = """
            SELECT
                id
            FROM "django_content_type" content_type
            WHERE app_label = 'core_backend' AND model = 'operator'
        """

        cursor.execute(query, [id])
        result = cursor.fetchone()
        if result is not None:
            return result[0]

        return None
    @staticmethod
    def get_operator_sql_where_clause(id, limit, offset):
        params = []
        limit_statement = ''
        where_conditions = 'operator.is_deleted = FALSE'

        if id is not None:
            where_conditions += ' AND operator.id = %s'
            params.append(id)

        if limit is not None and limit > 0 and offset is not None and offset >= 0:
            limit_statement = 'LIMIT %s OFFSET %s'
            params.append(limit)
            params.append(offset)

        return params, where_conditions, limit_statement


    @staticmethod
    def get_operator_sql(cursor, id, limit, offset):

      params, where_conditions, limit_statement = ApiSpecialSqlOperators.get_operator_sql_where_clause(id, limit, offset)
    
      query = """---sql
        SELECT json_agg(_query_result.json_data) AS result FROM (
          SELECT (
            json_build_object(
              'id', operator.id,
              'is_deleted', operator.is_deleted,
              'hiring_date', operator.hiring_date,
              'first_name', _user.first_name,
              'last_name', _user.last_name,
              'title', _user.title,
              'suffix', _user.suffix,
              'date_of_birth', _user.date_of_birth,
              'user_id', _user.id,
              'location', (
                SELECT 
                  json_build_object(
                    'id', location.id,
                    'country', location.country,
                    'address', location.address,
                    'city', location.city,
                    'state', location.state,
                    'zip', location.zip,
                    'unit_number', location.unit_number
                  )
                FROM "core_backend_location" location
                WHERE location.id = _user.location_id
              ),
              'contacts', COALESCE((
                SELECT json_agg(
                  json_build_object(
                    'id', contact.id,
                    'email', contact.email,
                    'phone', contact.phone,
                    'fax', contact.fax,
                    'phone_context', contact.phone_context,
                    'email_context', contact.email_context,
                    'fax_context', contact.fax_context
                  )
                )
                FROM "core_backend_user_contacts" _user_contact
                  INNER JOIN "core_backend_contact" contact
                    ON _user_contact.contact_id = contact.id
                WHERE _user_contact.user_id = _user.id
              ), '[]'::json)
            )
          ) AS json_data
          FROM "core_backend_operator" operator
            INNER JOIN "core_backend_user" _user 
              ON operator.user_id = _user.id
          WHERE %s
          ORDER BY operator.id
          %s
        ) _query_result
      """ % (where_conditions, limit_statement)

      cursor.execute(query, params)
      result = cursor.fetchone()
      if len(result) == 1:
          return result[0]

      return []

    @staticmethod
    def get_operator_count_sql(cursor, id):
        params, where_conditions, _ = ApiSpecialSqlOperators.get_operator_sql_where_clause(id, None, None)

        query = """
            SELECT
               COUNT(*)
            FROM "core_backend_operator" operator
            WHERE %s
        """ % where_conditions

        cursor.execute(query, params)
        result = cursor.fetchone()
        if len(result) == 1:
            return result[0]

        return 0