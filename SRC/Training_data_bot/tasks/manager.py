
import asyncio
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from ..core.models import TaskType, TaskTemplate
from ..core.exceptions import TaskError, TemplateError
from ..core.logging import get_logger, LogContext
from .qa_generation import QAGenerator
from .classification import ClassficationGenerator
from .summarization import SummarizationGenerator

class TaskManager:
    """
        Manage task templates and execution  
    """
    def __init__(self):
        self.logger = get_logger("task_manager")
        self.templates: Dict[UUID, TaskTemplate] = {}
        
        #Initialize task generators
        self.generators = {
            TaskType.QA_GENERATION: QAGenerator(),
            TaskType.CLASSIFICATION: ClassficationGenerator(),
            TaskType.SUMMARIZATION: SummarizationGenerator(),
        }
        
        #Load Default templates
        self._load_default_templates()
    
    async def execute_task(
        self,
        
    )
        