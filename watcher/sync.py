import os
import logging
from typing import Dict, Any
from pymongo import MongoClient
from langchain_openai import OpenAIEmbeddings
import hashlib

from watcher.utils import read_markdown_file, enrich_metadata
from utils.document_ids import generate_document_id

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
        self.collection.create_index("document_id", unique=True)

        openai_api_key = os.environ.get("OPENAI_API_KEY")
        if not openai_api_key:
            logger.warning(
                "OPENAI_API_KEY environment variable is not set. Embeddings will not be generated."
            )
            self.embeddings = None
        else:
            self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)

        logger.info("Document syncer initialized")

    def compute_content_hash(self, content: str) -> str:
        """Compute MD5 hash of the content for change detection."""
        return hashlib.md5(content.encode()).hexdigest()

    def generate_embedding(self, content: str) -> list[float]:
        """Generate vector embedding for the given content."""
        if not self.embeddings:
            logger.warning(
                "OpenAI embeddings not initialized. Cannot generate embedding."
            )
            return None

        try:
            return self.embeddings.embed_query(content)
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return None

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
            document_id = generate_document_id(file_path)

            # Compute content hash
            content_hash = self.compute_content_hash(content)

            # Check if document exists with same content hash
            existing_doc = self.collection.find_one({"document_id": document_id})
            if existing_doc and existing_doc.get("content_hash") == content_hash:
                logger.info(f"Document {document_id} unchanged, skipping sync")
                return True

            # Create document object
            document = {
                "document_id": document_id,
                "filename": os.path.basename(file_path),
                "filepath": file_path,
                "metadata": metadata,
                "content": content,
                "content_hash": content_hash,
            }

            # Upsert document to MongoDB
            result = self.collection.update_one(
                {"document_id": document_id}, {"$set": document}, upsert=True
            )
            logger.info(
                f"MongoDB result: acknowledged={result.acknowledged}, modified_count={result.modified_count}, upserted_id={result.upserted_id}"
            )
            logger.info(f"Document {document_id} synced to MongoDB")

            # Check if embedding needs to be generated
            document_with_embedding = self.collection.find_one(
                {"document_id": document_id, "vector_embedding": {"$exists": True}}
            )
            has_embedding = document_with_embedding is not None

            should_generate_embedding = (
                result.upserted_id is not None
                or result.modified_count > 0
                or not has_embedding
            )

            if should_generate_embedding:
                logger.info(f"Generating embeddings for document {document_id}")
                # Generate embedding
                vector_embedding = self.generate_embedding(content)

                if vector_embedding:
                    # Update document with embedding
                    embed_result = self.collection.update_one(
                        {"document_id": document_id},
                        {"$set": {"vector_embedding": vector_embedding}},
                    )
                    logger.info(
                        f"Embedding update result: acknowledged={embed_result.acknowledged}, modified_count={embed_result.modified_count}"
                    )
                    logger.info(f"Embeddings generated for document {document_id}")
                else:
                    logger.warning(
                        f"Failed to generate embeddings for document {document_id}"
                    )
            else:
                logger.info(
                    f"Skipping embedding generation for unchanged document {document_id}"
                )
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
            document_id = generate_document_id(file_path)
            self.collection.delete_one({"document_id": document_id})
            logger.info(f"Document {document_id} deleted from MongoDB")
        except Exception as e:
            logger.error(f"Error deleting document {file_path}: {str(e)}")
