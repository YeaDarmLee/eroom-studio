-- Add floor column to rooms table
-- This allows rooms to be organized by floor within each branch

ALTER TABLE rooms 
ADD COLUMN floor VARCHAR(20) AFTER branch_id,
ADD INDEX idx_floor (floor);

-- Set default floor for existing rooms
-- All existing rooms will be assigned to 1F (1st floor)
UPDATE rooms SET floor = '1F' WHERE floor IS NULL;

-- Add comment for documentation
ALTER TABLE rooms 
MODIFY COLUMN floor VARCHAR(20) 
COMMENT 'Floor designation (e.g., B1, 1F, 2F, 3F)';

-- Verify the changes
SELECT 
    TABLE_NAME,
    COLUMN_NAME,
    COLUMN_TYPE,
    IS_NULLABLE,
    COLUMN_COMMENT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
AND TABLE_NAME = 'rooms'
AND COLUMN_NAME = 'floor';
