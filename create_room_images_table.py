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
    
    # Drop the table if it exists
    cursor.execute("DROP TABLE IF EXISTS room_images")
    print("✓ Dropped existing room_images table (if any)")
    
    # Create the room_images table with INT UNSIGNED to match rooms.id
    create_table_sql = """
    CREATE TABLE room_images (
        id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
        room_id INT UNSIGNED NOT NULL,
        image_url VARCHAR(255) NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_room_id (room_id),
        CONSTRAINT fk_room_images_room_id 
            FOREIGN KEY (room_id) 
            REFERENCES rooms(id) 
            ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """
    
    try:
        cursor.execute(create_table_sql)
        conn.commit()
        print("✓ room_images 테이블이 성공적으로 생성되었습니다!")
        
        # Show the created table
        cursor.execute("SHOW CREATE TABLE room_images")
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
