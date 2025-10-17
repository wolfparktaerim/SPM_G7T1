# shared/__init__.py
"""Shared utilities for all microservices"""

from .firebase_config import init_firebase, get_db_reference
from .utils import (
    current_timestamp, 
    validate_epoch_timestamp, 
    validate_status,
    days_until_deadline, 
    format_deadline      
)

__all__ = [
    'init_firebase',
    'get_db_reference',
    'current_timestamp',
    'validate_epoch_timestamp',
    'validate_status',
    'days_until_deadline',  
    'format_deadline'      
]