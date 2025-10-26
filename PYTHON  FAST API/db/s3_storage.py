import boto3
import json
from typing import List, Optional
from config import settings
from modules.module import Document
from exceptions import (
    S3UploadError,
    S3DownloadError,
    S3ListError,
    S3FileNotFoundError,
    UnsupportedFileFormatError
)

class S3Storage:

    def __init__(self, auto_create_bucket: bool = True):
        """
        Initialize S3 storage.
        
        Args:
            auto_create_bucket: If True, automatically create bucket if it doesn't exist
        """
        self.s3 = boto3.client('s3',
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.S3_REGION  
        )
        self.bucket_name = settings.S3_BUCKET_NAME
        
        # Auto-create bucket if it doesn't exist
        if auto_create_bucket:
            self.ensure_bucket_exists()
      
    def ensure_bucket_exists(self) -> bool:
        """
        Ensure the S3 bucket exists. Create it if it doesn't.
        
        Returns:
            bool: True if bucket exists or was created, False otherwise
        """
        try:
            # Check if bucket exists
            self.s3.head_bucket(Bucket=self.bucket_name)
            return True
        except self.s3.exceptions.ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                # Bucket doesn't exist, create it
                try:
                    self.s3.create_bucket(Bucket=self.bucket_name)
                    return True
                except Exception as create_error:
                    print(f"Failed to create bucket: {create_error}")
                    return False
            else:
                return False
        except Exception as e:
            return False
    
    def create_document_s3(self, document: Document, format: str = "json") -> str:
        """
        Store a document in S3 with the specified format.
        
        Supported formats:
        - 'json': Stores as JSON file
        - 'text': Stores as plain text
        - 'txt': Same as text
        - 'csv': Stores as CSV (if content is structured data)
        
        Args:
            document: Document to store
            format: File format ('json', 'text', 'txt', 'csv')
        
        Returns:
            str: S3 key path of the stored file
        
        Raises:
            UnsupportedFileFormatError: If format is not supported
            S3UploadError: If upload to S3 fails
        """
        try:
            key = f"documents/{document.doc_id}"
            
            # Prepare content based on format
            if format.lower() == "json":
                # Store entire document as JSON 
                content_dict = {
                    "doc_id": document.doc_id,
                    "doc_title": document.doc_title,
                    "description": document.description,
                    "content": document.content,
                    "doc_page_count": document.doc_page_count,
                    "isValid": document.isValid
                }
                body = json.dumps(content_dict, indent=2).encode("utf-8")
                content_type = "application/json"
                
            elif format.lower() in ["text"]:
                # Store content as plain text
                body = document.content.encode("utf-8") if isinstance(document.content, str) else document.content
                content_type = "text/plain"
                                
            else:
                # Invalid format
                raise UnsupportedFileFormatError(
                    format=format,
                    supported_formats=['json', 'text'],
                    details={'requested_format': format.lower()}
                )
            
            # Add file extension to key based on format
            if format.lower() == "json":
                key = f"{key}.json"
            elif format.lower() in ["text"]:
                key = f"{key}.txt"
            
            # Upload to S3
            try:
                self.s3.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=body,
                    ContentType=content_type,
                    Metadata={
                        'doc_title': document.doc_title or '',
                        'format': format.lower()
                    }
                )
                return key
            except Exception as upload_error:
                raise S3UploadError(
                    s3_key=key,
                    reason=str(upload_error),
                    details={'bucket': self.bucket_name, 'format': format.lower()}
                )
            
        except UnsupportedFileFormatError:
            raise  # Re-raise custom exceptions as-is
        except S3UploadError:
            raise  # Re-raise custom exceptions as-is
        except Exception as e:
            raise S3UploadError(
                s3_key=f"documents/{document.doc_id}",
                reason=str(e),
                details={'format': format, 'error_type': type(e).__name__}
            )

    def list_all_files(self) -> List[dict]:
        """
        Retrieve all document file information from S3.
        Returns list of file metadata (keys, sizes, etc.) without downloading content.
        
        Returns:
            List of dicts containing file information
        
        Raises:
            S3ListError: If listing files from S3 fails
        """
        try:
            response = self.s3.list_objects_v2(Bucket=self.bucket_name, Prefix="documents/")
            
            if 'Contents' in response:
                files = []
                for obj in response['Contents']:
                    files.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'].isoformat(),
                        'file_type': obj['Key'].split('.')[-1] if '.' in obj['Key'] else None
                    })
                return files
            return []
            
        except Exception as e:
            raise S3ListError(
                prefix="documents/",
                reason=str(e),
                details={'bucket': self.bucket_name, 'error_type': type(e).__name__}
            )
    
    def get_file_content(self, key: str) -> dict:
        """
        Download and return the content of a specific file from S3.
        
        Args:
            key: S3 key path (e.g., "documents/123.json")
        
        Returns:
            dict with 'key', 'content', 'file_type'
        
        Raises:
            S3FileNotFoundError: If file is not found in S3
            S3DownloadError: If download from S3 fails
        """
        try:
            file_obj = self.s3.get_object(Bucket=self.bucket_name, Key=key)
            content = file_obj['Body'].read().decode('utf-8')
            file_type = key.split('.')[-1] if '.' in key else None
            
            return {
                'key': key,
                'content': content,
                'file_type': file_type
            }
        except self.s3.exceptions.NoSuchKey:
            raise S3FileNotFoundError(
                s3_key=key,
                details={'bucket': self.bucket_name}
            )
        except Exception as e:
            raise S3DownloadError(
                s3_key=key,
                reason=str(e),
                details={'bucket': self.bucket_name, 'error_type': type(e).__name__}
            )
    
    def get_all_documents(self) -> List[Document]:
        """
        Retrieve all documents from S3.
        Note: This requires downloading each file from S3.
        DEPRECATED: Use list_all_files() and get_file_content() instead.
        """
        try:
            response = self.s3.list_objects_v2(Bucket=self.bucket_name, Prefix="documents/")
            documents = []
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    # Get the object from S3
                    try:
                        file_obj = self.s3.get_object(Bucket=self.bucket_name, Key=obj['Key'])
                        content = file_obj['Body'].read().decode('utf-8')
                        
                        # Try to parse as JSON if it's a .json file
                        if obj['Key'].endswith('.json'):
                            data = json.loads(content)
                            document = Document(**data)
                        else:
                            # For text files, create a minimal document
                            document = Document(
                                doc_id=obj['Key'].split('/')[-1],
                                doc_title=f"Document from {obj['Key']}",
                                content=content,
                                doc_page_count=0,
                                isValid=True
                            )
                        documents.append(document)
                    except Exception as e:
                        print(f"Error reading file {obj['Key']}: {str(e)}")
                        continue
            
            return documents
            
        except Exception as e:
            raise Exception(f"Failed to retrieve documents from S3: {str(e)}")
    
    def get_document(self, key: str) -> Optional[Document]:
        """
        Retrieve a specific document from S3 by its key.
        
        Args:
            key: S3 key path (e.g., "documents/123.json")
        
        Returns:
            Document object or None if not found
        """
        try:
            file_obj = self.s3.get_object(Bucket=self.bucket_name, Key=key)
            content = file_obj['Body'].read().decode('utf-8')
            
            # Try to parse as JSON
            if key.endswith('.json'):
                data = json.loads(content)
                return Document(**data)
            else:
                # For text files
                return Document(
                    doc_id=key.split('/')[-1],
                    doc_title=f"Document from {key}",
                    content=content,
                    doc_page_count=0,
                    isValid=True
                )
                
        except self.s3.exceptions.NoSuchKey:
            return None
        except Exception as e:
            raise Exception(f"Failed to retrieve document from S3: {str(e)}")
    
    def update_document_s3(self, document: Document, s3_key: str) -> str:
        """
        Update an existing document in S3.
        Overwrites the existing file with new content.
        
        Args:
            document: Updated document
            s3_key: Existing S3 key path (e.g., "documents/123.json")
        
        Returns:
            str: S3 key path (same as input)
        
        Raises:
            S3FileNotFoundError: If file doesn't exist
            S3UploadError: If update fails
        """
        try:
            # Check if file exists
            try:
                self.s3.head_object(Bucket=self.bucket_name, Key=s3_key)
            except self.s3.exceptions.ClientError as e:
                if e.response['Error']['Code'] == '404':
                    raise S3FileNotFoundError(s3_key=s3_key, details={'bucket': self.bucket_name})
                raise
            
            # Determine format from file extension
            format = "json" if s3_key.endswith('.json') else "text"
            
            # Prepare updated content
            if format == "json":
                content_dict = {
                    "doc_id": document.doc_id,
                    "doc_title": document.doc_title,
                    "description": document.description,
                    "content": document.content,
                    "doc_page_count": document.doc_page_count,
                    "isValid": document.isValid
                }
                body = json.dumps(content_dict, indent=2).encode("utf-8")
                content_type = "application/json"
            else:  # text
                body = document.content.encode("utf-8") if isinstance(document.content, str) else document.content
                content_type = "text/plain"
            
            # Update the file in S3 (overwrite)
            try:
                self.s3.put_object(
                    Bucket=self.bucket_name,
                    Key=s3_key,
                    Body=body,
                    ContentType=content_type,
                    Metadata={
                        'doc_title': document.doc_title or '',
                        'format': format
                    }
                )
                return s3_key
            except Exception as upload_error:
                raise S3UploadError(
                    s3_key=s3_key,
                    reason=str(upload_error),
                    details={'bucket': self.bucket_name, 'format': format, 'operation': 'update'}
                )
            
        except S3FileNotFoundError:
            raise
        except S3UploadError:
            raise
        except Exception as e:
            raise S3UploadError(
                s3_key=s3_key,
                reason=str(e),
                details={'bucket': self.bucket_name, 'error_type': type(e).__name__, 'operation': 'update'}
            )
    
    def delete_document(self, key: str) -> bool:
        """
        Delete a document from S3.
        
        Args:
            key: S3 key path
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.s3.delete_object(Bucket=self.bucket_name, Key=key)
            return True
        except Exception as e:
            print(f"Failed to delete document from S3: {str(e)}")
            return False
    
    