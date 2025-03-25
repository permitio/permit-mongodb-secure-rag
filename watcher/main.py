import os
import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

from watcher.sync import DocumentSyncer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
DOCS_DIR = "/app/docs"
SYNC_COMPLETE_FILE = "/app/sync_complete"


class MarkdownEventHandler(FileSystemEventHandler):
    def __init__(self, syncer: DocumentSyncer):
        self.syncer = syncer

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith((".md", ".markdown")):
            logger.info(f"File created: {event.src_path}")
            self.syncer.sync_document(event.src_path, is_new=True)

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith((".md", ".markdown")):
            logger.info(f"File modified: {event.src_path}")
            self.syncer.sync_document(event.src_path, is_new=False)

    def on_deleted(self, event):
        if not event.is_directory and event.src_path.endswith((".md", ".markdown")):
            logger.info(f"File deleted: {event.src_path}")
            self.syncer.delete_document(event.src_path)


def sync_existing_documents(syncer: DocumentSyncer, docs_dir: str):
    logger.info(f"Syncing existing documents in {docs_dir}")

    file_count = 0
    for root, _, files in os.walk(docs_dir):
        for file in files:
            if file.endswith((".md", ".markdown")):
                file_path = os.path.join(root, file)
                logger.info(f"Processing file: {file_path}")
                file_count += 1
                syncer.sync_document(file_path, is_new=True)

    logger.info(f"Found {file_count} markdown files to process")
    logger.info("Existing document sync completed")

    # Create sync_complete file to signal readiness
    with open(SYNC_COMPLETE_FILE, "w") as f:
        f.write("Initial sync completed")


def main():
    mongodb_uri = os.environ.get("MONGODB_URI", "mongodb://root:example@mongodb:27017")

    try:
        from pymongo import MongoClient

        client = MongoClient(mongodb_uri)
        db_names = client.list_database_names()
        logger.info(f"Connected to MongoDB. Available databases: {db_names}")
    except Exception as e:
        logger.error(f"Error connecting to MongoDB: {str(e)}")
        return

    syncer = DocumentSyncer(mongodb_uri)

    # Sync existing documents at startup
    sync_existing_documents(syncer, DOCS_DIR)

    # Set up file watcher
    event_handler = MarkdownEventHandler(syncer)
    observer = Observer()
    observer.schedule(event_handler, DOCS_DIR, recursive=True)
    observer.start()

    logger.info(f"Watching directory: {DOCS_DIR}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()


if __name__ == "__main__":
    main()
