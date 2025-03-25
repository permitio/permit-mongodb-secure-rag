import logging
from typing import List, Dict, Any
from langchain_core.documents import Document

logger = logging.getLogger(__name__)


def format_documents_for_response(docs: List[Document]) -> List[Dict[str, Any]]:
    """Format documents for API response."""
    formatted_docs = []
    for doc in docs:
        formatted_doc = {
            "document_id": doc.metadata.get("document_id", "unknown"),
            "filename": doc.metadata.get("filename", "unknown"),
            "department": doc.metadata.get("metadata", {}).get("department", "unknown"),
            "author": doc.metadata.get("metadata", {}).get("author", "unknown"),
            "confidential": doc.metadata.get("metadata", {}).get("confidential", False),
            "snippet": (
                doc.page_content[:200] + "..."
                if len(doc.page_content) > 200
                else doc.page_content
            ),
        }
        formatted_docs.append(formatted_doc)
    return formatted_docs
