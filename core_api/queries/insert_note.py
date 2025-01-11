class ApiSpecialSqlInsertNote:
    @staticmethod
    def query_insert_note(cursor, start_at_note, body_note, booking_id_note):
        
        queryInsertSql = """--sql
            INSERT INTO core_backend_note(
                is_deleted,
                created_at,
                text,
                booking_id,
                created_by_id,
                last_updated_at
            ) VALUES (
                'false',
                '%s',
                '%s',
                '%s',
                '4',
                '%s'
            )""" % (
                start_at_note,
                body_note,
                booking_id_note,
                start_at_note
            )
    
        cursor.execute(queryInsertSql)