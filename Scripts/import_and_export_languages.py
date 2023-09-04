import csv
import psycopg2

conn = psycopg2.connect(
    host="127.0.0.1",
    database="core_db",
    user="core_user",
    password="core_password"
)

file_name = input("Input CSV of Language with path: ")

with open(file_name, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    next(reader)  # Jump Line if reader don´t exist
    row_count = sum(1 for row in reader)  # Count the number of rows in the CSV file
    f.seek(0)  # Reset the file pointer to the beginning of the file
    next(reader)  # Skip the header row
    for i, row in enumerate(reader):
        available = row[0] == 'True'
        common = row[1] == 'True'
        alpha2 = row[2]
        alpha3 = row[3]
        name = row[4]
        description = row[5]
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO core_backend_language (id, is_deleted, alpha2, alpha3, available, common, description, name) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO UPDATE SET is_deleted = EXCLUDED.is_deleted, alpha3 = EXCLUDED.alpha3, available = EXCLUDED.available, common = EXCLUDED.common, description = EXCLUDED.description, name = EXCLUDED.name",
            (i + 1, False, alpha2, alpha3, available, common, description, name)
        )

    conn.commit()
