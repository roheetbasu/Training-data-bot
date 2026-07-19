"""
    Main Bot Class
"""
import asyncio
from pathlib import Path
from typing import Dict,List,Optional,Union,Any
from uuid import UUID

from .core.config import settings
from .core.logging import get_logger, LogContent
from .core.exceptions import TrainingDataBotError, ConfigurationError

from .sources import UnifiedLoader
from .decodo import DecodoClient
from .ai import AIClient
from .tasks import TaskManager
from .preprocessing import TextPreprocessor
from .evaluation import QualityEvaluator
from .storage import DatasetExporter, DatabaseManager 


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
        
    def _init_components(self):
        """Initiaize all bot components"""
        try:
            self.loader =UnifiedLoader()
            self.decodo_client = DecodoClient()
            self.ai_client = AIClient()
            self.taskmanager = TaskManager()
            self.preprocessing = TextPreprocessor()
            self.evaluator = QualityEvaluator()
            self.exporter = DatasetExporter()
            self.db_manager = DatabaseManager()
            #state (memory boxes)
            self.documents: Dict[UUID, Document] = {}
            self.datasets: Dict[UUID, Dataset] = {}
            self.jobs: Dict[UUID, ProcessingJob] = {}
        except Exception as e:
            raise ConfigurationError("Failed to initialize bot components",...)
        
    async def load_documents(
        self,
        sources: Union[str, Path, List[Union[str, Path]]],
        doc_types,
        **kwargs
                ):
        
        if isinstance ( sources , (str , Path )):
            sources = [ sources ]
        
        documents = []
        for source in sources:
            source_path = Path(source)
            if source_path.is_dir():
                dir_docs = await self.loader.load_directory(source_path)
                documents.extend(dir_docs)
            else:
                doc =  await self.loader.load_single(source_path)
                documents.append(doc)
                
        for doc in documents:
            self.documents[doc.id] = doc