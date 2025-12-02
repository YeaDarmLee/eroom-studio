import mysql.connector
from config import config
import re

# Get database configuration
db_config = config['default'].SQLALCHEMY_DATABASE_URI

# Parse the connection string
match = re.match(r'mysql\+mysqlconnector://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', db_config)
if match:
    user, password, host, port, database = match.groups()
    
    # Connect to MySQL
    conn = mysql.connector.connect(
        host=host,
        port=int(port),
        user=user,
        password=password,
        database=database
    )
    
    cursor = conn.cursor()
    
    # Check branches table structure
    cursor.execute("SHOW CREATE TABLE branches")
    result = cursor.fetchone()
    print("Branches table structure:")
    print(result[1])
    print("\n" + "="*80 + "\n")
    
    # Drop table if exists
    cursor.execute("DROP TABLE IF EXISTS branch_images")
    
    # Create the branch_images table with INT (assuming branches.id is INT based on previous experience, but will verify)
    # If branches.id is INT UNSIGNED, we need to match it.
    
    is_unsigned = "unsigned" in result[1].lower()
    id_type = "INT UNSIGNED" if is_unsigned else "INT"
    
    print(f"Detected ID type for branches: {id_type}")
    
    create_table_sql = f"""
    CREATE TABLE branch_images (
        id {id_type} AUTO_INCREMENT PRIMARY KEY,
        branch_id {id_type} NOT NULL,
        image_url VARCHAR(255) NOT NULL,
        order_index INT DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_branch_id (branch_id),
        CONSTRAINT fk_branch_images_branch_id 
            FOREIGN KEY (branch_id) 
            REFERENCES branches(id) 
            ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """
    
    try:
        cursor.execute(create_table_sql)
        conn.commit()
        print("✓ branch_images 테이블이 성공적으로 생성되었습니다!")
        
        # Show the created table
        cursor.execute("SHOW CREATE TABLE branch_images")
        result = cursor.fetchone()
        print("\nCreated table structure:")
        print(result[1])
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()
        conn.close()
else:
    print("Failed to parse database configuration")
