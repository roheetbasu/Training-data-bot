from ..core.logging import get_logger

class DataBaseManager:
    """ Manage database connections and operations """
    
    def __init__(self):
        self.logger = get_logger("database")
        
    async def close(self):
        """ close database connections """
        self.logger.debug("Database connections closed")