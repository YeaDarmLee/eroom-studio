CREATE TABLE IF NOT EXISTS branch_floors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    branch_id INT UNSIGNED NOT NULL,
    floor VARCHAR(20) NOT NULL,
    floor_plan_image VARCHAR(255),
    FOREIGN KEY (branch_id) REFERENCES branches(id),
    UNIQUE KEY unique_branch_floor (branch_id, floor)
);
