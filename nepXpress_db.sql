-- ============================================================
--  NepXpress  –  Database Schema
-- ============================================================

CREATE DATABASE nepXpress CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE nepXpress;

-- ── Users (customers + admins) ────────────────────────────────────────── --
CREATE TABLE  users (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(120)  NOT NULL,
    email         VARCHAR(180)  NOT NULL UNIQUE,
    password_hash VARCHAR(255)  NOT NULL,
    role          ENUM('customer','admin','superadmin') NOT NULL DEFAULT 'customer',
    status        ENUM('active','inactive') NOT NULL DEFAULT 'active',
    phone         VARCHAR(20),
    address       TEXT,
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ── Delivery Agents ───────────────────────────────────────────────────── --
CREATE TABLE delivery_agents (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(120) NOT NULL,
    email      VARCHAR(180) NOT NULL UNIQUE,
    phone      VARCHAR(20),
    status     ENUM('active','inactive','offline') NOT NULL DEFAULT 'active',
    zone       VARCHAR(100),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ── Shipments ─────────────────────────────────────────────────────────── --
CREATE TABLE shipments (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    tracking_id  VARCHAR(30)   NOT NULL UNIQUE,
    customer_id  INT           NOT NULL,
    agent_id     INT,
    destination  VARCHAR(200)  NOT NULL,
    status       ENUM('pending','processing','in_transit','delivered','delayed','cancelled')
                 NOT NULL DEFAULT 'pending',
    amount       DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    notes        TEXT,
    created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES users(id)            ON DELETE CASCADE,
    FOREIGN KEY (agent_id)    REFERENCES delivery_agents(id)  ON DELETE SET NULL
);

-- ── System Alerts ─────────────────────────────────────────────────────── --
CREATE TABLE system_alerts (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    type         ENUM('warning','info','success','error') NOT NULL DEFAULT 'info',
    title        VARCHAR(200) NOT NULL,
    message      TEXT,
    reference_id VARCHAR(50),        -- e.g. tracking_id of related shipment
    is_read      TINYINT(1) NOT NULL DEFAULT 0,
    created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ------system settings----------------------------------------------------------- --
CREATE TABLE IF NOT EXISTS system_settings (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    setting_key   VARCHAR(100) NOT NULL UNIQUE,
    setting_value TEXT,
    updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);




-- ============================================================
--  Seed Data  
-- ============================================================

-- Admin user  (password: admin123)
INSERT IGNORE INTO users (name, email, password_hash, role, status) VALUES
('Samyog Rai', 'samyog@gmail.com',
 SHA2('admin123', 256), 'admin', 'active');

-- Sample customers
INSERT IGNORE INTO users (name, email, password_hash, role, status, created_at) VALUES
('John Doe',    'john@gmail.com',   SHA2('pass123',256), 'customer', 'active',   '2026-05-18 09:00:00'),
('Priya Sharma','priya@gmail.com',  SHA2('pass123',256), 'customer', 'active',   '2026-05-17 10:00:00'),
('Rajan Lama',  'rajan@gmail.com',  SHA2('pass123',256), 'customer', 'inactive', '2026-05-16 11:00:00'),
('Sita Gurung', 'sita@gmail.com',   SHA2('pass123',256), 'customer', 'active',   '2026-05-15 12:00:00'),
('Hari Tamang', 'hari@gmail.com',   SHA2('pass123',256), 'customer', 'active',   '2026-05-14 08:00:00'),
('Nisha Karki', 'nisha@gmail.com',  SHA2('pass123',256), 'customer', 'active',   '2026-05-17 14:00:00');

-- Delivery agents
INSERT IGNORE INTO delivery_agents (name, email, phone, status, zone) VALUES
('Arjun K.',  'arjun@nepxpress.com',  '9801000001', 'active',  'Kathmandu'),
('Bikram T.', 'bikram@nepxpress.com', '9801000002', 'active',  'Pokhara'),
('Sanjay M.', 'sanjay@nepxpress.com', '9801000003', 'active',  'Lalitpur'),
('Deepak R.', 'deepak@nepxpress.com', '9801000004', 'offline', 'Biratnagar');

-- Shipments (tracking IDs matching screenshots)
INSERT IGNORE INTO shipments (tracking_id, customer_id, agent_id, destination, status, amount, created_at) VALUES
('NXP-2849', 2, 1, 'Kathmandu', 'in_transit', 800.00,  '2026-05-18 08:00:00'),
('NXP-2848', 3, 2, 'Pokhara',   'processing', 1500.00, '2026-05-18 07:00:00'),
('NXP-2847', 4, 3, 'Lalitpur',  'delivered',  600.00,  '2026-05-17 09:00:00'),
('NXP-2846', 5, 1, 'Bhaktapur', 'delivered',  1200.00, '2026-05-16 10:00:00'),
('NXP-2845', 6, 4, 'Biratnagar','delayed',    950.00,  '2026-05-15 11:00:00'),
('NXP-2844', 7, 2, 'Dharan',    'delivered',  700.00,  '2026-05-15 08:00:00');

-- System alerts
INSERT IGNORE INTO system_alerts (type, title, message, reference_id, is_read, created_at) VALUES
('warning', 'Delivery Delayed',    '#NXP-2845 — weather disruption on Biratnagar route', 'NXP-2845', 0, DATE_SUB(NOW(), INTERVAL 3 HOUR)),
('error',   'Agent Offline',       'Deepak R. hasn''t checked in for 4 hours',           NULL,        0, DATE_SUB(NOW(), INTERVAL 4 HOUR)),
('success', 'Payment Confirmed',   'Order #NXP-2846 — NPR 1,200 received',               'NXP-2846', 1, DATE_SUB(NOW(), INTERVAL 5 HOUR)),
('info',    'New User Registered', 'Nisha Karki joined as a customer',                   NULL,        1, DATE_SUB(NOW(), INTERVAL 1 DAY));

-- System settings
INSERT IGNORE INTO system_settings (setting_key, setting_value) VALUES
('site_name',      'NepXpress'),
('contact_email',  'admin@nepxpress.com'),
('currency',       'NPR'),
('support_phone',  ''),
('address',        'Kathmandu, Nepal'),
('notif_delay',         '1'),
('notif_new_user',      '1'),
('notif_payment',       '1'),
('notif_agent_offline', '1'),
('notif_new_shipment',  '0');



DESCRIBE users;
ALTER TABLE users ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'active';
INSERT IGNORE INTO users (name, email, password, role) VALUES
('John Doe',    'john@gmail.com',   SHA2('pass123',256), 'customer'),
('Priya Sharma','priya@gmail.com',  SHA2('pass123',256), 'customer'),
('Rajan Lama',  'rajan@gmail.com',  SHA2('pass123',256), 'customer'),
('Sita Gurung', 'sita@gmail.com',   SHA2('pass123',256), 'customer'),
('Hari Tamang', 'hari@gmail.com',   SHA2('pass123',256), 'customer'),
('Nisha Karki', 'nisha@gmail.com',  SHA2('pass123',256), 'customer');
SELECT id, name, role, status FROM users ORDER BY id;


SET SQL_SAFE_UPDATES = 0;
DELETE FROM shipments;
SET SQL_SAFE_UPDATES = 1;
INSERT INTO shipments (tracking_id, customer_id, agent_id, destination, status, amount, created_at) VALUES
('NXP-2849', 163, 1, 'Kathmandu',  'in_transit', 800.00,  '2026-05-18 08:00:00'),
('NXP-2848', 164, 2, 'Pokhara',    'processing', 1500.00, '2026-05-18 07:00:00'),
('NXP-2847', 165, 3, 'Lalitpur',   'delivered',  600.00,  '2026-05-17 09:00:00'),
('NXP-2846', 166, 1, 'Bhaktapur',  'delivered',  1200.00, '2026-05-16 10:00:00'),
('NXP-2845', 167, 4, 'Biratnagar', 'delayed',    950.00,  '2026-05-15 11:00:00'),
('NXP-2844', 168, 2, 'Dharan',     'delivered',  700.00,  '2026-05-15 08:00:00');
SELECT id, tracking_id, customer_id, status FROM shipments;


UPDATE shipments SET created_at = NOW() WHERE tracking_id IN 
('NXP-2849','NXP-2848','NXP-2847','NXP-2846','NXP-2845','NXP-2844');

-- Add some last month shipments for comparison
INSERT INTO shipments (tracking_id, customer_id, agent_id, destination, status, amount, created_at) VALUES
('NXP-2843', 163, 1, 'Kathmandu', 'delivered', 900.00, DATE_SUB(NOW(), INTERVAL 35 DAY)),
('NXP-2842', 164, 2, 'Pokhara',   'delivered', 750.00, DATE_SUB(NOW(), INTERVAL 38 DAY));

ALTER TABLE users 
ADD COLUMN security_answer VARCHAR(255) DEFAULT NULL;

DESCRIBE delivery_agents;

SELECT * FROM delivery_agents;


