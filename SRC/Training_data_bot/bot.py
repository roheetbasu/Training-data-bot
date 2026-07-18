"""
    Main Bot Class
"""
import asyncio
from pathlib import Path
from typing import Dict,List,Optional,Union,Any
from uuid import UUID


class TrainingDataBot:
    """ 
    Main Training Bot Class
    
    This class  provides a high level interface for:
    - Loading documents from various sources
    - Processing text with task templates
    - Quality Assessment and filtering 
    - Dataset Creation and export
    """
    
    def __init__(self, config: Optional[Dict[str, Any]]):
        
        self.logger = get_logger("training_data_bot")
        self.config = config or {}
        self._init_components()
        self.logger.info("Training Data Bot intialized sucessfully")
        