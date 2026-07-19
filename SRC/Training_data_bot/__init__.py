"""
    Training Data Curation Bot
    
    Enterprise-grade training data curation bot for LLM-fine tuning using Decodo + Python automation
"""
    
__version__ = "0.1.0"
__author__ = "Roheet Basukala"
__email__ = "roheetbasu@gmail.com"
__description__ = "Enterprise - grade training data curation bot for LLM fine - tuning"

# Core imports for easy access
from .core.config import settings
from .core.logging import get_logger
from .core.exceptions import TrainingDataBotError

# main bot class
from .bot import TrainingDataBot

from .sources import (
    PDFLoader,
    WebLoader,
    DocumentLoader,
    UnifiedLoader
)

from .task import (
    QAGenerator,
    ClassificationGenerator,
    
)
