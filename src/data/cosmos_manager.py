"""
Azure Cosmos DB integration for the Mortgage Lending Assistant.

This module provides functionality to interact with Azure Cosmos DB
for storing and retrieving mortgage application data.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Union
from azure.cosmos import CosmosClient, PartitionKey, exceptions
from .models import MortgageApplication

logger = logging.getLogger(__name__)

class CosmosDBManager:
    """
    Manages interactions with Azure Cosmos DB for the mortgage lending assistant.
    For the MVP, this can be configured to use local storage instead of actual Cosmos DB.
    """
    
    def __init__(self, use_mock: bool = False):
        """
        Initialize the Cosmos DB manager.
        
        Args:
            use_mock: If True, uses local file storage instead of actual Cosmos DB.
        """
        self.use_mock = use_mock
        
        if not use_mock:
            # Load configuration
            with open("config/app_config.json", "r") as f:
                config = json.load(f)
                
            # Set up Cosmos DB client
            endpoint = config["azure"]["cosmos_db"]["endpoint"]
            key = os.environ.get("AZURE_COSMOS_KEY")
            
            if not key:
                logger.warning("AZURE_COSMOS_KEY environment variable not set. Falling back to mock mode.")
                self.use_mock = True
            else:
                try:
                    self.client = CosmosClient(endpoint, key)
                    self.database_name = config["azure"]["cosmos_db"]["database_name"]
                    self.container_name = config["azure"]["cosmos_db"]["container_name"]
                    
                    # Initialize database and container
                    self._init_database()
                    logger.info(f"Connected to Cosmos DB at {endpoint}")
                except Exception as e:
                    logger.error(f"Failed to connect to Cosmos DB: {str(e)}. Falling back to mock mode.")
                    self.use_mock = True
        
        if self.use_mock:
            # Set up mock storage directory
            self.mock_dir = "data/mock_cosmos"
            os.makedirs(self.mock_dir, exist_ok=True)
            logger.info("Using mock storage instead of Cosmos DB")
    
    def _init_database(self) -> None:
        """Initialize the database and container if they don't exist."""
        if not self.use_mock:
            try:
                # Create database if it doesn't exist
                database = self.client.create_database_if_not_exists(id=self.database_name)
                
                # Create container if it doesn't exist
                database.create_container_if_not_exists(
                    id=self.container_name,
                    partition_key=PartitionKey(path="/application_id"),
                    offer_throughput=400
                )
                
                logger.info(f"Initialized database {self.database_name} and container {self.container_name}")
            except exceptions.CosmosHttpResponseError as e:
                logger.error(f"Failed to initialize Cosmos DB: {str(e)}")
                raise
    
    def create_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new item in the database.
        
        Args:
            item: Dictionary representing the item to create.
            
        Returns:
            The created item with any server-side additions.
        """
        if self.use_mock:
            # For mock storage, save to a JSON file
            item_id = item.get("id", item.get("application_id"))
            file_path = os.path.join(self.mock_dir, f"{item_id}.json")
            
            with open(file_path, "w") as f:
                json.dump(item, f, indent=2)
            
            logger.info(f"Created mock item with ID {item_id}")
            return item
        else:
            # For actual Cosmos DB
            try:
                container = self.client.get_database_client(self.database_name).get_container_client(self.container_name)
                result = container.create_item(body=item)
                logger.info(f"Created item with ID {result['id']}")
                return result
            except exceptions.CosmosHttpResponseError as e:
                logger.error(f"Failed to create item: {str(e)}")
                raise
    
    def read_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """
        Read an item from the database.
        
        Args:
            item_id: ID of the item to read.
            
        Returns:
            The item if found, None otherwise.
        """
        if self.use_mock:
            # For mock storage, read from JSON file
            file_path = os.path.join(self.mock_dir, f"{item_id}.json")
            
            try:
                with open(file_path, "r") as f:
                    item = json.load(f)
                return item
            except FileNotFoundError:
                logger.warning(f"Item with ID {item_id} not found in mock storage")
                return None
        else:
            # For actual Cosmos DB
            try:
                container = self.client.get_database_client(self.database_name).get_container_client(self.container_name)
                result = container.read_item(item=item_id, partition_key=item_id)
                return result
            except exceptions.CosmosResourceNotFoundError:
                logger.warning(f"Item with ID {item_id} not found in Cosmos DB")
                return None
            except exceptions.CosmosHttpResponseError as e:
                logger.error(f"Failed to read item: {str(e)}")
                raise
    
    def update_item(self, item_id: str, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update an item in the database.
        
        Args:
            item_id: ID of the item to update.
            item: Updated item data.
            
        Returns:
            The updated item if successful, None otherwise.
        """
        if self.use_mock:
            # For mock storage, update JSON file
            file_path = os.path.join(self.mock_dir, f"{item_id}.json")
            
            try:
                # Check if file exists
                if not os.path.exists(file_path):
                    logger.warning(f"Item with ID {item_id} not found in mock storage")
                    return None
                
                with open(file_path, "w") as f:
                    json.dump(item, f, indent=2)
                
                logger.info(f"Updated mock item with ID {item_id}")
                return item
            except Exception as e:
                logger.error(f"Failed to update mock item: {str(e)}")
                raise
        else:
            # For actual Cosmos DB
            try:
                container = self.client.get_database_client(self.database_name).get_container_client(self.container_name)
                result = container.replace_item(item=item_id, body=item)
                logger.info(f"Updated item with ID {item_id}")
                return result
            except exceptions.CosmosResourceNotFoundError:
                logger.warning(f"Item with ID {item_id} not found in Cosmos DB")
                return None
            except exceptions.CosmosHttpResponseError as e:
                logger.error(f"Failed to update item: {str(e)}")
                raise
    
    def delete_item(self, item_id: str) -> bool:
        """
        Delete an item from the database.
        
        Args:
            item_id: ID of the item to delete.
            
        Returns:
            True if successful, False otherwise.
        """
        if self.use_mock:
            # For mock storage, delete JSON file
            file_path = os.path.join(self.mock_dir, f"{item_id}.json")
            
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Deleted mock item with ID {item_id}")
                    return True
                else:
                    logger.warning(f"Item with ID {item_id} not found in mock storage")
                    return False
            except Exception as e:
                logger.error(f"Failed to delete mock item: {str(e)}")
                return False
        else:
            # For actual Cosmos DB
            try:
                container = self.client.get_database_client(self.database_name).get_container_client(self.container_name)
                container.delete_item(item=item_id, partition_key=item_id)
                logger.info(f"Deleted item with ID {item_id}")
                return True
            except exceptions.CosmosResourceNotFoundError:
                logger.warning(f"Item with ID {item_id} not found in Cosmos DB")
                return False
            except exceptions.CosmosHttpResponseError as e:
                logger.error(f"Failed to delete item: {str(e)}")
                return False
    
    def query_items(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Query items from the database.
        
        Args:
            query: SQL query string.
            parameters: Query parameters.
            
        Returns:
            List of items matching the query.
        """
        if self.use_mock:
            # For mock storage, scan JSON files
            results = []
            
            try:
                for filename in os.listdir(self.mock_dir):
                    if filename.endswith(".json"):
                        with open(os.path.join(self.mock_dir, filename), "r") as f:
                            item = json.load(f)
                            
                            # Very basic filtering - this is just for MVP
                            # A real implementation would parse the SQL query
                            include_item = True
                            if parameters:
                                for key, value in parameters.items():
                                    if key in item and item[key] != value:
                                        include_item = False
                                        break
                            
                            if include_item:
                                results.append(item)
                
                logger.info(f"Query returned {len(results)} mock items")
                return results
            except Exception as e:
                logger.error(f"Failed to query mock items: {str(e)}")
                return []
        else:
            # For actual Cosmos DB
            try:
                container = self.client.get_database_client(self.database_name).get_container_client(self.container_name)
                items = list(container.query_items(
                    query=query,
                    parameters=parameters,
                    enable_cross_partition_query=True
                ))
                logger.info(f"Query returned {len(items)} items")
                return items
            except exceptions.CosmosHttpResponseError as e:
                logger.error(f"Failed to query items: {str(e)}")
                return []
    
    def save_application(self, application: MortgageApplication) -> bool:
        """
        Save a mortgage application to the database.
        
        Args:
            application: The application to save.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Convert application to dictionary
            app_dict = application.to_dict()
            
            # Check if application already exists
            existing = self.read_item(application.application_id)
            
            if existing:
                # Update existing application
                result = self.update_item(application.application_id, app_dict)
            else:
                # Create new application
                result = self.create_item(app_dict)
            
            return result is not None
        except Exception as e:
            logger.error(f"Failed to save application: {str(e)}")
            return False
    
    def get_application(self, application_id: str) -> Optional[MortgageApplication]:
        """
        Retrieve a mortgage application from the database.
        
        Args:
            application_id: ID of the application to retrieve.
            
        Returns:
            The application if found, None otherwise.
        """
        try:
            app_dict = self.read_item(application_id)
            
            if app_dict:
                # Convert dictionary to application
                return MortgageApplication.from_dict(app_dict)
            else:
                return None
        except Exception as e:
            logger.error(f"Failed to get application: {str(e)}")
            return None