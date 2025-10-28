from fastapi import APIRouter, HTTPException, Query
from typing import List
import json
from modules.module import Document, DocumentCreate
from db.dynamodb import DynamoDBDocumentStorage
from config import settings
from db.s3_storage import S3Storage

router = APIRouter(
    prefix=settings.API_V1_PREFIX,
    tags=[settings.APPLICATION_TAG],
)

dynamodb_document_storage = DynamoDBDocumentStorage()
s3_storage = S3Storage()

@router.post("/documents/", response_model=Document, status_code=201)
def create_document(
    document: DocumentCreate,
    format: str = Query(default="json", regex="^(json|text)$", description="File format : json or text")
) -> Document:
    """
    Create a new document with auto-generated UUID.
    """
    try:
        new_document = Document(**document.model_dump())
        s3_result = s3_storage.create_document_s3(new_document, format=format)
        new_document.s3_url = s3_result
        dynamodb_document_storage.create_document(document=new_document)
        return new_document
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create document: {str(e)}")


@router.get("/documents/", response_model=List[Document], status_code=200)
def get_documents() -> List[Document]:
    """
    Retrieve all documents from S3.
    Files are fetched and processed here.
    """ 
    try:
        files = s3_storage.list_all_files()
        documents = []
        
        for file in files:
            try:
                file_data = s3_storage.get_file_content(file['key'])
                
                if file_data['file_type'] == 'json':
                    data = json.loads(file_data['content'])  
                    document = Document(**data)
                    document.s3_url = file_data['key']
                elif file_data['file_type'] in ['text']:
                    document = Document(
                        doc_id=file_data['key'].split('/')[-1],
                        doc_title=f"Document from {file_data['key']}",
                        content=file_data['content'],
                        doc_page_count=0,
                        isValid=True
                    )
                    document.s3_url = file_data['key']
                    
                documents.append(document)
            except Exception as e:
                print(f"Error processing file {file['key']}: {str(e)}")
                continue
        
        return documents
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve documents: {str(e)}")


@router.get("/documents/{doc_id}", response_model=Document)
def get_document_by_id(doc_id: str) -> Document:
    """
    Dynamically retrieve a document by its ID.
    First checks DynamoDB, then falls back to S3 if not found.
    """
    document = dynamodb_document_storage.get_document_by_id(doc_id)
    if document is not None:
        return document
    
    try:
        files = s3_storage.list_all_files()
        
        for file in files:
            if file['key'].endswith('.json'):
                file_doc_id = file['key'].replace('documents/', '').replace('.json', '')
                if file_doc_id == doc_id:
                    file_data = s3_storage.get_file_content(file['key'])
                    
                    if file_data['file_type'] == 'json':
                        data = json.loads(file_data['content'])
                        document = Document(**data)
                        document.s3_url = file_data['key']
                        return document
            
            elif file['key'].endswith('.txt'):
                file_doc_id = file['key'].replace('documents/', '').replace('.txt', '')
                if file_doc_id == doc_id:
                    file_data = s3_storage.get_file_content(file['key'])
                    
                    if file_data['file_type'] == 'txt':
                        document = Document(
                            doc_id=file_doc_id,
                            doc_title=f"Document from {file_data['key']}",
                            content=file_data['content'],
                            doc_page_count=0,
                            isValid=True
                        )
                        document.s3_url = file_data['key']
                        return document
        
        raise HTTPException(status_code=404, detail="Document not found")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Document not found: {str(e)}")


@router.patch("/documents/{doc_id}")
def update_document(doc_id: str, document: Document) -> Document:
    """
    Update a document by its ID.
    Raises 404 if not found.
    """
    existing_doc = dynamodb_document_storage.get_document_by_id(doc_id)
    if existing_doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    
    updated = dynamodb_document_storage.update_document(
        doc_id=doc_id,
        document=document
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        if existing_doc.s3_url:
            s3_storage.update_document(updated, existing_doc.s3_url)
    except Exception as s3_error:
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
    existing_doc = dynamodb_document_storage.get_document_by_id(doc_id)
    print(f"existing_doc = {existing_doc}")
    if existing_doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    
    dynamodb_document_storage.delete_document(doc_id=doc_id)
    
    try:
        if existing_doc.s3_url:
            s3_storage.delete_file(existing_doc.s3_url)
    except Exception as s3_error:
        return {
            "warning": f"S3 cleanup failed: {str(s3_error)}"
        }
    
    return {"message": "Document deleted from both DynamoDB and S3"}

