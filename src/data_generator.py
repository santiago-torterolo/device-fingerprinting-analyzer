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
        
        print("Tables created successfully")
        
        # Generate devices
        devices = []
        os_list = ['Windows', 'macOS', 'Linux', 'Android', 'iOS']
        browser_list = ['Chrome', 'Firefox', 'Safari', 'Edge']
        risk_levels = ['low', 'medium', 'high']
        
        for i in range(800):
            device = Device(
                device_id=str(uuid4()),
                device_hash=fake.sha256()[:64],
                os=random.choice(os_list),
                browser=random.choice(browser_list),
                risk_level=random.choices(risk_levels, weights=[0.6, 0.3, 0.1])[0]
            )
            db.session.add(device)
            devices.append(device)
        
        db.session.commit()
        print(f"Created {len(devices)} devices")
        
        # Generate accounts
        accounts = []
        kyc_levels = ['verified', 'pending', 'rejected']
        
        for i in range(200):
            account = Account(
                account_id=str(uuid4()),
                account_hash=fake.sha256()[:64],
                kyc_level=random.choices(kyc_levels, weights=[0.7, 0.25, 0.05])[0],
                risk_level=random.choices(risk_levels, weights=[0.7, 0.25, 0.05])[0]
            )
            db.session.add(account)
            accounts.append(account)
        
        db.session.commit()
        print(f"Created {len(accounts)} accounts")
        
        # Generate crossings
        crossings_count = 0
        for i in range(1200):
            device = random.choice(devices)
            account = random.choice(accounts)
            
            crossing = DeviceAccountCrossing(
                id=i + 1,
                device_id=device.device_id,
                account_id=account.account_id,
                risk_flag=random.choices(risk_levels, weights=[0.8, 0.15, 0.05])[0]
            )
            db.session.add(crossing)
            crossings_count += 1
        
        db.session.commit()
        print(f"Created {crossings_count} crossings")
        print("Database ready. Run: flask run")

if __name__ == "__main__":
    generate_demo_data()
