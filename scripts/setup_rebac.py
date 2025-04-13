# setup_rebac.py
import os
import asyncio
import logging
from permit import Permit

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
PERMIT_API_KEY = os.environ.get("PERMIT_API_KEY")
PERMIT_PDP_URL = os.getenv("PERMIT_PDP_URL", "http://permit-pdp:7000")


async def setup_rebac_structure():
    """Setup the ReBAC structure in Permit.io"""

    # Initialize Permit client
    permit_client = Permit(token=PERMIT_API_KEY, pdp=PERMIT_PDP_URL)

    try:
        # Create resource types
        logger.info("Creating resource types...")

        await permit_client.api.resources.create(
            {
                "key": "document",
                "name": "Document",
                "actions": {"read": {"description": "Read the document"}},
            }
        )

        await permit_client.api.resources.create(
            {
                "key": "department",
                "name": "Department",
                "actions": {"view": {"description": "View department details"}},
            }
        )
        logger.info("✅ Resource types created successfully.")

        # Create resource relations
        logger.info("Creating resource relations...")

        await permit_client.api.resource_relations.create(
            "document",
            {"key": "parent", "name": "Parent", "subject_resource": "department"},
        )

        logger.info("✅ Resource relations created successfully.")

        await asyncio.sleep(10)

        # Create roles
        logger.info("Creating resource roles...")

        await permit_client.api.resource_roles.create(
            "department", {"key": "member", "name": "Member", "permissions": ["view"]}
        )

        await permit_client.api.resource_roles.create(
            "document", {"key": "reader", "name": "Reader", "permissions": ["read"]}
        )

        logger.info("✅ Resource roles created successfully.")
        # Setup role derivation
        logger.info("Setting up role derivations...")

        derivation_rule = {
            "role": "member",
            "on_resource": "department",
            "linked_by_relation": "parent",
        }

        await permit_client.api.resource_roles.create_role_derivation(
            resource_key="document",
            role_key="reader",
            derivation_rule=derivation_rule,
        )

        logger.info("✅ Role derivation setup completed.")

        logger.info("🎉 ReBAC structure setup completed successfully")

    except Exception as e:
        logger.error(f"Error setting up ReBAC structure: {str(e)}")
        raise


async def main():
    await setup_rebac_structure()


if __name__ == "__main__":
    asyncio.run(main())
