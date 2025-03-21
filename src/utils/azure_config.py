# src/utils/azure_config.py

import os
import json
import logging
import openai
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient
from azure.cosmos import CosmosClient
from azure.storage.blob import BlobServiceClient
from azure.ai.formrecognizer import DocumentAnalysisClient

class AzureResourceManager:
    """
    Manages connections to Azure resources for the Mortgage Lending Assistant MVP.
    Handles configuration, connection management, and resource validation.
    """
    
    def __init__(self, config_path=None):
        """
        Initialize the Azure Resource Manager with optional config path.
        
        Args:
            config_path (str, optional): Path to Azure configuration JSON file.
                If not provided, will use environment variables or default config location.
        """
        self.logger = logging.getLogger(__name__)
        self.credential = DefaultAzureCredential()
        
        # Load configuration
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                self.config = json.load(f)
        else:
            # Default to config file in standard location
            config_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                     'config', 'azure_config.json')
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    self.config = json.load(f)
            else:
                # If no config file exists, initialize with empty config
                self.config = {
                    "subscription_id": os.environ.get("AZURE_SUBSCRIPTION_ID", ""),
                    "resource_group": os.environ.get("AZURE_RESOURCE_GROUP", ""),
                    "location": os.environ.get("AZURE_LOCATION", "eastus"),
                    "cosmos_db": {
                        "account_name": os.environ.get("COSMOS_ACCOUNT_NAME", ""),
                        "database_name": os.environ.get("COSMOS_DB_NAME", "mortgage_db"),
                        "endpoint": os.environ.get("COSMOS_ENDPOINT", ""),
                        "key": os.environ.get("COSMOS_KEY", "")
                    },
                    "openai": {
                        "endpoint": os.environ.get("AZURE_OPENAI_ENDPOINT", ""),
                        "key": os.environ.get("AZURE_OPENAI_KEY", ""),
                        "deployment_name": os.environ.get("AZURE_OPENAI_DEPLOYMENT", ""),
                        "api_version": os.environ.get("AZURE_OPENAI_API_VERSION", "2023-05-15")
                    },
                    "document_intelligence": {
                        "endpoint": os.environ.get("DOCUMENT_INTELLIGENCE_ENDPOINT", ""),
                        "key": os.environ.get("DOCUMENT_INTELLIGENCE_KEY", "")
                    },
                    "storage": {
                        "account_name": os.environ.get("STORAGE_ACCOUNT_NAME", ""),
                        "connection_string": os.environ.get("STORAGE_CONNECTION_STRING", ""),
                        "containers": {
                            "documents": "mortgage-documents",
                            "applications": "mortgage-applications"
                        }
                    }
                }
                self.logger.warning("No Azure configuration file found. Using environment variables or defaults.")
        
        # Initialize clients as None - they'll be created on demand
        self._resource_client = None
        self._cognitive_client = None
        self._cosmos_client = None
        self._blob_client = None
        self._openai_client = None
        self._document_client = None
    
    def validate_configuration(self):
        """
        Validates that all required configuration elements are present.
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        required_fields = [
            "subscription_id",
            "resource_group",
            "openai.endpoint",
            "openai.key",
            "cosmos_db.endpoint",
            "cosmos_db.key",
            "document_intelligence.endpoint",
            "document_intelligence.key",
            "storage.connection_string"
        ]
        
        for field in required_fields:
            if not self._get_nested_config(field):
                self.logger.error(f"Missing required configuration: {field}")
                return False
        
        return True
    
    def _get_nested_config(self, key_path):
        """
        Gets a value from nested configuration using dot notation.
        
        Args:
            key_path (str): Dot-separated path to configuration value (e.g., "cosmos_db.endpoint")
            
        Returns:
            Value from configuration or None if not found
        """
        parts = key_path.split('.')
        value = self.config
        for part in parts:
            if part not in value:
                return None
            value = value[part]
        return value
    
    @property
    def resource_client(self):
        """Get or create Azure Resource Management client."""
        if not self._resource_client and self.config.get("subscription_id"):
            self._resource_client = ResourceManagementClient(
                credential=self.credential,
                subscription_id=self.config["subscription_id"]
            )
        return self._resource_client
    
    @property
    def cognitive_services_client(self):
        """Get or create Azure Cognitive Services management client."""
        if not self._cognitive_client and self.config.get("subscription_id"):
            self._cognitive_client = CognitiveServicesManagementClient(
                credential=self.credential,
                subscription_id=self.config["subscription_id"]
            )
        return self._cognitive_client
    
    @property
    def cosmos_client(self):
        """Get or create Azure Cosmos DB client."""
        if not self._cosmos_client:
            cosmos_config = self.config.get("cosmos_db", {})
            if cosmos_config.get("endpoint") and cosmos_config.get("key"):
                self._cosmos_client = CosmosClient(
                    url=cosmos_config["endpoint"],
                    credential=cosmos_config["key"]
                )
            else:
                self.logger.error("Cosmos DB configuration is incomplete")
        return self._cosmos_client
    
    @property
    def blob_client(self):
        """Get or create Azure Blob Storage client."""
        if not self._blob_client:
            storage_config = self.config.get("storage", {})
            if storage_config.get("connection_string"):
                self._blob_client = BlobServiceClient.from_connection_string(
                    storage_config["connection_string"]
                )
            else:
                self.logger.error("Storage configuration is incomplete")
        return self._blob_client
    

    @property
    def openai_client(self):
        """Get or create Azure OpenAI client."""
        if not self._openai_client:
            openai_config = self.config.get("openai", {})
            if openai_config.get("endpoint") and openai_config.get("key"):
                openai.api_type = "azure"
                openai.api_key = openai_config["key"]
                openai.api_base = openai_config["endpoint"]
                openai.api_version = openai_config.get("api_version", "2023-05-15")
                self._openai_client = openai
            else:
                self.logger.error("OpenAI configuration is incomplete")
        return self._openai_client
    
    @property
    def document_client(self):
        """Get or create Azure Document Intelligence client."""
        if not self._document_client:
            doc_config = self.config.get("document_intelligence", {})
            if doc_config.get("endpoint") and doc_config.get("key"):
                self._document_client = DocumentAnalysisClient(
                    endpoint=doc_config["endpoint"],
                    credential=doc_config["key"]
                )
            else:
                self.logger.error("Document Intelligence configuration is incomplete")
        return self._document_client
    
    def get_cosmos_database(self):
        """Get or create the Cosmos DB database for the application."""
        if not self.cosmos_client:
            return None
        
        db_name = self.config["cosmos_db"]["database_name"]
        try:
            return self.cosmos_client.get_database_client(db_name)
        except Exception as e:
            self.logger.error(f"Error accessing Cosmos DB database: {e}")
            return None
    
    def get_blob_container(self, container_name=None):
        """
        Get a blob container client by name.
        
        Args:
            container_name (str, optional): Container name. If not provided, 
                                           uses the documents container from config.
        
        Returns:
            azure.storage.blob.ContainerClient: Blob container client
        """
        if not self.blob_client:
            return None
        
        if not container_name:
            container_name = self.config["storage"]["containers"]["documents"]
            
        try:
            return self.blob_client.get_container_client(container_name)
        except Exception as e:
            self.logger.error(f"Error accessing blob container: {e}")
            return None
    
    def save_configuration(self, config_path=None):
        """
        Save the current configuration to a file.
        
        Args:
            config_path (str, optional): Path to save the configuration.
                If not provided, uses the default location.
        """
        if not config_path:
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                     'config', 'azure_config.json')
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
        
        self.logger.info(f"Azure configuration saved to {config_path}")

# Singleton instance
_azure_manager = None

def get_azure_manager(config_path=None):
    """
    Get the singleton instance of AzureResourceManager.
    
    Args:
        config_path (str, optional): Path to Azure configuration file.
        
    Returns:
        AzureResourceManager: Singleton instance of the resource manager
    """
    global _azure_manager
    if _azure_manager is None:
        _azure_manager = AzureResourceManager(config_path)
    return _azure_manager