# src/utils/azure_helpers.py

import os
import logging
from src.utils.azure_config import get_azure_manager

logger = logging.getLogger(__name__)

def ensure_cosmos_containers():
    """
    Ensures that all required Cosmos DB containers exist.
    Creates containers based on config if they don't exist.
    """
    azure_mgr = get_azure_manager()
    cosmos_client = azure_mgr.cosmos_client
    
    if not cosmos_client:
        logger.error("Could not initialize Cosmos DB client")
        return False
    
    try:
        db_name = azure_mgr.config["cosmos_db"]["database_name"]
        containers = azure_mgr.config["cosmos_db"]["containers"]
        
        # Create database if it doesn't exist
        try:
            cosmos_client.create_database_if_not_exists(id=db_name)
            logger.info(f"Ensured Cosmos DB database exists: {db_name}")
        except Exception as e:
            logger.error(f"Error creating Cosmos DB database: {e}")
            return False
        
        # Get database client
        db_client = cosmos_client.get_database_client(db_name)
        
        # Create each container if it doesn't exist
        for container_info in containers:
            container_name = container_info["name"]
            partition_key = container_info["partition_key"]
            
            try:
                db_client.create_container_if_not_exists(
                    id=container_name,
                    partition_key=partition_key
                )
                logger.info(f"Ensured Cosmos DB container exists: {container_name}")
            except Exception as e:
                logger.error(f"Error creating Cosmos DB container {container_name}: {e}")
        
        return True
    except Exception as e:
        logger.error(f"Error ensuring Cosmos DB containers: {e}")
        return False

def ensure_blob_containers():
    """
    Ensures that all required blob containers exist.
    Creates containers based on config if they don't exist.
    """
    azure_mgr = get_azure_manager()
    blob_client = azure_mgr.blob_client
    
    if not blob_client:
        logger.error("Could not initialize Blob Storage client")
        return False
    
    try:
        containers = azure_mgr.config["storage"]["containers"]
        
        # Create each container if it doesn't exist
        for container_name in containers.values():
            try:
                blob_client.create_container_if_not_exists(name=container_name)
                logger.info(f"Ensured blob container exists: {container_name}")
            except Exception as e:
                logger.error(f"Error creating blob container {container_name}: {e}")
        
        return True
    except Exception as e:
        logger.error(f"Error ensuring blob containers: {e}")
        return False

def get_openai_client():
    """
    Get the Azure OpenAI client.
    
    Returns:
        AzureOpenAI: OpenAI client
    """
    azure_mgr = get_azure_manager()
    return azure_mgr.openai_client

def get_document_client():
    """
    Get the Azure Document Intelligence client.
    
    Returns:
        DocumentAnalysisClient: Document Intelligence client
    """
    azure_mgr = get_azure_manager()
    return azure_mgr.document_client

def get_cosmos_container(container_name):
    """
    Get a specific Cosmos DB container.
    
    Args:
        container_name (str): Name of the container to get
        
    Returns:
        CosmosContainer: Container client or None if not found
    """
    azure_mgr = get_azure_manager()
    cosmos_client = azure_mgr.cosmos_client
    
    if not cosmos_client:
        logger.error("Could not initialize Cosmos DB client")
        return None
    
    try:
        db_name = azure_mgr.config["cosmos_db"]["database_name"]
        db_client = cosmos_client.get_database_client(db_name)
        container_client = db_client.get_container_client(container_name)
        return container_client
    except Exception as e:
        logger.error(f"Error getting Cosmos DB container {container_name}: {e}")
        return None

def get_blob_container(container_name):
    """
    Get a specific Blob Storage container.
    
    Args:
        container_name (str): Name of the container to get
        
    Returns:
        ContainerClient: Blob container client or None if not found
    """
    azure_mgr = get_azure_manager()
    blob_client = azure_mgr.blob_client
    
    if not blob_client:
        logger.error("Could not initialize Blob Storage client")
        return None
    
    try:
        return blob_client.get_container_client(container_name)
    except Exception as e:
        logger.error(f"Error getting blob container {container_name}: {e}")
        return None

def validate_azure_resources():
    """
    Validates that all required Azure resources are available and accessible.
    
    Returns:
        tuple: (bool, list) - Success status and list of any validation errors
    """
    azure_mgr = get_azure_manager()
    validation_errors = []
    
    # Check Cosmos DB
    if not azure_mgr.cosmos_client:
        validation_errors.append("Could not connect to Cosmos DB")
    
    # Check Blob Storage
    if not azure_mgr.blob_client:
        validation_errors.append("Could not connect to Blob Storage")
    
    # Check OpenAI
    if not azure_mgr.openai_client:
        validation_errors.append("Could not connect to Azure OpenAI")
    
    # Check Document Intelligence
    if not azure_mgr.document_client:
        validation_errors.append("Could not connect to Document Intelligence")
    
    # Try to ensure containers exist
    if not validation_errors:
        try:
            if not ensure_cosmos_containers():
                validation_errors.append("Failed to create Cosmos DB containers")
            
            if not ensure_blob_containers():
                validation_errors.append("Failed to create Blob Storage containers")
        except Exception as e:
            validation_errors.append(f"Error creating containers: {str(e)}")
    
    return (len(validation_errors) == 0, validation_errors)

def initialize_azure_resources():
    """
    Initialize all Azure resources needed for the application.
    
    Returns:
        bool: True if initialization is successful, False otherwise
    """
    try:
        # Get Azure manager
        azure_mgr = get_azure_manager()
        
        # Validate configuration
        if not azure_mgr.validate_configuration():
            logger.error("Azure configuration is incomplete or invalid")
            return False
        
        # Ensure Cosmos DB containers exist
        if not ensure_cosmos_containers():
            logger.error("Failed to initialize Cosmos DB containers")
            return False
        
        # Ensure Blob Storage containers exist
        if not ensure_blob_containers():
            logger.error("Failed to initialize Blob Storage containers")
            return False
        
        logger.info("Azure resources initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing Azure resources: {e}")
        return False