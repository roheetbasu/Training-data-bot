import asyncio
from typing import Dict, Any, Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
import json
import os

from ..core.config import settings
from ..core.models import DecodoRequest, DecodoResponse,
from ..core.exceptions import DecodoAPIError, Authentication
from ..core.logging import get_logger, log_api_call


class AIClient:
    
    def __init__(self):
        
        self.logger = get_logger("ai.client")
        
        # Try to use OpenAI
        self.openai_api_key = os.getenv("OPEN_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        
        # Default to simulation if no AI API keys are available
        self.use_simulation = not (self.openai_api_key or self.anthropic_api_key)
        
        if self.use_simulation:
            self.logger.info("Using Simulation mode for development")
            
        else:
            self.logger.info("Connected to real AI services") 
            