import os
import logging
from typing import Dict, Any
from pymongo import MongoClient

from watcher.utils import read_markdown_file, get_document_id, enrich_metadata

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentSyncer:
    def __init__(self, mongodb_uri: str):
        """
        Initialize the document syncer.
        Args:
            mongodb_uri: MongoDB connection URI
        """
        self.mongodb_uri = mongodb_uri
        self.mongo_client = MongoClient(self.mongodb_uri)
        self.db = self.mongo_client.secure_rag
        self.collection = self.db.documents
        logger.info("Document syncer initialized")

    def sync_document(self, file_path: str, is_new: bool = False) -> bool:
        """
        Sync a document to MongoDB.
        Args:
            file_path: Path to the markdown file
            is_new: Whether the document is newly created (True) or updated (False)
        Returns:
            True if sync is successful, False otherwise
        """
        logger.info(f"Syncing document: {file_path} (is_new={is_new})")

        try:
            # Read markdown file
            metadata, content, file_name = read_markdown_file(file_path)

            # Enrich metadata
            metadata = enrich_metadata(metadata, file_path)

            # Generate document ID
            document_id = get_document_id(file_path)

            # Create document object (without vector_embedding)
            document = {
                "document_id": document_id,
                "filename": os.path.basename(file_path),
                "filepath": file_path,
                "metadata": metadata,
                "content": content,
            }

            # Upsert document to MongoDB
            result = self.collection.update_one(
                {"document_id": document_id}, {"$set": document}, upsert=True
            )
            logger.info(
                f"MongoDB result: acknowledged={result.acknowledged}, modified_count={result.modified_count}, upserted_id={result.upserted_id}"
            )
            logger.info(f"Document {document_id} synced to MongoDB")
            return True

        except Exception as e:
            logger.error(f"Error syncing document {file_path}: {str(e)}")
            return False

    def delete_document(self, file_path: str) -> None:
        """
        Delete a document from MongoDB.
        Args:
            file_path: Path to the markdown file
        """
        try:
            document_id = get_document_id(file_path)
            self.collection.delete_one({"document_id": document_id})
            logger.info(f"Document {document_id} deleted from MongoDB")
        except Exception as e:
            logger.error(f"Error deleting document {file_path}: {str(e)}")
