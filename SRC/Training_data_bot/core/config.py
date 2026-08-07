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
        
    

