# setup_all.py
import asyncio
import logging
from setup_rebac import setup_rebac_structure
from setup_departments import create_department_instances
from setup_users import assign_users_to_departments

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def setup_all():
    """Run all setup scripts in order"""
    try:
        logger.info("Starting complete ReBAC setup process...")

        # Step 1: Set up ReBAC structure
        await setup_rebac_structure()

        # Step 2: Create department instances
        await create_department_instances()

        # Step 3: Assign users to departments
        await assign_users_to_departments()

        logger.info("Complete ReBAC setup process finished successfully")

    except Exception as e:
        logger.error(f"Error in setup process: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(setup_all())
