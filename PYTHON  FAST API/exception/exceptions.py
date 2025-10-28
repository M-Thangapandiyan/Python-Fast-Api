"""
Custom Exception Classes for the Document Service
"""


class DocumentServiceException(Exception):
    """Base exception class for all document service exceptions."""
    
    def __init__(self, message: str, status_code: int = 500, details: dict = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class S3StorageError(DocumentServiceException):
    """Base exception for S3 storage operations."""
    
    def __init__(self, message: str, s3_key: str = None, status_code: int = 500, details: dict = None):
        self.s3_key = s3_key
        super().__init__(message, status_code=status_code, details=details or {})


class S3FileNotFoundError(S3StorageError):
    """Raised when a file is not found in S3."""
    
    def __init__(self, s3_key: str, details: dict = None):
        message = f"File '{s3_key}' not found in S3"
        super().__init__(message, s3_key=s3_key, status_code=404, details=details or {})


class S3UploadError(S3StorageError):
    """Raised when file upload to S3 fails."""
    
    def __init__(self, s3_key: str, reason: str = None, details: dict = None):
        message = f"Failed to upload file '{s3_key}' to S3"
        if reason:
            message += f": {reason}"
        super().__init__(message, s3_key=s3_key, status_code=500, details=details or {})


class S3ListError(S3StorageError):
    """Raised when listing S3 files fails."""
    
    def __init__(self, prefix: str = None, reason: str = None, status_code: int = 500, details: dict = None):
        message = "Failed to list files from S3"
        if prefix:
            message += f" with prefix '{prefix}'"
        if reason:
            message += f": {reason}"
        super().__init__(message, s3_key=prefix, status_code=status_code, details=details or {})


class UnsupportedFileFormatError(DocumentServiceException):
    """Raised when an unsupported file format is requested."""
    
    def __init__(self, format: str, supported_formats: list = None, details: dict = None):
        message = f"Unsupported file format: '{format}'"
        if supported_formats:
            message += f". Supported formats: {', '.join(supported_formats)}"
        self.format = format
        self.supported_formats = supported_formats or []
        super().__init__(message, status_code=400, details=details or {})
        
        
class DownloadError(S3StorageError):
    def __init__(self, prefix: str = None, reason: str = None, status_code : int = 404, details:dict = None):
        message = "Download failed"          
        if reason:
            message += f": {reason}"
        super().__init__(message=message, s3_key= prefix, status_code=status_code, details=details or {})



