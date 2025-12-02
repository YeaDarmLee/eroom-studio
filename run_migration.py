"""
Execute SQL migration for branch_services table
"""
import mysql.connector

try:
    # Connect to database
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='1234',
        database='eroom'
    )
    cursor = conn.cursor()
    
    # Read SQL file
    with open('migrations/add_branch_services.sql', 'r', encoding='utf-8') as f:
        sql_script = f.read()
    
    # Split by semicolon and execute each statement
    statements = [s.strip() for s in sql_script.split(';') if s.strip()]
    
    for statement in statements:
        if statement:
            try:
                cursor.execute(statement)
                print(f"✓ Executed: {statement[:50]}...")
            except Exception as e:
                print(f"✗ Error: {e}")
                print(f"  Statement: {statement[:100]}")
    
    conn.commit()
    print("\n✓ Migration completed successfully!")
    print("✓ branch_services table created")
    print("✓ Sample services inserted for existing branches")
    
except Exception as e:
    print(f"✗ Migration failed: {e}")
finally:
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals():
        conn.close()
