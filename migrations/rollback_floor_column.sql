-- Rollback script for floor column
-- Use this if you need to remove the floor column

-- Remove the floor column
ALTER TABLE rooms DROP COLUMN floor;

-- Verify the column is removed
SELECT 
    TABLE_NAME,
    COLUMN_NAME
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
AND TABLE_NAME = 'rooms';
