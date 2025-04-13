# setup_users.py
import os
import asyncio
import logging
from permit import Permit

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
PERMIT_API_KEY = os.environ.get("PERMIT_API_KEY")
PERMIT_PDP_URL = os.getenv("PERMIT_PDP_URL", "http://permit-pdp:7000")


# Sample users - you can replace this with reading from a file or database
USERS = [
    {"id": "user_engineering_1", "name": "Alice", "department": "engineering"},
    {"id": "user_engineering_2", "name": "Bob", "department": "engineering"},
    {"id": "user_marketing_1", "name": "Carol", "department": "marketing"},
    {"id": "user_finance_1", "name": "Dave", "department": "finance"},
]


async def assign_users_to_departments():
    """Assign users to their respective departments"""

    # Initialize Permit client
    permit_client = Permit(token=PERMIT_API_KEY, pdp=PERMIT_PDP_URL)

    try:
        logger.info("Starting user department assignments...")

        for user in USERS:
            # First, ensure user exists in Permit
            try:
                await permit_client.api.users.create(
                    {
                        "key": user["id"],
                        "email": f"{user['name'].lower()}@example.com",
                        "first_name": user["name"],
                        "last_name": "",
                    }
                )
                logger.info(f"Created user: {user['id']}")
            except Exception as e:
                # User might already exist
                logger.warning(f"Error creating user {user['id']}: {str(e)}")

            # Assign user to department
            try:
                await permit_client.api.role_assignments.assign(
                    {
                        "user": user["id"],
                        "role": "member",
                        "resource_instance": f"department:{user['department']}",
                        "tenant": "default",
                    }
                )
                logger.info(
                    f"Assigned user {user['id']} to department {user['department']}"
                )
            except Exception as e:
                logger.error(
                    f"Error assigning user {user['id']} to department: {str(e)}"
                )

        logger.info("User department assignments completed")

    except Exception as e:
        logger.error(f"Error in user assignment process: {str(e)}")
        raise


async def main():
    await assign_users_to_departments()


if __name__ == "__main__":
    asyncio.run(main())
