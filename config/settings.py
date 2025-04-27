"""
Configuration management module for the Rose Tracker application.
Loads and validates environment variables using python-dotenv.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Set

# Load environment variables from .env file
env_path = Path('.') / '.env'
load_dotenv(env_path)

class Settings:
    """Application settings loaded from environment variables with defaults."""
    
    def __init__(self):
        # Flask Configuration
        self.FLASK_APP: str = os.getenv('FLASK_APP', 'app.py')
        self.FLASK_ENV: str = os.getenv('FLASK_ENV', 'development')
        self.FLASK_DEBUG: bool = bool(int(os.getenv('FLASK_DEBUG', '1')))
        self.SECRET_KEY: str = os.getenv('SECRET_KEY', 'your-secret-key-here')
        
        # JWT Configuration
        self.JWT_SECRET_KEY: str = os.getenv('JWT_SECRET_KEY', 'your-jwt-secret-key-here')
        
        # CORS Configuration
        self.ALLOWED_ORIGINS: list = os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000').split(',')

        # Database Configuration
        self.DATABASE_URL: str = os.getenv('DATABASE_URL', 'sqlite:///roses.db')

        # Application Paths
        self.UPLOAD_FOLDER: str = os.getenv('UPLOAD_FOLDER', 'uploads')
        
        # File Extensions
        self.ALLOWED_IMAGE_EXTENSIONS: Set[str] = set(
            os.getenv('ALLOWED_IMAGE_EXTENSIONS', 'jpg,jpeg,png,gif').split(',')
        )
        self.ALLOWED_VIDEO_EXTENSIONS: Set[str] = set(
            os.getenv('ALLOWED_VIDEO_EXTENSIONS', 'mp4,avi,mov').split(',')
        )

        # YOLO-BoTSORT Configuration
        self.BOTSORT_CONFIG_URL: str = os.getenv(
            'BOTSORT_CONFIG_URL', 
            'https://raw.githubusercontent.com/ultralytics/ultralytics/main/ultralytics/cfg/trackers/botsort.yaml'
        )

    def validate(self) -> None:
        """Validate the configuration settings."""
        required_vars = ['SECRET_KEY', 'JWT_SECRET_KEY']
        missing_vars = [var for var in required_vars if not getattr(self, var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

        # Create necessary directories
        os.makedirs(self.UPLOAD_FOLDER, exist_ok=True)

    def is_development(self) -> bool:
        """Check if the application is in development mode."""
        return self.FLASK_ENV == 'development'

# Create a global settings instance
settings = Settings()
settings.validate() 