""" Decodo client for web scraping and data extraction """

import asyncio
from typing import Dict, Any, Optional, List
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
import time
import os

from ..core.config import settings
from ..core.exceptions import DecodoAPIError, AuthenticationError, RateLimitError
from ..core.logging import get_logger, log_api_call

class DecodoClient:
    """ Client for interacting with Decodo's web scraping APIs """
    
    def __init__(self):
        self.logger = get_logger("decodo.client")
        self.base_url = "https://scraper-api.decodo.com" 
        self.timeout = settings.decodo.timeout
        self.max_retries = settings.decodo.max_retries
        
        self.username = os.getenv("DECODO_USERNAME") or "U0000283015"
        self.password = os.getenv("DECODO_PASSWORD") or "PW_1fcac9f9d8fhg09rt5"
        self.basic_auth_token = os.getenv("DECODO_BASIC_AUTH") or "VTaw45kd45df9ddf0"
        
        # set up headers
        headers = {
            "accept" : "application/json",
            "content_type" : "application/json",
            "User-agent" : "TrainingDataBot/1.0"
        }
        
        # Add Basic Authentication using provided token
        if self.basic_auth_token:
            headers["authorization"] = f"Basic {self.basic_auth_token}"
        
        # create HTTP client
        self.client = httpx.AsyncClient(
            base_url = self.base_url,
            timeout = self.timeout,
            headers = headers
        )
        
    