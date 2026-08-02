import asyncio
import httpx

from .base import BaseLoader
from typing import Optional, Union
from ..core.models import DocumentType, Document
from ..core.exceptions import DocumentLoadError, UnsupportedFormatError
from ..core.logging import LogContext, get_logger
from ..decodo import DecodoClient

class WebLoader(BaseLoader):
    
    def __init__(self, use_decodo: bool = True, **decodo_kwargs):
        super().__init__()
        self.supported_formats = [DocumentType.URL]
        self.logger = get_logger("web_loader")
        
        # Initialize Decodo client
        self.use_decodo = use_decodo
        self.decodo_client: Optional[DecodoClient] = None
        
        if self.use_decodo:
            try:
                self.decodo_client = DecodoClient()
                self.logger.info("WebLoader initialized with Decodo profession")
            except Exception as e:
                self.logger.warning(f"Failed to intitalize Decodo Client: {e}")
                self.logger.info("WebLoader will use fallback scraping")
                self.use_decodo = False
        
    async def load_single(
        self,
        source,
        **kwargs
    ):
        
      
        if not isinstance(source, str) or not source.startswith(("http://", "https://")):
            raise DocumentLoadError(f"Invalid URL: {source}")
        
        with LogContext("load_url", url=source, method="decodo" if self.use_decodo else "fallback"):
            try:
                
                if self.use_decodo and self.decodo_client:
                    content, extraction_method = await self._fetch_with_decodo(source, **kwargs)
                else:
                    content, extraction_method = await self._fetch_with_fallback(source)
                
                # Extract the title from the content
                title = self._extract_title(source, content)
                
                document = self.create_document(
                    title=title,
                    content=content,
                    source=source,
                    doc_type=DocumentType.URL,
                    extraction_method=extraction_method
                )
                
                self.logger.info(f"Successfully loaded {len(content)} characters")
                return document
            
            except Exception as e:
                self.logger.error(f"Failed to load URL {source} : {e}")
                raise DocumentLoadError(
                    f"Failed to load URL: {source}",
                    file_path = source,
                    cause = e
                )
        
        
    async def _fetch_with_decodo(self, url: str, **kwargs):
        """
            Fetch content using Decodo  
        """
        
        try:
            self.logger.debug(f"Using Decodo professional Scrapping for {url}")
            
            # Set up Decodo parameters
            scrape_params = {
                "target": kwargs.get("target", "universal"),
                "locale": kwargs.get("locale", "en-us"),
                "geo" : kwargs.get("geo", "United States"),
                "device_type" : kwargs.get("output_format", "html")
            }
            
            # Call decodo api
            result = await self.decodo_client.scrape_url(url, **scrape_params)
            
            #Extract content from Decodo response
            if isinstance(result, dict):
                if "content" in result:
                    # Clean text content (already processed by Decodo)
                    content = result['content']
                    if content and len(content.strip()) > 0:
                        self.logger.debug(f"Decodo Extracted {len(content)}")
                        return content, "WebLoader.Decodo"
                    
                # if no content field try to extract from the raw html
                if "html" in result or "data" in result:
                    html = result.get("html") or result.get("data", "")
                    if html:
                        content = self._extract_html_text(html)
                        self.logger.debug(f"Extracted {len(content)} characters")
                        return content, "WebLoader.Decodo.HTML"
                    

            # If we get here, Decodo didn't return usable content
            self.logger.warning(f"Decodo returned unusable content for {url}") 
            return await self._fetch_with_fallback(url)
        except Exception as e:
            self.logger.warning(f"Decodo scraping failed for {url} : {e}") 
            self.logger.info("Falling back to basic scraping")   
            return await self._fetch_with_fallback(url)
    
    async def _fetch_with_fallback(self, url: str):
        
        self.logger.debug(f"Using fallback scraping for {url}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers={
                'User-Agent' :("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                "AppleWebKit/537.36 (KHTML, like Gecko) "
                                "Chrome/138.0.0.0 Safari/537.36""Mozilla/5.0 (Macintosh; Intel Mac 05 X 10_15_7)")
            })
            response.raise_for_status()
            
            content_type = response.headers.get('content-type', '').lower()
            
            if 'text/html' in content_type:
                content = self._extract_html_text(response.text)
                return content, "WebLoader.Fallback.HTML"
            else:
                return response.text, "WebLoader.Fallback.Text"
        
    def _extract_html_text(self, html: str):
        """
            Extract clean text from HTML content  
        """
        
        try:
            from bs4 import BeautifulSoup
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for script in soup("script", "style", "nav", "footer", "header"):
                script.decompose()
                
            # Remove common navigation and UI elements
            for element in soup.find_all(class_=[
                                                    "nav",
                                                    "navbar",
                                                    "navigation",
                                                    "menu",
                                                    "sidebar",
                                                    "footer",
                                                    "header",
                                                    "breadcrumb",
                                                    "advertisement",
                                                    "ads",
                                                    "popup",
                                                    "modal",
                                                    "cookie-banner",
                                                    "cookie-consent"
                                                ]):
                element.decompose()
            
            # Extract text 
            text = soup.get_text()
            
            #clean up whitespaces and normalize
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split())
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Remove excess whitespaces
            import re
            text = re.sub(r'\s+', ' ',text).strip()
            
            return text
        
        except ImportError:
            self.logger.warning("BeautifulSoup not available, returning raw HTML")
            return html
        
        except Exception as e:
            self.logger.warning(f"HTML extraction failed: {e}, returining raw HTML")
            return html
        
    
        
    