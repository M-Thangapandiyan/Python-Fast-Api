from typing import List
from modules.module import Document

class DocumentStorage:
    def __init__(self):
        self.documents = {}

    def create_document(self, document: Document) -> Document:
        """Create or add a new document."""
        self.documents[document.doc_id] = document
        return document

    def get_all_documents(self) -> List[Document]:
        """Return a list of all documents."""
        return list(self.documents.values()) if self.documents else []

    def get_document_by_id(self, doc_id: str) -> Document | None:
        """Return a document by its ID, or None if not found."""
        return self.documents.get(doc_id)

    def delete_document(self, doc_id: str) -> str:
        """Delete a document by its ID."""
        result = self.documents.pop(doc_id, None)
        return "Document deleted" if result is not None else "Document not found"

    def update_document(self, doc_id, document: Document) -> Document | None:
        """Update an existing document."""
        if doc_id in self.documents:
            self.documents[document.doc_id] = document
            return document
        else:
            return None
