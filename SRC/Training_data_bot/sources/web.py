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
          