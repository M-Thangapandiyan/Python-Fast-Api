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


class DocumentNotFoundError(DocumentServiceException):
    """Raised when a document is not found."""
    
    def __init__(self, doc_id: str, details: dict = None):
        message = f"Document with ID '{doc_id}' not found"
        self.doc_id = doc_id
        super().__init__(message, status_code=404, details=details or {})


class DocumentAlreadyExistsError(DocumentServiceException):
    """Raised when trying to create a document that already exists."""
    
    def __init__(self, doc_id: str, details: dict = None):
        message = f"Document with ID '{doc_id}' already exists"
        self.doc_id = doc_id
        super().__init__(message, status_code=409, details=details or {})


class DocumentValidationError(DocumentServiceException):
    """Raised when document validation fails."""
    
    def __init__(self, message: str, validation_errors: dict = None, details: dict = None):
        self.validation_errors = validation_errors or {}
        super().__init__(message, status_code=400, details=details or {})


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


class S3DownloadError(S3StorageError):
    """Raised when file download from S3 fails."""
    
    def __init__(self, s3_key: str, reason: str = None, details: dict = None):
        message = f"Failed to download file '{s3_key}' from S3"
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


class DynamoDBStorageError(DocumentServiceException):
    """Base exception for DynamoDB storage operations."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, status_code=500, details=details or {})


class DynamoDBConnectionError(DynamoDBStorageError):
    """Raised when connection to DynamoDB fails."""
    
    def __init__(self, reason: str = None, details: dict = None):
        message = "Failed to connect to DynamoDB"
        if reason:
            message += f": {reason}"
        super().__init__(message, details=details or {})


class UnsupportedFileFormatError(DocumentServiceException):
    """Raised when an unsupported file format is requested."""
    
    def __init__(self, format: str, supported_formats: list = None, details: dict = None):
        message = f"Unsupported file format: '{format}'"
        if supported_formats:
            message += f". Supported formats: {', '.join(supported_formats)}"
        self.format = format
        self.supported_formats = supported_formats or []
        super().__init__(message, status_code=400, details=details or {})


class FileProcessingError(DocumentServiceException):
    """Raised when processing a file fails."""
    
    def __init__(self, file_key: str, reason: str = None, details: dict = None):
        message = f"Failed to process file '{file_key}'"
        if reason:
            message += f": {reason}"
        self.file_key = file_key
        super().__init__(message, status_code=500, details=details or {})

