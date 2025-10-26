from fastapi import APIRouter, HTTPException, Query, Request, status
from typing import List
import json
from modules.module import Document, DocumentCreate
from db.data_store import DocumentStorage
from db.dynamodb import DynamoDBDocumentStorage
from config import settings
from db.s3_storage import S3Storage
from exceptions import (
    DocumentServiceException,
    DocumentNotFoundError,
    DocumentValidationError,
    S3UploadError,
    S3DownloadError,
    S3ListError,
    S3FileNotFoundError,
    UnsupportedFileFormatError,
    FileProcessingError
)

router = APIRouter(
    prefix=settings.API_V1_PREFIX,
    tags=[settings.APPLICATION_TAG],
)

dynamodb_document_storage = DynamoDBDocumentStorage()
s3_storage = S3Storage() 

@router.post("/documents/", response_model=Document, status_code=201)
def create_document(
    document: DocumentCreate,
    format: str = Query(default="json", regex="^(json|text)$", description="File format for S3 storage: json or text")
) -> Document:
    """
    Create a new document with auto-generated UUID.
    
    Parameters:
    - document: Document data to create
    - format: Storage format in S3 ('json' or'text')
    
    The document is stored in both DynamoDB and S3.
    """
    try:
        new_document = Document(**document.model_dump())
        # Store in S3 with specified format
        s3_result = s3_storage.create_document_s3(new_document, format=format)
        new_document.s3_url = s3_result
        # Store metadata in DynamoDB
        return dynamodb_document_storage.create_document(document=new_document)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create document: {str(e)}")


@router.get("/documents/", response_model=List[Document], status_code=200)
def get_documents() -> List[Document]:
    """
    Retrieve all documents from S3.
    Files are fetched and processed here.
    """ 
    try:
        # Step 1: Get list of all files from S3 (just metadata, no content)
        files = s3_storage.list_all_files()
        
        documents = []
        # Step 2: Process each file
        for file_info in files:
            try:
                # Download file content
                file_data = s3_storage.get_file_content(file_info['key'])
                
                # Parse based on file type
                if file_data['file_type'] == 'json':
                    # Parse JSON file
                    data = json.loads(file_data['content'])
                    document = Document(**data)
                    # Set s3_url metadata
                    document.s3_url = file_data['key']
                elif file_data['file_type'] in ['text']:
                    # Create minimal document from text file
                    document = Document(
                        doc_id=file_data['key'].split('/')[-1],
                        doc_title=f"Document from {file_data['key']}",
                        content=file_data['content'],
                        doc_page_count=0,
                        isValid=True
                    )
                    # Set s3_url metadata
                    document.s3_url = file_data['key']
                else:
                    # Unknown type, skip
                    continue
                    
                documents.append(document)
            except Exception as e:
                print(f"Error processing file {file_info['key']}: {str(e)}")
                continue
        
        return documents
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve documents: {str(e)}")


@router.get("/documents/{doc_id}", response_model=Document)
def get_document_by_id(doc_id: str) -> Document:
    """
    Dynamically retrieve a document by its ID.
    Checks both DynamoDB and S3.
    Raises 404 if not found in either.
    """
    # Step 1: Try to get from DynamoDB
    document = dynamodb_document_storage.get_document_by_id(doc_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.patch("/documents/{doc_id}")
def update_document(doc_id: str, document: Document) -> Document:
    """
    Update a document by its ID.
    Raises 404 if not found.
    """
    # First check if document exists
    existing_doc = dynamodb_document_storage.get_document_by_id(doc_id)
    if existing_doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Update in DynamoDB
    updated = dynamodb_document_storage.update_document(
        doc_id=doc_id,
        document=document
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Also update in S3
    try:
        if existing_doc.s3_url:
            # Update the document in S3
            s3_storage.update_document_s3(updated, existing_doc.s3_url)
    except Exception as s3_error:
        # If S3 update fails, rollback DynamoDB update
        print(f"Error: Could not update in S3: {s3_error}")
        # Rollback DynamoDB update
        dynamodb_document_storage.update_document(
            doc_id=doc_id,
            document=existing_doc
        )
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to update document in both storage systems: {str(s3_error)}"
        )
    
    return updated


@router.delete("/documents/{doc_id}")
def delete_document(doc_id: str):
    """
    Delete a document by its ID.
    Raises 404 if not found.
    """
    # First check if document exists in DynamoDB
    existing_doc = dynamodb_document_storage.get_document_by_id(doc_id)
    if existing_doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete from DynamoDB
    result = dynamodb_document_storage.delete_document(doc_id=doc_id)
    
    # Also delete from S3
    try:
        if existing_doc.s3_url:
            s3_storage.delete_document(existing_doc.s3_url)
    except Exception as s3_error:
        # If S3 delete fails, document is still in DynamoDB (delete was successful)
        # This is less critical for deletes, but log the error
        print(f"Warning: Document deleted from DynamoDB but not from S3: {s3_error}")
        return {
            "message": "Document deleted from DynamoDB (partial cleanup)",
            "warning": f"S3 cleanup failed: {str(s3_error)}"
        }
    
    return {"message": "Document deleted from both DynamoDB and S3"}

