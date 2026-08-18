""" Decodo client for web scraping and data extraction """

import asyncio
from typing import Dict, Any, Optional, List
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
import time

from ..core.config import settings
from ..core.exceptions import DecodoAPIError, AuthenticationError, RateLimitError
from ..core.logging import get_logger, log_api_call

