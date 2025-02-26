class ApiSpecialSqlInvoices:

    @staticmethod
    def get_invoice_sql_where_clause(
        id,
        limit,
        offset
    ):
        params = []
        limit_statement = ''
        where_conditions = 'invoice.is_deleted = FALSE'
        
        if id is not None:
            where_conditions += ' AND invoice.id = %s'
            params.append(id)
            
        if limit is not None and limit > 0 and offset is not None and offset >= 0:
            limit_statement = 'LIMIT %s OFFSET %s'
            params.append(limit)
            params.append(offset)

        return params, where_conditions, limit_statement

    @staticmethod
    def get_invoice_sql(
        cursor,
        id,
        limit,
        offset,
        field_to_sort,
        order_to_sort
    ):
        params, where_conditions, limit_statement = ApiSpecialSqlInvoices.get_invoice_sql_where_clause(
            id,
            limit,
            offset
        )

        query = """--sql
            SELECT json_agg(_query_result.json_data) AS result FROM (
                SELECT
                    (json_build_object(
                        'id', invoice.id,
                        'created_at', invoice.created_at,
                        'sent_at', invoice.sent_at,
                        'sent', invoice.sent,
                        'amount', invoice.amount,
                        'taxes', invoice.taxes,
                    )) AS json_data
                FROM "core_backend_invoice" invoice
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
    def get_invoice_count_sql(
        cursor,
        id
    ):
        params, where_conditions, _ = ApiSpecialSqlInvoices.get_invoice_sql_where_clause(
            id,
            None,
            None
        )

        query = """--sql
            SELECT
               COUNT(DISTINCT invoice.id)
            FROM "core_backend_invoice" invoice
            WHERE %s
        """ % where_conditions

        cursor.execute(query, params)
        result = cursor.fetchone()
        if len(result) == 1:
            return result[0]

        return 0