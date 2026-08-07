"""
    Simple configuration management for Training Data Bot
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from functools import lru_cache

class SimpleConfig:
    """ Simple Configuration class """
    
    def __init__(self):
        # Application info
        self.app_name = "Training Data Curation Bot"
        self.app_version = "0.1.0"
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        
        #Decodo API
        self.decodo = self._create_decodo_config()
        
        # Processing
        self.processing = self._create_processing_config()
        
        #Storage
        self.storage = self._create_storage_config()
        
        #Quality
        self.quality = self._create_quality_config()
        
        #DashBoard
        self.dashboard = self._create_dashboard_config()
        
        #security
        self.security = self._create_security_config()
        
        #Monitoring
        self.monitoring = self._create_monitoring_config()
        
    def _create_decodo_config(self):
        """ Create Decodo Config """
        class DecodoConfig:
            api_key = os.getenv("DECODO_API_KEY", "mock_api_key")
            base_url = os.getenv("DECODO_BASE_URL", "https://api.decodo.com")
            user_id = os.getenv("DECODO_USER_ID")
            basic_auth = os.getenv("DECODO_BASIC_AUTH")
            timeout = int(os.getenv("DECODO_TIMEOUT", "60"))
            max_retries = int(os.getenv("DECODO_MAX_RETRIES","3"))
            rate_limit = int(os.getenv("DECODO_RATE_LIMIT", "10"))
            back_off = 2.0
            retry_status_codes = [429, 502, 503, 504]

        return DecodoConfig
    
