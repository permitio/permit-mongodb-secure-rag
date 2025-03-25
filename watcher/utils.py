import os
import frontmatter
from typing import Dict, Any, Optional
import hashlib


def read_markdown_file(file_path: str) -> tuple[Dict[str, Any], str, str]:
    """
    Read a markdown file and extract its frontmatter metadata and content.
    Args:
        file_path: Path to the markdown file
    Returns:
        Tuple of (metadata, content, file_name)
    """
    with open(file_path, "r", encoding="utf-8") as file:
        post = frontmatter.load(file)

    metadata = dict(post.metadata)
    content = post.content
    file_name = os.path.basename(file_path)

    return metadata, content, file_name


def get_document_id(file_path: str) -> str:
    """
    Generate a unique document ID based on the file path.
    Args:
        file_path: Path to the markdown file
    Returns:
        A unique document ID
    """
    file_name = os.path.basename(file_path)
    name_without_ext = os.path.splitext(file_name)[0]
    path_hash = hashlib.md5(file_path.encode()).hexdigest()[:8]
    return f"{name_without_ext}_{path_hash}"


def extract_department_from_path(file_path: str) -> Optional[str]:
    """
    Extract department information from file path if available.
    Args:
        file_path: Path to the markdown file
    Returns:
        Department name or None if not found
    """
    dir_path = os.path.dirname(file_path)
    if dir_path:
        return os.path.basename(dir_path)
    return None


def enrich_metadata(metadata: Dict[str, Any], file_path: str) -> Dict[str, Any]:
    """
    Enrich metadata with additional information based on file path.
    Args:
        metadata: Existing metadata from frontmatter
        file_path: Path to the markdown file
    Returns:
        Enriched metadata
    """
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
