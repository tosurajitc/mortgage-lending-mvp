import os
import json
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import uuid
from dotenv import load_dotenv


load_dotenv()

logger = logging.getLogger(__name__)

class CosmosDBManager:
    """
    Manages interactions with Azure Cosmos DB for the mortgage lending assistant.
    Provides robust mock mode for development and testing.
    """
    
    def __init__(self, use_mock: bool = None):
        # Load configuration
        config_path = os.path.join(os.getcwd(), "config", "app_config.json")
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
                
            # Determine mock mode
            if use_mock is None:
                use_mock = config.get('mock_mode', {}).get('enabled', True)
            
            # Set mock storage path
            self.mock_dir = config.get('mock_mode', {}).get('mock_storage_path', 'data/mock_cosmos')
            
            # Get Cosmos DB settings
            cosmos_db_config = config.get('azure', {}).get('cosmos_db', {})
            self.container_name = cosmos_db_config.get('container_name', 'Applications')
            self.database_name = cosmos_db_config.get('database_name', 'MortgageLendingDB')
        except Exception as e:
            logger.warning(f"Error loading config: {e}")
            # Fallback to defaults
            use_mock = True
            self.mock_dir = 'data/mock_cosmos'
            self.container_name = 'Applications'
            self.database_name = 'MortgageLendingDB'
        
        # Rest of the existing initialization...    


        """
        Initialize the Cosmos DB manager.
        
        Args:
            use_mock: If True, uses local file storage instead of actual Cosmos DB.
        """
        # Logging setup
        self.logger = logging.getLogger(__name__)
        
        # Default configuration
        self.use_mock = use_mock
        self.container_name = "applications"  # Add a default container name
        self.database_name = "mortgage_lending_db"  # Add a default database name
        
        # Mock storage setup
        self.mock_dir = os.path.join(os.getcwd(), "data", "mock_cosmos")
        os.makedirs(self.mock_dir, exist_ok=True)
        
        # Check for Cosmos DB configuration
        try:
            # Try to load configuration if available
            config_path = os.path.join(os.getcwd(), "config", "app_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    config = json.load(f)
                    # Override defaults if config exists
                    self.container_name = config.get('azure', {}).get('cosmos_db', {}).get('container_name', self.container_name)
                    self.database_name = config.get('azure', {}).get('cosmos_db', {}).get('database_name', self.database_name)
        except Exception as e:
            self.logger.warning(f"Error loading config: {e}")
        
        # Environment variable check
        cosmos_key = os.environ.get("COSMOS_KEY")
        if not cosmos_key and not use_mock:
            self.logger.warning("COSMOS_KEY not set. Falling back to mock mode.")
            self.use_mock = True
        
        self.logger.info(f"Cosmos DB Manager initialized (Mock Mode: {self.use_mock})")

    def _get_mock_file_path(self, item_id: str, container_name: Optional[str] = None) -> str:
        """
        Generate a mock file path for storing/retrieving items.
        
        Args:
            item_id: Unique identifier for the item
            container_name: Optional container name (defaults to default container)
        
        Returns:
            Full path to the mock storage file
        """
        # Use provided container name or default
        container_dir = container_name or self.container_name
        
        # Create container directory if it doesn't exist
        container_path = os.path.join(self.mock_dir, container_dir)
        os.makedirs(container_path, exist_ok=True)
        
        # Generate filename (sanitize item_id to be filename-friendly)
        safe_item_id = "".join(c if c.isalnum() or c in ['-', '_'] else '_' for c in str(item_id))
        return os.path.join(container_path, f"{safe_item_id}.json")

    async def create_item(self, container_name: str, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new item in the database or mock storage.
        
        Args:
            container_name: Container name
            item: Dictionary representing the item to create
        
        Returns:
            The created item with any server-side additions
        """
        # Ensure item has an ID
        if 'id' not in item and 'application_id' not in item:
            item['id'] = str(uuid.uuid4())
        
        # Use ID from either 'id' or 'application_id'
        item_id = item.get('id') or item.get('application_id')
        
        if self.use_mock:
            # Mock storage
            file_path = self._get_mock_file_path(item_id, container_name)
            
            try:
                # Add timestamp
                item['created_at'] = datetime.utcnow().isoformat()
                
                # Write to file
                with open(file_path, 'w') as f:
                    json.dump(item, f, indent=2)
                
                self.logger.info(f"Created mock item in {container_name}: {item_id}")
                return item
            
            except Exception as e:
                self.logger.error(f"Error creating mock item: {e}")
                raise
        
        # Real Cosmos DB implementation would go here (not implemented in mock mode)
        return item

    async def get_item(self, container_name: str, query: Union[Dict[str, Any], str]) -> Optional[Dict[str, Any]]:
        """
        Retrieve an item from the database or mock storage.
        
        Args:
            container_name: Container name
            query: Query parameters to find the item or application_id
        
        Returns:
            The item if found, None otherwise
        """
        # Normalize query to dictionary if it's a string (application_id)
        if isinstance(query, str):
            query = {"application_id": query}
        
        # Ensure query is a dictionary
        if not isinstance(query, dict):
            self.logger.error(f"Invalid query type: {type(query)}. Expected dict or str.")
            return None

        if self.use_mock:
            try:
                # Scan mock files in the container directory
                container_path = os.path.join(self.mock_dir, container_name)
                
                # Ensure the container directory exists
                if not os.path.exists(container_path):
                    self.logger.warning(f"No mock container found: {container_name}")
                    return None
                
                for filename in os.listdir(container_path):
                    if filename.endswith('.json'):
                        file_path = os.path.join(container_path, filename)
                        
                        with open(file_path, 'r') as f:
                            item = json.load(f)
                        
                        # Check if item matches all query conditions
                        if all(str(query.get(k, '')) == str(item.get(k, '')) for k in query):
                            return item
                
                # If no matching item found
                return None
            
            except FileNotFoundError:
                self.logger.warning(f"No mock container found: {container_name}")
                return None
            except Exception as e:
                self.logger.error(f"Error retrieving mock item: {e}")
                raise
        
        # Real Cosmos DB implementation would go here
        return None

    async def update_item(self, container_name: str, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing item in the database or mock storage.
        
        Args:
            container_name: Container name
            item: Updated item data
        
        Returns:
            The updated item
        """
        # Ensure item has an ID
        item_id = item.get('id') or item.get('application_id')
        
        if self.use_mock:
            try:
                file_path = self._get_mock_file_path(item_id, container_name)
                
                # Add/update timestamp
                item['updated_at'] = datetime.utcnow().isoformat()
                
                # Write updated item
                with open(file_path, 'w') as f:
                    json.dump(item, f, indent=2)
                
                self.logger.info(f"Updated mock item in {container_name}: {item_id}")
                return item
            
            except Exception as e:
                self.logger.error(f"Error updating mock item: {e}")
                raise
        
        # Real Cosmos DB implementation would go here
        return item

    async def query_items(self, container_name: str, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Query items from the database or mock storage.
        
        Args:
            container_name: Container name
            query: Query string (simplified for mock mode)
            parameters: Optional query parameters
        
        Returns:
            List of matching items
        """
        if self.use_mock:
            try:
                container_path = os.path.join(self.mock_dir, container_name)
                results = []
                
                for filename in os.listdir(container_path):
                    if filename.endswith('.json'):
                        file_path = os.path.join(container_path, filename)
                        
                        with open(file_path, 'r') as f:
                            item = json.load(f)
                        
                        # Basic query matching (very simplified)
                        if parameters:
                            if all(str(parameters.get(k)) in str(item.get(k, '')) for k in parameters):
                                results.append(item)
                        else:
                            results.append(item)
                
                return results
            
            except FileNotFoundError:
                self.logger.warning(f"No mock container found: {container_name}")
                return []
            except Exception as e:
                self.logger.error(f"Error querying mock items: {e}")
                return []
        
        # Real Cosmos DB implementation would go here
        return []