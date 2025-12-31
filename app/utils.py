"""
Utility functions for GDPR-compliant data protection.
Hashing, tokenization, and encryption functions.
"""

import hashlib
import os
import json
from datetime import datetime, timedelta
from cryptography.fernet import Fernet


def hash_pii(value: str, salt: str = None) -> str:
    """
    Hash PII data using SHA256 with salt.
    
    Args:
        value: Data to hash (email, IP, etc)
        salt: Optional salt (default: SECRET_KEY from environment)
    
    Returns:
        SHA256 hashed value as hex string
    """
    if not value:
        return None
    
    salt = salt or os.getenv('SECRET_KEY', 'default-salt')
    message = f"{value}{salt}".encode('utf-8')
    return hashlib.sha256(message).hexdigest()


def tokenize_card(card_number: str, account_id: str) -> dict:
    """
    Tokenize credit card for secure storage.
    Only stores last 4 digits + hash.
    
    Args:
        card_number: Full card number
        account_id: Associated account ID
    
    Returns:
        Dict with 'last_four' and 'token'
    """
    last_four = card_number[-4:] if len(card_number) >= 4 else card_number
    token_input = f"{last_four}:{account_id}"
    
    return {
        'last_four': last_four,
        'token': hash_pii(token_input)
    }


def hash_ip_address(ip: str) -> str:
    """
    Hash IP address for geographic analysis.
    
    Args:
        ip: IP address string
    
    Returns:
        SHA256 hashed IP
    """
    return hash_pii(ip)


def anonymize_email(email: str) -> dict:
    """
    Anonymize email by hashing + storing domain only.
    
    Example:
        john.doe@gmail.com → {domain: 'gmail.com', hash: 'abc123...'}
    
    Args:
        email: Full email address
    
    Returns:
        Dict with 'domain' and 'hash', or None if invalid
    """
    if not email or '@' not in email:
        return None
    
    domain = email.split('@')[1]
    
    return {
        'domain': domain,
        'hash': hash_pii(email)
    }


def encrypt_sensitive_data(data: dict, key: str = None) -> str:
    """
    Encrypt sensitive data using Fernet (AES-128).
    
    Args:
        data: Dictionary to encrypt
        key: Encryption key (default: ENCRYPTION_KEY from environment)
    
    Returns:
        Encrypted string
    """
    key = key or os.getenv('ENCRYPTION_KEY', Fernet.generate_key().decode())
    cipher = Fernet(key)
    plaintext = json.dumps(data).encode('utf-8')
    return cipher.encrypt(plaintext).decode('utf-8')


def decrypt_sensitive_data(encrypted: str, key: str = None) -> dict:
    """
    Decrypt previously encrypted data.
    
    Args:
        encrypted: Encrypted string
        key: Encryption key
    
    Returns:
        Decrypted dictionary
    """
    key = key or os.getenv('ENCRYPTION_KEY')
    cipher = Fernet(key)
    plaintext = cipher.decrypt(encrypted.encode('utf-8'))
    return json.loads(plaintext.decode('utf-8'))


def is_data_expired(created_at: datetime, retention_days: int = 90) -> bool:
    """
    Check if data exceeds retention period per GDPR policy.
    
    Args:
        created_at: Timestamp data was created
        retention_days: Number of days to retain (default: 90)
    
    Returns:
        True if data should be deleted
    """
    expiration = created_at + timedelta(days=retention_days)
    return datetime.utcnow() > expiration


def calculate_device_fingerprint(attributes: dict) -> str:
    """
    Calculate device fingerprint from multiple attributes.
    
    Args:
        attributes: Dict with os, browser, resolution, timezone, language
    
    Returns:
        SHA256 hash of combined attributes
    """
    fingerprint_parts = [
        attributes.get('os', ''),
        attributes.get('browser', ''),
        attributes.get('resolution', ''),
        attributes.get('timezone', ''),
        attributes.get('language', ''),
    ]
    
    fingerprint_str = '|'.join(filter(None, fingerprint_parts))
    return hashlib.sha256(fingerprint_str.encode()).hexdigest()


def mask_pii_for_display(value: str, visible_chars: int = 4) -> str:
    """
    Mask PII for UI display.
    
    Example:
        'john.doe@gmail.com' → 'john****@gmail.com'
    
    Args:
        value: Value to mask
        visible_chars: Number of starting characters to show
    
    Returns:
        Masked string
    """
    if not value or len(value) <= visible_chars:
        return '*' * len(value)
    
    return value[:visible_chars] + '*' * (len(value) - visible_chars - 4) + value[-4:]
