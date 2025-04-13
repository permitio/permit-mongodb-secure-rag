import os
import hashlib


def generate_document_id(file_path: str) -> str:
    # Remove container path prefix if present
    if file_path.startswith("/app/"):
        file_path = file_path.replace("/app/", "", 1)

    file_name = os.path.basename(file_path)
    name = os.path.splitext(file_name)[0]

    relative_path = file_path if file_path.startswith("docs/") else f"docs/{file_path}"
    relative_path = relative_path.lower()

    hash_part = hashlib.md5(relative_path.encode()).hexdigest()[:8]

    return f"{name}_{hash_part}"
