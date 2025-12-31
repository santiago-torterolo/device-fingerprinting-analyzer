"""
Standalone data generator 
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
from datetime import datetime
from uuid import uuid4
from faker import Faker
from app import db, create_app
from src.models import Device, Account, DeviceAccountCrossing

fake = Faker()

def generate_demo_data():
    # Ensure data directory exists for DuckDB
    os.makedirs('data', exist_ok=True)
    
    app = create_app('development')
    
    with app.app_context():
        # Manual table creation to avoid SERIAL issues in DuckDB 1.1.0/SQLAlchemy
        conn = db.engine.connect()
        # DuckDB requires individual execution or specific handling for multi-statement strings sometimes
        # We'll use the connection to execute the DDL
        statements = [
            "DROP TABLE IF EXISTS device_account_crossings",
            "DROP TABLE IF EXISTS accounts",
            "DROP TABLE IF EXISTS devices",
            """CREATE TABLE devices (
                device_id VARCHAR(36) PRIMARY KEY,
                device_hash VARCHAR(64) UNIQUE,
                os VARCHAR(50),
                browser VARCHAR(50),
                screen_resolution VARCHAR(20),
                timezone VARCHAR(50),
                is_vpn BOOLEAN DEFAULT FALSE,
                is_datacenter BOOLEAN DEFAULT FALSE,
                risk_score FLOAT DEFAULT 0.0,
                risk_level VARCHAR(20) DEFAULT 'low',
                account_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE accounts (
                account_id VARCHAR(36) PRIMARY KEY,
                account_hash VARCHAR(64) UNIQUE,
                email_domain VARCHAR(100),
                kyc_level VARCHAR(20) DEFAULT 'pending',
                risk_score FLOAT DEFAULT 0.0,
                risk_level VARCHAR(20) DEFAULT 'low',
                device_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE device_account_crossings (
                id INTEGER PRIMARY KEY,
                device_id VARCHAR(36),
                account_id VARCHAR(36),
                risk_flag VARCHAR(50) DEFAULT 'low',
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )"""
        ]
        
        for stmt in statements:
            conn.execute(db.text(stmt))
        
        conn.commit()
        conn.close()
        
        # 1. Prepare data
        os_list = ['Windows', 'macOS', 'Linux', 'Android', 'iOS']
        browser_list = ['Chrome', 'Firefox', 'Safari', 'Edge']
        risk_levels_weights = {'low': (0.6, 1.0, 30.0), 'medium': (0.3, 31.0, 70.0), 'high': (0.1, 71.0, 100.0)}
        
        device_ids = [str(uuid4()) for _ in range(800)]
        account_ids = [str(uuid4()) for _ in range(200)]
        
        # 2. Generate crossings and counts
        crossings = []
        dev_counts = {rid: 0 for rid in device_ids}
        acc_counts = {rid: 0 for rid in account_ids}
        
        for i in range(1200):
            d_id = random.choice(device_ids)
            a_id = random.choice(account_ids)
            crossings.append({
                'id': i + 1,
                'device_id': d_id,
                'account_id': a_id,
                'risk_flag': random.choices(['low', 'medium', 'high'], weights=[0.8, 0.15, 0.05])[0]
            })
            dev_counts[d_id] += 1
            acc_counts[a_id] += 1

        # 3. Insert Devices
        print("Inserting devices...")
        for d_id in device_ids:
            level = random.choices(list(risk_levels_weights.keys()), weights=[w[0] for w in risk_levels_weights.values()])[0]
            m_s, M_s = risk_levels_weights[level][1], risk_levels_weights[level][2]
            conn.execute(db.text("INSERT INTO devices (device_id, device_hash, os, browser, risk_level, risk_score, account_count) VALUES (:id, :h, :os, :b, :l, :s, :c)"),
                        {'id': d_id, 'h': fake.sha256()[:64], 'os': random.choice(os_list), 'b': random.choice(browser_list), 'l': level, 's': random.uniform(m_s, M_s), 'c': dev_counts[d_id]})
        
        # 4. Insert Accounts
        print("Inserting accounts...")
        kyc_levels = ['verified', 'pending', 'rejected']
        for a_id in account_ids:
            level = random.choices(['low', 'medium', 'high'], weights=[0.7, 0.25, 0.05])[0]
            m_s, M_s = risk_levels_weights[level][1], risk_levels_weights[level][2]
            conn.execute(db.text("INSERT INTO accounts (account_id, account_hash, kyc_level, risk_level, risk_score, device_count) VALUES (:id, :h, :k, :l, :s, :c)"),
                        {'id': a_id, 'h': fake.sha256()[:64], 'k': random.choice(kyc_levels), 'l': level, 's': random.uniform(m_s, M_s), 'c': acc_counts[a_id]})
        
        # 5. Insert Crossings
        print("Inserting crossings...")
        for c in crossings:
            conn.execute(db.text("INSERT INTO device_account_crossings (id, device_id, account_id, risk_flag) VALUES (:id, :d, :a, :r)"),
                        {'id': c['id'], 'd': c['device_id'], 'a': c['account_id'], 'r': c['risk_flag']})
        
        conn.commit()
        conn.close()
        print(f"Data generation complete: 800 devices, 200 accounts, 1200 crossings.")
        print("Database ready. Run: python main.py")

if __name__ == "__main__":
    generate_demo_data()
