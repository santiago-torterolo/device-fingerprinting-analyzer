"""
Synthetic data generator for device fingerprinting.
Creates realistic fraud patterns: normal devices, fraud rings, and crossings.
GDPR compliant: All PII is hashed before storage.
"""

import uuid
import random
from datetime import datetime, timedelta
from faker import Faker
from app import create_app, db
from app.utils import hash_pii, hash_ip_address, anonymize_email, tokenize_card
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

fake = Faker()

app = create_app('development')


class DataGenerator:
    """Generate synthetic device fingerprinting data with fraud patterns."""
    
    def __init__(self):
        self.app_context = app.app_context()
        self.app_context.push()
    
    def generate_normal_device(self):
        """Generate a normal device with realistic fingerprint."""
        os_choices = ['Windows', 'macOS', 'iOS', 'Android']
        browser_choices = ['Chrome', 'Firefox', 'Safari', 'Edge']
        
        return {
            'device_hash': hash_pii(str(uuid.uuid4())),
            'os': random.choice(os_choices),
            'os_version': f"{random.randint(10, 15)}.0",
            'browser': random.choice(browser_choices),
            'browser_version': f"{random.randint(100, 130)}.0",
            'screen_resolution': random.choice(['1920x1080', '1366x768', '2560x1440', '375x812']),
            'timezone': fake.timezone(),
            'language': random.choice(['en', 'es', 'de', 'fr', 'pt']),
            'is_vpn': random.random() < 0.05,
            'ip_hash': hash_ip_address(fake.ipv4()),
            'risk_score': 0.0,
            'created_at': datetime.utcnow() - timedelta(days=random.randint(1, 365))
        }
    
    def generate_normal_account(self):
        """Generate a normal account with KYC verification."""
        email = fake.email()
        
        return {
            'account_hash': hash_pii(email),
            'email_hash': hash_pii(email),
            'email_domain': anonymize_email(email)['domain'],
            'kyc_level': random.choice(['verified', 'pending', 'verified']),
            'kyc_verified_at': datetime.utcnow() - timedelta(days=random.randint(1, 180)),
            'account_age_days': random.randint(1, 365),
            'transaction_count': random.randint(1, 50),
            'risk_score': random.uniform(0, 20),
            'created_at': datetime.utcnow() - timedelta(days=random.randint(1, 365))
        }
    
    def generate_fraud_ring(self, size=5):
        """
        Generate a fraud ring: multiple accounts linked by shared device/IP/card.
        Simulates real fraud pattern.
        
        Args:
            size: Number of accounts in ring (default: 5)
        
        Returns:
            Dict with devices, accounts, and crossing details
        """
        ring_ip = fake.ipv4()
        ring_card = fake.credit_card_number()
        ring_bank_account = fake.iban()
        
        devices = [self.generate_normal_device() for _ in range(random.randint(2, 3))]
        for device in devices:
            device['ip_hash'] = hash_ip_address(ring_ip)
        
        accounts = []
        for i in range(size):
            account = {
                'account_hash': hash_pii(f"fraud_ring_{uuid.uuid4()}"),
                'email_hash': hash_pii(fake.email()),
                'email_domain': 'gmail.com',
                'kyc_level': random.choice(['verified', 'pending', 'rejected']),
                'kyc_verified_at': datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                'account_age_days': random.randint(1, 30),
                'transaction_count': random.randint(50, 200),
                'risk_score': random.uniform(60, 95),
                'created_at': datetime.utcnow() - timedelta(days=random.randint(1, 20))
            }
            accounts.append(account)
        
        return {
            'devices': devices,
            'accounts': accounts,
            'shared_ip': ring_ip,
            'shared_card': ring_card,
            'shared_bank': ring_bank_account
        }
    
    def insert_devices(self, devices):
        """Insert devices into database."""
        from src.models import Device
        
        for device_data in devices:
            device = Device(**device_data)
            db.session.add(device)
        
        db.session.commit()
        logger.info(f"Inserted {len(devices)} devices")
    
    def insert_accounts(self, accounts):
        """Insert accounts into database."""
        from src.models import Account
        
        for account_data in accounts:
            account = Account(**account_data)
            db.session.add(account)
        
        db.session.commit()
        logger.info(f"Inserted {len(accounts)} accounts")
    
    def insert_crossings(self, devices, accounts, shared_attributes=None):
        """
        Insert device-account crossings with shared attributes.
        
        Args:
            devices: List of Device objects
            accounts: List of Account objects
            shared_attributes: Dict of shared attributes (ip, card, bank, kyc)
        """
        from src.models import DeviceAccountCrossing
        
        for account in accounts:
            for device in devices:
                crossing_data = {
                    'device_id': device.device_id,
                    'account_id': account.account_id,
                    'crossing_count': 1,
                    'shared_attributes': shared_attributes or {},
                    'risk_flag': 'high' if shared_attributes and len(shared_attributes) > 1 else 'low',
                    'first_seen': datetime.utcnow()
                }
                
                crossing = DeviceAccountCrossing(**crossing_data)
                db.session.add(crossing)
        
        db.session.commit()
        logger.info(f"Inserted {len(accounts) * len(devices)} crossings")
    
    def generate_complete_dataset(self, n_normal_devices=800, n_fraud_rings=20):
        """
        Generate complete synthetic dataset.
        
        Creates:
        - 800 normal devices (1-2 accounts each)
        - 20 fraud rings (5-10 accounts per ring, same IP/card/bank)
        - Realistic fraud patterns
        
        Args:
            n_normal_devices: Number of normal devices
            n_fraud_rings: Number of fraud rings to create
        """
        logger.info("Starting data generation...")
        
        from src.models import Device, Account, DeviceAccountCrossing
        
        all_devices = []
        all_accounts = []
        all_crossings = []
        
        logger.info(f"Generating {n_normal_devices} normal devices...")
        for _ in range(n_normal_devices):
            device = self.generate_normal_device()
            device_obj = Device(**device)
            all_devices.append(device_obj)
            
            account = self.generate_normal_account()
            account_obj = Account(**account)
            all_accounts.append(account_obj)
            
            crossing = {
                'device_id': device_obj.device_id,
                'account_id': account_obj.account_id,
                'crossing_count': 1,
                'shared_attributes': {'ip': True},
                'risk_flag': 'low'
            }
            all_crossings.append(crossing)
        
        db.session.add_all(all_devices)
        db.session.add_all(all_accounts)
        db.session.commit()
        logger.info(f"Inserted {len(all_devices)} normal devices and accounts")
        
        logger.info(f"Generating {n_fraud_rings} fraud rings...")
        fraud_ring_devices = []
        fraud_ring_accounts = []
        
        for ring_idx in range(n_fraud_rings):
            ring = self.generate_fraud_ring(size=random.randint(5, 10))
            
            for device_data in ring['devices']:
                device_obj = Device(**device_data)
                fraud_ring_devices.append(device_obj)
            
            for account_data in ring['accounts']:
                account_obj = Account(**account_data)
                fraud_ring_accounts.append(account_obj)
        
        db.session.add_all(fraud_ring_devices)
        db.session.add_all(fraud_ring_accounts)
        db.session.commit()
        logger.info(f"Inserted {len(fraud_ring_devices)} fraud ring devices")
        logger.info(f"Inserted {len(fraud_ring_accounts)} fraud ring accounts")
        
        logger.info("Creating device-account crossings...")
        crossing_count = 0
        
        for account in all_accounts:
            device_idx = random.randint(0, len(all_devices) - 1)
            device = all_devices[device_idx]
            
            crossing = DeviceAccountCrossing(
                device_id=device.device_id,
                account_id=account.account_id,
                crossing_count=1,
                shared_attributes={'ip': True},
                risk_flag='low'
            )
            db.session.add(crossing)
            crossing_count += 1
        
        for account in fraud_ring_accounts:
            devices_in_ring = random.sample(fraud_ring_devices, min(3, len(fraud_ring_devices)))
            
            for device in devices_in_ring:
                crossing = DeviceAccountCrossing(
                    device_id=device.device_id,
                    account_id=account.account_id,
                    crossing_count=1,
                    shared_attributes={'ip': True, 'card': True, 'bank': True},
                    risk_flag='high'
                )
                db.session.add(crossing)
                crossing_count += 1
        
        db.session.commit()
        logger.info(f"Inserted {crossing_count} crossings")
        
        logger.info("Data generation complete!")
        logger.info(f"Summary:")
        logger.info(f"  - Total devices: {len(all_devices) + len(fraud_ring_devices)}")
        logger.info(f"  - Total accounts: {len(all_accounts) + len(fraud_ring_accounts)}")
        logger.info(f"  - Total crossings: {crossing_count}")


def main():
    """Main entry point for data generation."""
    generator = DataGenerator()
    generator.generate_complete_dataset(n_normal_devices=800, n_fraud_rings=20)


if __name__ == '__main__':
    main()
