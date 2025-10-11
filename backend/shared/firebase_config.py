# shared/firebase_config.py

import os
import firebase_admin
from firebase_admin import credentials, db

_firebase_initialized = False

def init_firebase():
    """Initialize Firebase Admin SDK (only once per app)"""
    global _firebase_initialized
    
    if not _firebase_initialized:
        json_path = os.getenv("JSON_PATH")
        database_url = os.getenv("DATABASE_URL")
        
        if not json_path or not database_url:
            raise ValueError("JSON_PATH and DATABASE_URL must be set")
        
        cred = credentials.Certificate(json_path)
        firebase_admin.initialize_app(cred, {"databaseURL": database_url})
        _firebase_initialized = True
    
    return db

def get_db_reference(path=""):
    """Get a Firebase database reference"""
    return db.reference(path)