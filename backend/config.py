# backend/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration"""
    
    # Flask
    DEBUG = True
    HOST = '0.0.0.0'
    PORT = int(os.getenv('PORT', 5001))
    
    # Supabase
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    
    # eGauge
    EGAUGE_USER = os.getenv('EGUSR', 'evamexico')
    EGAUGE_PASSWORD = os.getenv('EGPWD', '12345678')
    
    # CORS
    CORS_ORIGINS = [
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]
    
    # Data extraction limits
    MAX_DAYS_HISTORY = 365
    BATCH_INSERT_SIZE = 1000
    
    @staticmethod
    def validate():
        """Validate required configuration"""
        if not Config.SUPABASE_URL or not Config.SUPABASE_KEY:
            raise ValueError(
                "Missing Supabase credentials. Please set SUPABASE_URL and "
                "SUPABASE_KEY in your .env file"
            )
        
        if 'your-' in Config.SUPABASE_URL or 'your-' in Config.SUPABASE_KEY:
            raise ValueError(
                "Please replace placeholder values in .env file with actual "
                "Supabase credentials"
            )
