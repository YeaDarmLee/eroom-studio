-- Add password_hash column to users table
USE eroom;

ALTER TABLE users ADD COLUMN password_hash VARCHAR(255) NULL;

-- Verify the column was added
DESCRIBE users;
