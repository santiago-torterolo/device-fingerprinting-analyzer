"""
Application configuration.
Environment variables and database setup for different deployment contexts.
Supports DuckDB (local) and PostgreSQL (production).
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration shared across all environments."""
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = os.getenv('SQLALCHEMY_ECHO', 'False').lower() == 'true'
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = True


class DevelopmentConfig(Config):
    """Development environment configuration - DUCKDB."""
    
    DEBUG = True
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'duckdb:///data/device_fp.db'  # ← DUCKDB LOCAL
    )


class TestingConfig(Config):
    """Testing environment configuration."""
    
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


class ProductionConfig(Config):
    """Production environment configuration - PostgreSQL."""
    
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL', 
        'postgresql://fraud_analyst:dev123456@localhost:5432/device_fp_db'
    )


def get_config():
    """
    Get configuration based on FLASK_ENV environment variable.
    
    Returns:
        Configuration class for current environment
    """
    env = os.getenv('FLASK_ENV', 'development').lower()
    
    config_map = {
        'development': DevelopmentConfig,
        'testing': TestingConfig,
        'production': ProductionConfig,
    }
    
    return config_map.get(env, DevelopmentConfig)
