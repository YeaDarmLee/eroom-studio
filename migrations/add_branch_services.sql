-- Add branch_services table
CREATE TABLE IF NOT EXISTS branch_services (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    branch_id BIGINT UNSIGNED NOT NULL,
    service_type VARCHAR(20) NOT NULL COMMENT 'common or specialized',
    name VARCHAR(100) NOT NULL,
    description VARCHAR(200),
    icon VARCHAR(50) COMMENT 'Remix Icon class name',
    order_index INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (branch_id) REFERENCES branches(id) ON DELETE CASCADE,
    INDEX idx_branch_type (branch_id, service_type),
    INDEX idx_order (branch_id, service_type, order_index)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert sample common services for existing branches
INSERT INTO branch_services (branch_id, service_type, name, description, icon, order_index)
SELECT id, 'common', '초고속 WiFi', '1Gbps 속도 보장', 'ri-wifi-line', 1
FROM branches;

INSERT INTO branch_services (branch_id, service_type, name, description, icon, order_index)
SELECT id, 'common', '냉난방 시설', '개별 온도 조절', 'ri-air-conditioning-line', 2
FROM branches;

INSERT INTO branch_services (branch_id, service_type, name, description, icon, order_index)
SELECT id, 'common', '정수기', '냉온수 무료 제공', 'ri-water-flash-line', 3
FROM branches;

INSERT INTO branch_services (branch_id, service_type, name, description, icon, order_index)
SELECT id, 'common', '보안 시스템', '24시간 CCTV', 'ri-shield-keyhole-line', 4
FROM branches;

-- Insert sample specialized services for existing branches
INSERT INTO branch_services (branch_id, service_type, name, description, icon, order_index)
SELECT id, 'specialized', '프리미엄 마이크', 'Shure SM7B 구비', 'ri-mic-2-line', 1
FROM branches;

INSERT INTO branch_services (branch_id, service_type, name, description, icon, order_index)
SELECT id, 'specialized', '모니터 스피커', 'Yamaha HS8', 'ri-speaker-line', 2
FROM branches;

INSERT INTO branch_services (branch_id, service_type, name, description, icon, order_index)
SELECT id, 'specialized', '디지털 피아노', 'Roland FP-90X', 'ri-keyboard-line', 3
FROM branches;

INSERT INTO branch_services (branch_id, service_type, name, description, icon, order_index)
SELECT id, 'specialized', '녹음 장비', 'Pro Tools 시스템', 'ri-computer-line', 4
FROM branches;
