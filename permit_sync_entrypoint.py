import asyncio
import logging
import os
import sys

sys.path.append("/app/scripts")

from scripts.setup_all import setup_all

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    try:
        logger.info("Starting Permit sync process...")
        await setup_all()
        logger.info("Permit sync completed successfully")
    except Exception as e:
        logger.error(f"Permit sync failed: {str(e)}")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
