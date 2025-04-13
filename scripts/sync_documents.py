import os
import asyncio
import logging
import frontmatter
import hashlib
from permit import Permit
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.document_ids import generate_document_id


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
PERMIT_PDP_URL = os.environ.get("PERMIT_PDP_URL", "http://localhost:7000")
PERMIT_API_KEY = os.environ.get("PERMIT_API_KEY")


# Initialize Permit client
permit_client = Permit(token=PERMIT_API_KEY, pdp=PERMIT_PDP_URL)


def read_markdown_file(file_path):
    """Read a markdown file and extract metadata and content."""
    with open(file_path, "r", encoding="utf-8") as file:
        post = frontmatter.load(file)

    metadata = dict(post.metadata)
    content = post.content
    file_name = os.path.basename(file_path)

    return metadata, content, file_name


def get_document_id(file_path):
    """Generate a unique document ID based on the file path."""
    file_name = os.path.basename(file_path)
    name_without_ext = os.path.splitext(file_name)[0]
    path_hash = hashlib.md5(file_path.encode()).hexdigest()[:8]
    return f"{name_without_ext}_{path_hash}"


def extract_department_from_path(file_path):
    """Extract department information from file path."""
    dir_path = os.path.dirname(file_path)
    if dir_path:
        return os.path.basename(dir_path)
    return None


def enrich_metadata(metadata, file_path):
    """Enrich metadata with additional information."""
    enriched_metadata = metadata.copy()

    if "department" not in enriched_metadata:
        department = extract_department_from_path(file_path)
        if department:
            enriched_metadata["department"] = department

    if "confidential" not in enriched_metadata:
        enriched_metadata["confidential"] = False

    if "author" not in enriched_metadata:
        enriched_metadata["author"] = "unknown"

    return enriched_metadata


async def sync_to_permit_rebac(document_id, metadata):
    """Sync document to Permit using ReBAC model."""
    try:
        department = metadata.get("department", "").lower()

        if not department or department not in ["engineering", "marketing", "finance"]:
            department = "marketing"
            logger.warning(
                f"Department not found or invalid for {document_id}, defaulting to marketing"
            )

        # 1. Create document resource instance
        document_instance_data = {
            "key": document_id,
            "tenant": "default",
            "resource": "document",
            "attributes": {
                "author": metadata.get("author", "unknown"),
                "confidential": metadata.get("confidential", False),
                "department": department,
                "title": metadata.get("title", os.path.basename(document_id)),
            },
        }

        # Sync document instance to Permit
        await permit_client.api.resource_instances.create(document_instance_data)
        logger.info(f"Document instance {document_id} created in Permit")

        # 2. Create relationship tuple between department and document
        relationship_data = {
            "subject": f"department:{department}",
            "relation": "parent",
            "object": f"document:{document_id}",
            "tenant": "default",
        }

        # Create the relationship tuple
        await permit_client.api.relationship_tuples.create(relationship_data)
        logger.info(
            f"Relationship created: department:{department} is parent of document:{document_id}"
        )

        return True
    except Exception as e:
        logger.error(f"Permit error: {str(e)}")
        return False


async def sync_document(file_path):
    """Sync a document to Permit."""
    try:
        # Normalize file_path to match Docker container's path format for document_id generation
        normalized_path = file_path
        if not normalized_path.startswith("/app/"):
            # Remove './' if present and prepend '/app/'
            normalized_path = normalized_path.lstrip("./")
            normalized_path = f"/app/{normalized_path}"

        logger.info(f"Syncing document to Permit: {normalized_path}")

        # Read markdown file using the original file_path (not normalized)
        metadata, content, file_name = read_markdown_file(file_path)

        # Enrich metadata using the normalized path for consistency
        metadata = enrich_metadata(metadata, normalized_path)

        # Generate document ID using the normalized path
        document_id = generate_document_id(normalized_path)

        # Sync to Permit
        permit_success = await sync_to_permit_rebac(document_id, metadata)

        if permit_success:
            logger.info(f"Document {document_id} synced successfully to Permit")
        else:
            logger.error(f"Failed to sync document {document_id} to Permit")

    except Exception as e:
        logger.error(f"Error syncing document {file_path}: {str(e)}")


async def sync_all_documents():
    """Sync all documents in the docs directory to Permit."""
    docs_dir = "./docs"
    file_count = 0
    success_count = 0

    logger.info(f"Starting to sync all documents from {docs_dir} to Permit.io")

    for root, _, files in os.walk(docs_dir):
        for file in files:
            if file.endswith((".md", ".markdown")):
                file_path = os.path.join(root, file)
                file_count += 1

                try:
                    await sync_document(file_path)
                    success_count += 1
                except Exception as e:
                    logger.error(f"Failed to sync {file_path}: {str(e)}")

    logger.info(
        f"Completed syncing documents to Permit. Processed: {file_count}, Successful: {success_count}"
    )
    return success_count > 0


if __name__ == "__main__":
    if not PERMIT_API_KEY:
        logger.error("PERMIT_API_KEY environment variable is not set")
    else:
        asyncio.run(sync_all_documents())
