class ApiSpecialSqlInsertNote:
    @staticmethod
    def query_insert_note(cursor, created_note_now, body_note, booking_id_note):
        
        queryInsertSql = """--sql
            INSERT INTO core_backend_note(
                is_deleted,
                created_at,
                text,
                booking_id,
                last_updated_at
            ) VALUES (
                'false',
                '%s',
                '%s',
                '%s',
                '%s'
            )""" % (
                created_note_now,
                body_note,
                booking_id_note,
                created_note_now
            )
    
        cursor.execute(queryInsertSql)