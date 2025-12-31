-- Schema definition for Device Fingerprinting DB
-- Use this if you want to create tables manually via psql

CREATE TABLE IF NOT EXISTS devices (
    device_id VARCHAR(36) PRIMARY KEY,
    device_hash VARCHAR(64) UNIQUE NOT NULL,
    os VARCHAR(50),
    browser VARCHAR(50),
    risk_score DECIMAL(5,2) DEFAULT 0.0,
    risk_level VARCHAR(20) DEFAULT 'low',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS accounts (
    account_id VARCHAR(36) PRIMARY KEY,
    email_domain VARCHAR(100),
    kyc_level VARCHAR(20) DEFAULT 'pending',
    risk_score DECIMAL(5,2) DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS device_account_crossings (
    crossing_id SERIAL PRIMARY KEY,
    device_id VARCHAR(36) REFERENCES devices(device_id) ON DELETE CASCADE,
    account_id VARCHAR(36) REFERENCES accounts(account_id) ON DELETE CASCADE,
    risk_flag VARCHAR(50) DEFAULT 'low',
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_device_account UNIQUE(device_id, account_id)
);

CREATE INDEX idx_device_risk ON devices(risk_score);
CREATE INDEX idx_account_risk ON accounts(risk_score);
