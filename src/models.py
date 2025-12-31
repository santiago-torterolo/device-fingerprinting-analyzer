"""
DuckDB-compatible models.
"""

from datetime import datetime
from uuid import uuid4
from app import db


class Device(db.Model):
    __tablename__ = 'devices'
    
    device_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    device_hash = db.Column(db.String(64), unique=True, nullable=False)
    os = db.Column(db.String(50))
    browser = db.Column(db.String(50))
    screen_resolution = db.Column(db.String(20))
    timezone = db.Column(db.String(50))
    is_vpn = db.Column(db.Boolean, default=False)
    is_datacenter = db.Column(db.Boolean, default=False)
    risk_score = db.Column(db.Float, default=0.0)
    risk_level = db.Column(db.String(20), default='low')
    account_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'device_id': self.device_id,
            'device_hash': self.device_hash,
            'os': self.os,
            'browser': self.browser,
            'timezone': self.timezone,
            'is_vpn': self.is_vpn,
            'risk_score': self.risk_score,
            'risk_level': self.risk_level,
            'account_count': self.account_count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Account(db.Model):
    __tablename__ = 'accounts'
    
    account_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    account_hash = db.Column(db.String(64), unique=True, nullable=False)
    email_domain = db.Column(db.String(100))
    kyc_level = db.Column(db.String(20), default='pending')
    risk_score = db.Column(db.Float, default=0.0)
    risk_level = db.Column(db.String(20), default='low')
    device_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'account_id': self.account_id,
            'account_hash': self.account_hash,
            'kyc_level': self.kyc_level,
            'email_domain': self.email_domain,
            'risk_score': self.risk_score,
            'risk_level': self.risk_level,
            'device_count': self.device_count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class DeviceAccountCrossing(db.Model):
    __tablename__ = 'device_account_crossings'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(36), nullable=False)
    account_id = db.Column(db.String(36), nullable=False)
    risk_flag = db.Column(db.String(50), default='low')
    first_seen = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'device_id': self.device_id,
            'account_id': self.account_id,
            'risk_flag': self.risk_flag,
            'first_seen': self.first_seen.isoformat() if self.first_seen else None
        }
