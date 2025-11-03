"""
Document management routes.
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List
import json
from app.schemas.document import Document, DocumentCreate
from app.core.config import settings
from app.core.security import verify_token
from app.core.exceptions import InvalidTokenError
from app.utils.logger import logger
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.db.s3_storage import(
    create_document_s3,
    list_all_files,
    get_file_content,
    delete_file_s3,
    update_document_s3
) 
from app.db import database

router = APIRouter(
    prefix=settings.API_V1_PREFIX,
    tags=[settings.APPLICATION_TAG],
)


hTTPBearer = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(hTTPBearer)):
    """
    Extract and verify JWT token from request.
    """
    try:
        logger.info(f"credentials : {credentials}")
        token = credentials.credentials
        payload = verify_token(token, expected_type="access")
        return payload
    except InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=401, detail="Authentication failed")


@router.post("/documents/", response_model=Document, status_code=201)
def create_document(
    document: DocumentCreate,
    format: str = Query(default="json", pattern="^(json|text)$", description="File format : json or text"),
    current_user: dict = Depends(get_current_user)
) -> Document:
    """
    Create a new document with auto-generated UUID.
    Requires authentication.
    """
    try:
        logger.info(f"current_user : {current_user}")
        new_document = Document(**document.model_dump())  # Convert the incoming DocumentCreate → a Document model
        logger.info(f"new_document : {new_document}")
        s3_result = create_document_s3(new_document, format=format)
        new_document.s3_url = s3_result
        database.create_document(document=new_document)
        return new_document
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create document: {str(e)}")


@router.get("/documents/", response_model=List[Document], status_code=200)
def get_documents(current_user: dict = Depends(get_current_user)) -> List[Document]:
    """
    Retrieve all documents from S3.
    Requires authentication.
    """ 
    try:
        files = list_all_files()
        logger.info(f"files : {files}")
        documents = []
               
        for file in files:
            try:
                file_data = get_file_content(file['key'])
                
                if file_data['file_type'] == 'json':
                    data = json.loads(file_data['content'])  
                    document = Document(**data)
                    document.s3_url = file_data['key']
                elif file_data['file_type'] in ['txt']:
                    document = Document(
                        doc_id=file_data['key'].split('/')[-1].replace('.txt', ''),
                        doc_title=f"Document from {file_data['key']}",
                        content=file_data['content'],
                        doc_page_count=0,
                        is_valid=True
                    )
                    document.s3_url = file_data['key']
                    
                documents.append(document)
            except Exception as e:
                logger.info(f"Error processing file {file['key']}: {str(e)}")
                continue
        
        return documents
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve documents: {str(e)}")


@router.get("/documents/{doc_id}", response_model=Document)
def get_document_by_id(doc_id: str, current_user: dict = Depends(get_current_user)) -> Document:
    """
    Retrieve a document by its ID.
    Requires authentication.
    """
    document = database.get_document_by_id(doc_id)
    if document is not None:
        return document
    
    try:
        files = list_all_files()
        for file in files:
            if file['key'].endswith('.json'):
                file_doc_id = file['key'].replace('documents/', '').replace('.json', '')
                if file_doc_id == doc_id:
                    file_data = get_file_content(file['key'])
                    
                    if file_data['file_type'] == 'json':
                        data = json.loads(file_data['content'])
                        document = Document(**data)
                        document.s3_url = file_data['key']
                        return document
            
            elif file['key'].endswith('.txt'):
                file_doc_id = file['key'].replace('documents/', '').replace('.txt', '')
                if file_doc_id == doc_id:
                    file_data = get_file_content(file['key'])
                    
                    if file_data['file_type'] == 'txt':
                        document = Document(
                            doc_id=file_doc_id,
                            doc_title=f"Document from {file_data['key']}",
                            content=file_data['content'],
                            doc_page_count=0,
                            is_valid=True
                        )
                        document.s3_url = file_data['key']
                        return document
        
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Document not found: {str(e)}")


@router.patch("/documents/{doc_id}")
def update_document(doc_id: str, document: Document, current_user: dict = Depends(get_current_user)) -> Document:
    """
    Update a document by its ID.
    Requires authentication.
    """
    existing_doc = database.get_document_by_id(doc_id)
    if existing_doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    
    updated = database.update_document(
        doc_id=doc_id,
        document=document
    )
    
    if updated is None:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        if existing_doc.s3_url:
            update_document_s3(updated, existing_doc.s3_url)
    except Exception as s3_error:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to update document in storage systems: {str(s3_error)}"
        )
    
    return updated


@router.delete("/documents/{doc_id}", status_code=200)
def delete_document(doc_id: str, current_user: dict = Depends(get_current_user)):
    """
    Delete a document by its ID.
    Requires authentication.
    """
    try:
        # Step 1: Check if document exists
        existing_doc = database.get_document_by_id(doc_id)
        if existing_doc is None:
            raise HTTPException(status_code=404, detail="Document not found")

        try:
            result = database.delete_document(doc_id=doc_id)
            if result:
                result_message = {"message": f"Document '{doc_id}' deleted successfully"}
            else:
                raise HTTPException(status_code=404, detail="Document not found or already deleted")    
                
        except Exception as db_error:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete document from database: {str(db_error)}"
            )

        if existing_doc.s3_url:
            try:
                delete_file_s3(existing_doc.s3_url)
            except Exception as s3_error:
                logger.error(f"S3 deletion failed for {existing_doc.s3_url}: {s3_error}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Document deleted from DB, but failed to delete from S3: {str(s3_error)}"
                )

        return result_message

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error deleting document {doc_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

