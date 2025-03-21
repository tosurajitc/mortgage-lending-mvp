# src/utils/initialize.py

import os
import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
current_dir = Path(__file__).parent
parent_dir = current_dir.parent.parent
sys.path.append(str(parent_dir))

from src.utils.logging_utils import setup_logging
from src.utils.azure_helpers import initialize_azure_resources, validate_azure_resources
from src.utils.azure_config import get_azure_manager

def init_app():
    """
    Initialize the application with all required Azure resources.
    This should be called at application startup.
    
    Returns:
        bool: True if initialization was successful, False otherwise
    """
    # Set up logging first
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Initializing Mortgage Lending Assistant MVP")
    
    # Check for environment variables
    env_vars = [
        "AZURE_SUBSCRIPTION_ID",
        "AZURE_RESOURCE_GROUP",
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_KEY"
    ]
    
    missing_vars = [var for var in env_vars if not os.environ.get(var)]
    if missing_vars:
        logger.warning(f"Missing environment variables: {', '.join(missing_vars)}")
        logger.warning("These should be set in .env file or environment.")
    
    # Load and validate Azure configuration
    azure_mgr = get_azure_manager()
    
    if not azure_mgr.validate_configuration():
        logger.error("Azure configuration validation failed")
        logger.error("Please check your azure_config.json file or environment variables")
        logger.error("You may need to run scripts/setup_azure.py to create resources")
        return False
    
    # Initialize Azure resources
    logger.info("Initializing Azure resources")
    if not initialize_azure_resources():
        logger.error("Failed to initialize Azure resources")
        return False
    
    # Validate Azure resources
    logger.info("Validating Azure resources")
    valid, errors = validate_azure_resources()
    if not valid:
        for error in errors:
            logger.error(f"Validation error: {error}")
        return False
    
    logger.info("Application initialization completed successfully")
    return True

if __name__ == "__main__":
    # This allows running this file directly to test initialization
    success = init_app()
    if success:
        print("Application initialized successfully")
        sys.exit(0)
    else:
        print("Application initialization failed")
        sys.exit(1)