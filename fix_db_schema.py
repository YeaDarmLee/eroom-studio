import mysql.connector

try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="dldPekfa1!",
        database="eroom"
    )
    cursor = conn.cursor()

    sqls = [
        "ALTER TABLE rooms ADD COLUMN position_x FLOAT DEFAULT 0;",
        "ALTER TABLE rooms ADD COLUMN position_y FLOAT DEFAULT 0;",
        "ALTER TABLE rooms ADD COLUMN width FLOAT DEFAULT 10;",
        "ALTER TABLE rooms ADD COLUMN height FLOAT DEFAULT 10;"
    ]

    for sql in sqls:
        try:
            cursor.execute(sql)
            print(f"Executed: {sql}")
        except mysql.connector.Error as err:
            if err.errno == 1060: # Duplicate column name
                print(f"Column already exists: {sql}")
            else:
                print(f"Error executing {sql}: {err}")

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Database schema updated successfully.")

except mysql.connector.Error as err:
    print(f"Error connecting to database: {err}")
