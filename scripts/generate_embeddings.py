import os
import argparse
import logging
from pymongo import MongoClient
from langchain_openai import OpenAIEmbeddings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Retrieve environment variables
MONGODB_URI = os.environ.get("MONGODB_URI")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Validate environment variables
if not MONGODB_URI:
    raise ValueError("MONGODB_URI environment variable is not set")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

# Initialize MongoDB client
mongo_client = MongoClient(MONGODB_URI)
db = mongo_client.secure_rag
collection = db.documents

# Initialize OpenAI embeddings
embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)


def generate_embedding(content: str) -> list[float]:
    """Generate vector embedding for the given content."""
    return embeddings.embed_query(content)


def generate_embeddings_for_document(document_id: str) -> bool:
    """Generate embeddings for a specific document and update it in MongoDB."""
    try:
        document = collection.find_one({"document_id": document_id})
        if not document:
            logger.error(f"Document with ID {document_id} not found in MongoDB")
            return False

        content = document.get("content", "")
        if not content:
            logger.error(f"No content found for document {document_id}")
            return False

        vector_embedding = generate_embedding(content)
        logger.info(
            f"Generated embedding for document {document_id} (length: {len(vector_embedding)})"
        )

        result = collection.update_one(
            {"document_id": document_id},
            {"$set": {"vector_embedding": vector_embedding}},
        )
        logger.info(
            f"MongoDB update result: acknowledged={result.acknowledged}, modified_count={result.modified_count}"
        )
        return True

    except Exception as e:
        logger.error(f"Error generating embedding for document {document_id}: {str(e)}")
        return False


def generate_embeddings_for_all_documents() -> None:
    """Generate embeddings for all documents in the collection."""
    try:
        documents = collection.find()
        total_docs = collection.count_documents({})
        logger.info(f"Found {total_docs} documents to process")

        success_count = 0
        for doc in documents:
            document_id = doc.get("document_id")
            if generate_embeddings_for_document(document_id):
                success_count += 1

        logger.info(f"Processed {total_docs} documents, {success_count} successful")

    except Exception as e:
        logger.error(f"Error generating embeddings for all documents: {str(e)}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate embeddings for documents in MongoDB"
    )
    parser.add_argument(
        "--document-id",
        type=str,
        help="Specific document ID to generate embedding for (e.g., api_design_3d08a90b)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate embeddings for all documents in the collection",
    )
    args = parser.parse_args()

    if not args.document_id and not args.all:
        parser.error("Must specify either --document-id or --all")

    if args.document_id:
        logger.info(f"Generating embedding for document ID: {args.document_id}")
        generate_embeddings_for_document(args.document_id)
    elif args.all:
        logger.info("Generating embeddings for all documents")
        generate_embeddings_for_all_documents()


if __name__ == "__main__":
    main()
