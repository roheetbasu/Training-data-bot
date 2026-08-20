class TrainingDataBotError(Exception):
    """Base exception for the Training Data Bot."""
    def __init__(self, message="", context=None, cause=None, **kwargs):
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.cause = cause
        self.details = kwargs

class ConfigurationError(TrainingDataBotError):
    pass

class DocumentLoadError(TrainingDataBotError):
    def __init__(self, message="", file_path=None, cause=None, **kwargs):
        super().__init__(message, cause=cause, **kwargs)
        self.file_path = file_path

class UnsupportedFormatError(TrainingDataBotError):
    def __init__(self, message=None, file_format=None, supported_formats=None, **kwargs):
        if message is None:
            message = f"Unsupported format: {file_format}. Supported: {', '.join(supported_formats or [])}"
        super().__init__(message, **kwargs)
        self.file_format = file_format
        self.supported_formats = supported_formats or []

class TaskError(TrainingDataBotError):
    pass

class TemplateError(TrainingDataBotError):
    pass

class DecodoAPIError(TrainingDataBotError):
    pass

class AuthenticationError(DecodoAPIError):
    pass

class RateLimitError(DecodoAPIError):
    pass
