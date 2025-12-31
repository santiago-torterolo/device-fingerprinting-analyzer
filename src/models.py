"""
SQLAlchemy ORM models for device fingerprinting data.
Defines database schema for devices, accounts, and their relationships.
"""

from datetime import datetime
from uuid import uuid4
from app import db


class Device(db.Model):
    """
    Device fingerprint model.
    Represents unique device identifiers and their characteristics.
    """
    __tablename__ = 'devices'
    
    device_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    device_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)
    os = db.Column(db.String(50))
    os_version = db.Column(db.String(50))
    browser = db.Column(db.String(50))
    browser_version = db.Column(db.String(50))
    screen_resolution = db.Column(db.String(20))
    user_agent_hash = db.Column(db.String(64))
    timezone = db.Column(db.String(50))
    language = db.Column(db.String(10))
    is_vpn = db.Column(db.Boolean, default=False)
    is_datacenter = db.Column(db.Boolean, default=False)
    risk_score = db.Column(db.Numeric(5, 2), default=0.0, index=True)
    risk_level = db.Column(db.String(20), default='low', index=True)
    account_count = db.Column(db.Integer, default=0, index=True)
    last_risk_calculation = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    
    crossings = db.relationship(
        'DeviceAccountCrossing',
        backref='device',
        lazy='select',
        cascade='all, delete-orphan'
    )
    
    def __repr__(self):
        return f"<Device {self.device_id[:8]}... {self.os} {self.browser}>"
    
    def to_dict(self):
        """Convert device to dictionary."""
        return {
            'device_id': self.device_id,
            'device_hash': self.device_hash,
            'os': self.os,
            'browser': self.browser,
            'timezone': self.timezone,
            'is_vpn': self.is_vpn,
            'risk_score': float(self.risk_score) if self.risk_score else 0.0,
            'risk_level': self.risk_level,
            'account_count': self.account_count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Account(db.Model):
    """
    Account model.
    Represents user accounts with KYC and verification status.
    All PII is hashed before storage for GDPR compliance.
    """
    __tablename__ = 'accounts'
    
    account_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    account_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email_hash = db.Column(db.String(64))
    email_domain = db.Column(db.String(100))
    kyc_level = db.Column(db.String(20), default='pending', index=True)
    kyc_verified_at = db.Column(db.DateTime)
    account_age_days = db.Column(db.Integer, default=0)
    transaction_count = db.Column(db.Integer, default=0)
    risk_score = db.Column(db.Numeric(5, 2), default=0.0, index=True)
    risk_level = db.Column(db.String(20), default='low')
    is_suspended = db.Column(db.Boolean, default=False)
    device_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_transaction = db.Column(db.DateTime)
    
    crossings = db.relationship(
        'DeviceAccountCrossing',
        backref='account',
        lazy='select',
        cascade='all, delete-orphan'
    )
    payment_methods = db.relationship(
        'PaymentMethod',
        backref='account',
        lazy='select',
        cascade='all, delete-orphan'
    )
    
    def __repr__(self):
        return f"<Account {self.account_id[:8]}... KYC:{self.kyc_level}>"
    
    def to_dict(self):
        """Convert account to dictionary."""
        return {
            'account_id': self.account_id,
            'account_hash': self.account_hash,
            'kyc_level': self.kyc_level,
            'email_domain': self.email_domain,
            'risk_score': float(self.risk_score) if self.risk_score else 0.0,
            'risk_level': self.risk_level,
            'device_count': self.device_count,
            'transaction_count': self.transaction_count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class DeviceAccountCrossing(db.Model):
    """
    Device-Account crossing model (CORE).
    Links devices to accounts and tracks shared attributes.
    Essential for fraud ring detection.
    """
    __tablename__ = 'device_account_crossings'
    
    crossing_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_id = db.Column(
        db.String(36),
        db.ForeignKey('devices.device_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    account_id = db.Column(
        db.String(36),
        db.ForeignKey('accounts.account_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    crossing_count = db.Column(db.Integer, default=1)
    is_primary = db.Column(db.Boolean, default=False)
    shared_attributes = db.Column(db.JSON)
    risk_flag = db.Column(db.String(50), default='low', index=True)
    fraud_ring_id = db.Column(db.Integer, index=True)
    first_seen = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('device_id', 'account_id', name='uq_device_account'),
    )
    
    def __repr__(self):
        return f"<Crossing {self.device_id[:8]}...→{self.account_id[:8]}... risk:{self.risk_flag}>"
    
    def to_dict(self):
        """Convert crossing to dictionary."""
        return {
            'crossing_id': self.crossing_id,
            'device_id': self.device_id,
            'account_id': self.account_id,
            'shared_attributes': self.shared_attributes,
            'risk_flag': self.risk_flag,
            'is_primary': self.is_primary,
            'first_seen': self.first_seen.isoformat() if self.first_seen else None
        }


class SharedAttribute(db.Model):
    """
    Shared attribute model.
    Tracks IP addresses, payment tokens, bank accounts shared across devices/accounts.
    """
    __tablename__ = 'shared_attributes'
    
    attribute_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    crossing_id = db.Column(
        db.Integer,
        db.ForeignKey('device_account_crossings.crossing_id', ondelete='CASCADE'),
        nullable=False
    )
    attribute_type = db.Column(db.String(50), nullable=False, index=True)
    attribute_value_hash = db.Column(db.String(64), nullable=False, index=True)
    shared_count = db.Column(db.Integer, default=1, index=True)
    risk_weight = db.Column(db.Numeric(3, 2), default=0.5)
    last_occurrence = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<SharedAttribute type:{self.attribute_type} count:{self.shared_count}>"


class PaymentMethod(db.Model):
    """
    Payment method model (tokenized).
    Stores last 4 digits + token hash for payment tracking.
    """
    __tablename__ = 'payment_methods'
    
    payment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    account_id = db.Column(
        db.String(36),
        db.ForeignKey('accounts.account_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    payment_token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    last_four = db.Column(db.String(4))
    payment_type = db.Column(db.String(20))
    is_primary = db.Column(db.Boolean, default=False)
    device_count = db.Column(db.Integer, default=1, index=True)
    first_used = db.Column(db.DateTime, default=datetime.utcnow)
    last_used = db.Column(db.DateTime, default=datetime.utcnow)
    risk_score = db.Column(db.Numeric(5, 2), default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<PaymentMethod {self.last_four}>"


class IPAddress(db.Model):
    """
    IP address model.
    Stores geographic and ISP information with hashed IP.
    """
    __tablename__ = 'ip_addresses'
    
    ip_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ip_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)
    country = db.Column(db.String(2), index=True)
    region = db.Column(db.String(100))
    city = db.Column(db.String(100))
    isp = db.Column(db.String(100))
    asn = db.Column(db.Integer)
    is_datacenter = db.Column(db.Boolean, default=False, index=True)
    is_vpn_provider = db.Column(db.Boolean, default=False)
    is_residential = db.Column(db.Boolean, default=True)
    device_count = db.Column(db.Integer, default=1, index=True)
    account_count = db.Column(db.Integer, default=1)
    risk_score = db.Column(db.Numeric(5, 2), default=0.0)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<IP {self.country} {self.city}>"


class FraudRing(db.Model):
    """
    Fraud ring model.
    Represents clusters of accounts engaged in coordinated fraud.
    """
    __tablename__ = 'fraud_rings'
    
    ring_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cluster_name = db.Column(db.String(100))
    account_count = db.Column(db.Integer, default=0)
    device_count = db.Column(db.Integer, default=0)
    ip_count = db.Column(db.Integer, default=0)
    card_count = db.Column(db.Integer, default=0)
    bank_count = db.Column(db.Integer, default=0)
    connection_strength = db.Column(db.Integer, default=0)
    risk_level = db.Column(db.String(20), default='high')
    is_active = db.Column(db.Boolean, default=True, index=True)
    suspected_fraud_type = db.Column(db.String(100))
    discovered_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<FraudRing {self.cluster_name} accounts:{self.account_count}>"


class RiskScoringHistory(db.Model):
    """
    Risk scoring history model.
    Audit trail of risk calculations for devices and accounts.
    """
    __tablename__ = 'risk_scoring_history'
    
    history_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_id = db.Column(
        db.String(36),
        db.ForeignKey('devices.device_id', ondelete='CASCADE'),
        index=True
    )
    account_id = db.Column(
        db.String(36),
        db.ForeignKey('accounts.account_id', ondelete='CASCADE'),
        index=True
    )
    risk_score = db.Column(db.Numeric(5, 2))
    risk_level = db.Column(db.String(20))
    scoring_factors = db.Column(db.JSON)
    calculated_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<RiskHistory score:{self.risk_score}>"


class AuditLog(db.Model):
    """
    Audit log model.
    GDPR compliance: tracks who accessed what data and when.
    """
    __tablename__ = 'audit_log'
    
    log_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    action = db.Column(db.String(50), index=True)
    resource_type = db.Column(db.String(50))
    resource_id = db.Column(db.String(100), index=True)
    user_hash = db.Column(db.String(64))
    reason = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    ip_address_hash = db.Column(db.String(64))
    
    def __repr__(self):
        return f"<AuditLog {self.action} {self.resource_type}>"
