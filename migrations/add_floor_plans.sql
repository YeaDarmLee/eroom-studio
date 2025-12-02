-- Create branch_floors table
CREATE TABLE IF NOT EXISTS branch_floors (
    id INT PRIMARY KEY AUTO_INCREMENT,
    branch_id INT NOT NULL,
    floor VARCHAR(20) NOT NULL,
    floor_plan_image VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (branch_id) REFERENCES branches(id) ON DELETE CASCADE,
    UNIQUE KEY unique_branch_floor (branch_id, floor)
);

-- Add coordinate columns to rooms table
-- We check if columns exist before adding to avoid errors on re-run
SET @dbname = DATABASE();
SET @tablename = "rooms";
SET @columnname = "position_x";

SET @preparedStatement = (SELECT IF(
  (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE
      (table_name = @tablename)
      AND (table_schema = @dbname)
      AND (column_name = @columnname)
  ) > 0,
  "SELECT 1",
  "ALTER TABLE rooms ADD COLUMN position_x FLOAT DEFAULT 0 COMMENT 'X position in %', ADD COLUMN position_y FLOAT DEFAULT 0 COMMENT 'Y position in %', ADD COLUMN width FLOAT DEFAULT 10 COMMENT 'Width in %', ADD COLUMN height FLOAT DEFAULT 10 COMMENT 'Height in %';"
));

PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- Verify changes
SELECT TABLE_NAME, COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME IN ('branch_floors', 'rooms') AND TABLE_SCHEMA = DATABASE();
