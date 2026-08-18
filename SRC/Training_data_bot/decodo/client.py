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
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    
    @log_api_call("decodo")
    async def scrape_url(
        self,
        url: str,
        target: str = "universal",
        locale: str = "en-us",
        geo: str = "United States",
        device_type: str = "desktop",
        output_format: str= "html"  
    ) -> Dict[str, Any]:
        """ Scrape content from URL using Decodo's Scraping API """
        
        try:
            # Use the correct decodo API Format
            payload = {
                "url" : url,
                "headless": "html" # standard format as per decodo docs
            }
            
            if target != "universal":
                payload['target'] = target
            if locale != "en-us":
                payload["locale"] = locale
            if geo != "United States":
                payload["geo"] = geo
            if device_type != "desktop":
                payload["device_type"] = device_type
                
            # Make request to correct endpoint 
            self.logger.debug(f"Making Request to Decodo API: {payload}")
            response = await self.client.post("/v2/scrape", json=payload)
            
            # Log response details for debugging
            self.logger.debug(f"Decodo API response: {response.status_code}")
            if response.status_code != 200:
                self.logger.warning(f"Decodo API returned {response.status_code}")
            
            # Handle different response scenarios
            if response.status_code == 200:
                data = response.json()
                
                # Extract content from Decodo response format
                content = ""
                if "results" in data and len(data["results"]) > 0:
                    result = data["results"][0]
                    if "content" in result:
                        content = result["content"]
                    elif "html" in result:
                        content = result["html"]
                
                elif "html" in data:
                    content = data["html"]
                elif "content" in data:
                    content = data["content"]
                
                
                # Clean html content to text
                if content and (content.startswith("<!DOCTYPE") or content.startswith("<html")):
                    # Convert HTML to clean text
                    import re
                    from html import unescape

                    # Remove script and style tags and their contents
                    clean_content = re.sub(
                        r'<(script|style).*?>.*?</\1>',
                        '',
                        content,
                        flags=re.IGNORECASE | re.DOTALL
                    )

                    # Remove HTML comments
                    clean_content = re.sub(
                        r'<!--.*?-->',
                        '',
                        clean_content,
                        flags=re.DOTALL
                    )

                    # Remove remaining HTML tags
                    clean_content = re.sub(r'<[^>]+>', ' ', clean_content)

                    # Convert HTML entities such as &amp; and &nbsp;
                    clean_content = unescape(clean_content)

                    # Clean extra whitespace
                    clean_content = re.sub(r'\s+', ' ', clean_content).strip()

                    content = clean_content
                    
                # Return standardized format
                return {
                    "content": content,
                    "html": data.get("results", [{}])[0].get("content", content),
                    "url": url,
                    "status": "success",
                    "method": "decodo_api",
                    "raw_response": data
                }
            elif response.status_code == 401:
                self.logger.warning("Decodo API authentication failed")
                raise AuthenticationError(
                    "Decodo API authentication failed. Check your credentials."
                )

            elif response.status_code == 429:
                self.logger.warning("Decodo API rate limit exceeded")
                raise RateLimitError(
                    "Decodo API rate limit exceeded. Please try again later."
                )

            elif response.status_code in [500, 502, 503, 504]:
                self.logger.warning(
                    f"Decodo API server error: {response.status_code}"
                )
                raise DecodoAPIError(
                    f"Decodo API server error: {response.status_code}"
                )

            elif response.status_code == 404:
                self.logger.warning("Decodo API endpoint not found")
                raise DecodoAPIError(
                    "Decodo API endpoint not found. Check the API URL."
                )

            else:
                self.logger.error(
                    f"Decodo API request failed with status {response.status_code}"
                )

                try:
                    error_details = response.json()
                except Exception:
                    error_details = response.text

                raise DecodoAPIError(
                    f"Decodo API request failed: {response.status_code} - "
                    f"{error_details}"
                )

        except httpx.TimeoutException as e:
            self.logger.error(f"Decodo API request timed out: {e}")
            raise DecodoAPIError(
                f"Decodo API request timed out: {e}"
            ) from e

        except httpx.RequestError as e:
            self.logger.error(f"Decodo API request error: {e}")
            raise DecodoAPIError(
                f"Decodo API request error: {e}"
            ) from e

        except (AuthenticationError, RateLimitError, DecodoAPIError):
            # Re-raise our own exceptions so Tenacity can handle them
            raise

        except Exception as e:
            self.logger.exception(f"Unexpected Decodo API error: {e}")
            raise DecodoAPIError(
                f"Unexpected error while scraping {url}: {e}"
            ) from e