# setup_departments.py
import os
import asyncio
import logging
from permit import Permit

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
PERMIT_API_KEY = os.environ.get("PERMIT_API_KEY")
PERMIT_PDP_URL = os.getenv("PERMIT_PDP_URL", "http://permit-pdp:7000")

# Department definitions
DEPARTMENTS = [
    {"key": "engineering", "name": "Engineering Department"},
    {"key": "marketing", "name": "Marketing Department"},
    {"key": "finance", "name": "Finance Department"},
]


async def create_department_instances():
    """Create department resource instances in Permit"""

    # Initialize Permit client
    permit_client = Permit(token=PERMIT_API_KEY, pdp=PERMIT_PDP_URL)

    try:
        logger.info("Creating department instances...")

        for dept in DEPARTMENTS:
            # Create department instance
            instance_data = {
                "key": dept["key"],
                "tenant": "default",
                "resource": "department",
                "attributes": {"name": dept["name"]},
            }

            await permit_client.api.resource_instances.create(instance_data)
            logger.info(f"Created department instance: {dept['key']}")

        logger.info("Department instances created successfully")

    except Exception as e:
        logger.error(f"Error creating department instances: {str(e)}")
        raise


async def main():
    await create_department_instances()


if __name__ == "__main__":
    asyncio.run(main())
