

import os
import sys
import json
import argparse
import logging
from azure.identity import DefaultAzureCredential, InteractiveBrowserCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.cosmosdb import CosmosDBManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient
from azure.mgmt.keyvault import KeyVaultManagementClient
from azure.core.exceptions import HttpResponseError

# Add project root to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.append(project_root)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("azure_setup")

def get_credential(interactive=False):
    """Get Azure credential object."""
    try:
        if interactive:
            return InteractiveBrowserCredential()
        return DefaultAzureCredential()
    except Exception as e:
        logger.error(f"Error getting Azure credential: {e}")
        sys.exit(1)

def load_config(config_path):
    """Load configuration from file."""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        sys.exit(1)

def save_config(config, config_path):
    """Save updated configuration to file."""
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        logger.info(f"Configuration saved to {config_path}")
    except Exception as e:
        logger.error(f"Error saving configuration: {e}")

def create_resource_group(credential, subscription_id, config):
    """Create resource group if it doesn't exist."""
    resource_client = ResourceManagementClient(credential, subscription_id)
    rg_name = config["resource_group"]
    location = config["location"]
    
    logger.info(f"Checking resource group: {rg_name}")
    
    if not any(rg.name == rg_name for rg in resource_client.resource_groups.list()):
        logger.info(f"Creating resource group: {rg_name}")
        resource_client.resource_groups.create_or_update(
            rg_name,
            {"location": location}
        )
        logger.info(f"Resource group {rg_name} created")
    else:
        logger.info(f"Resource group {rg_name} already exists")

def create_cosmos_db(credential, subscription_id, config):
    """Create Cosmos DB account and database."""
    cosmos_client = CosmosDBManagementClient(credential, subscription_id)
    rg_name = config["resource_group"]
    location = config["location"]
    account_name = config["cosmos_db"]["account_name"]
    db_name = config["cosmos_db"]["database_name"]
    
    logger.info(f"Setting up Cosmos DB account: {account_name}")
    
    # Check if account exists
    try:
        account = cosmos_client.database_accounts.get(rg_name, account_name)
        logger.info(f"Cosmos DB account {account_name} already exists")
    except HttpResponseError:
        # Create account if it doesn't exist
        logger.info(f"Creating Cosmos DB account: {account_name}")
        poller = cosmos_client.database_accounts.begin_create_or_update(
            rg_name,
            account_name,
            {
                "location": location,
                "locations": [{"location_name": location}],
                "database_account_offer_type": "Standard",
                "capabilities": [{"name": "EnableServerless"}]
            }
        )
        account = poller.result()
        logger.info(f"Cosmos DB account {account_name} created")
    
    # Update configuration with account endpoint and key
    if account:
        keys = cosmos_client.database_accounts.list_keys(rg_name, account_name)
        config["cosmos_db"]["endpoint"] = f"https://{account_name}.documents.azure.com:443/"
        config["cosmos_db"]["key"] = keys.primary_master_key
        logger.info(f"Cosmos DB endpoint: {config['cosmos_db']['endpoint']}")
    
    # Now create database and containers
    logger.info(f"Setting up Cosmos DB database: {db_name}")
    
    # Need to use SDK directly for database and container creation since
    # it's not part of the management plane
    # This part would typically be done in the application code
    logger.info("Database and containers will be created by the application on first run")

def create_storage_account(credential, subscription_id, config):
    """Create Storage account and containers."""
    storage_client = StorageManagementClient(credential, subscription_id)
    rg_name = config["resource_group"]
    location = config["location"]
    account_name = config["storage"]["account_name"]
    
    logger.info(f"Setting up Storage account: {account_name}")
    
    # Check if account exists
    try:
        account = storage_client.storage_accounts.get_properties(rg_name, account_name)
        logger.info(f"Storage account {account_name} already exists")
    except HttpResponseError:
        # Create account if it doesn't exist
        logger.info(f"Creating Storage account: {account_name}")
        poller = storage_client.storage_accounts.begin_create(
            rg_name,
            account_name,
            {
                "location": location,
                "kind": "StorageV2",
                "sku": {"name": "Standard_LRS"}
            }
        )
        account = poller.result()
        logger.info(f"Storage account {account_name} created")
    
    # Get connection string
    if account:
        keys = storage_client.storage_accounts.list_keys(rg_name, account_name)
        key = keys.keys[0].value
        config["storage"]["connection_string"] = (
            f"DefaultEndpointsProtocol=https;"
            f"AccountName={account_name};"
            f"AccountKey={key};"
            f"EndpointSuffix=core.windows.net"
        )
        logger.info(f"Storage connection string updated")

def create_cognitive_services(credential, subscription_id, config):
    """Create Cognitive Services accounts (OpenAI, Document Intelligence)."""
    cognitive_client = CognitiveServicesManagementClient(credential, subscription_id)
    rg_name = config["resource_group"]
    location = config["location"]
    
    # Create OpenAI account
    openai_name = f"{rg_name}-openai"
    logger.info(f"Setting up OpenAI account: {openai_name}")
    
    # Note: Azure OpenAI is only available in specific regions and requires approval
    # This is just a placeholder - in reality you would need to request access
    logger.info("Note: Azure OpenAI requires special approval and is only available in specific regions")
    logger.info("This script will not create the OpenAI resource automatically")
    logger.info("Please create it manually and update the configuration")
    
    # Create Document Intelligence account
    doc_name = f"{rg_name}-docint"
    logger.info(f"Setting up Document Intelligence account: {doc_name}")
    
    try:
        doc_account = cognitive_client.accounts.get(rg_name, doc_name)
        logger.info(f"Document Intelligence account {doc_name} already exists")
    except HttpResponseError:
        try:
            # Create account if it doesn't exist
            logger.info(f"Creating Document Intelligence account: {doc_name}")
            poller = cognitive_client.accounts.begin_create(
                rg_name,
                doc_name,
                {
                    "location": location,
                    "kind": "FormRecognizer",
                    "sku": {"name": "S0"},
                    "properties": {}
                }
            )
            doc_account = poller.result()
            logger.info(f"Document Intelligence account {doc_name} created")
        except Exception as e:
            logger.error(f"Error creating Document Intelligence account: {e}")
            logger.info("Please create it manually and update the configuration")
            return
    
    # Update configuration with account endpoints and keys
    if 'doc_account' in locals():
        keys = cognitive_client.accounts.list_keys(rg_name, doc_name)
        config["document_intelligence"]["endpoint"] = f"https://{location}.api.cognitive.microsoft.com/"
        config["document_intelligence"]["key"] = keys.key1
        logger.info(f"Document Intelligence endpoint and key updated")

def create_key_vault(credential, subscription_id, config):
    """Create Key Vault for secure storage of secrets."""
    keyvault_client = KeyVaultManagementClient(credential, subscription_id)
    rg_name = config["resource_group"]
    location = config["location"]
    vault_name = config["key_vault"]["name"]
    
    logger.info(f"Setting up Key Vault: {vault_name}")
    
    # Get tenant ID from credential
    object_id = credential._get_current_user_object_id()
    tenant_id = credential.get_token("https://management.azure.com/.default").tenant_id
    
    # Create vault if it doesn't exist
    try:
        vault = keyvault_client.vaults.get(rg_name, vault_name)
        logger.info(f"Key Vault {vault_name} already exists")
    except HttpResponseError:
        try:
            # Create vault
            logger.info(f"Creating Key Vault: {vault_name}")
            vault_properties = {
                "location": location,
                "properties": {
                    "tenant_id": tenant_id,
                    "sku": {"family": "A", "name": "standard"},
                    "access_policies": [{
                        "tenant_id": tenant_id,
                        "object_id": object_id,
                        "permissions": {
                            "secrets": ["all"],
                            "keys": ["all"],
                            "certificates": ["all"]
                        }
                    }]
                }
            }
            poller = keyvault_client.vaults.begin_create_or_update(rg_name, vault_name, vault_properties)
            vault = poller.result()
            logger.info(f"Key Vault {vault_name} created")
        except Exception as e:
            logger.error(f"Error creating Key Vault: {e}")
            return
    
    # Update configuration with vault URI
    if 'vault' in locals():
        config["key_vault"]["uri"] = vault.properties.vault_uri
        logger.info(f"Key Vault URI: {config['key_vault']['uri']}")

def main():
    parser = argparse.ArgumentParser(description="Set up Azure resources for Mortgage MVP")
    parser.add_argument("--config", default="../config/azure_config.json", help="Path to configuration file")
    parser.add_argument("--interactive", action="store_true", help="Use interactive browser authentication")
    parser.add_argument("--subscription", help="Azure subscription ID (overrides config)")
    args = parser.parse_args()
    
    # Get configuration
    config_path = os.path.abspath(os.path.join(script_dir, args.config))
    logger.info(f"Using configuration from: {config_path}")
    
    # Load or create configuration
    if os.path.exists(config_path):
        config = load_config(config_path)
    else:
        logger.error(f"Configuration file not found: {config_path}")
        sys.exit(1)
    
    # Override subscription ID if provided
    if args.subscription:
        config["subscription_id"] = args.subscription
    
    # Check for subscription ID
    if not config["subscription_id"]:
        logger.error("Subscription ID is required. Please provide it in the config file or with --subscription")
        sys.exit(1)
    
    # Get Azure credential
    credential = get_credential(args.interactive)
    subscription_id = config["subscription_id"]
    
    # Create resources
    create_resource_group(credential, subscription_id, config)
    create_cosmos_db(credential, subscription_id, config)
    create_storage_account(credential, subscription_id, config)
    create_cognitive_services(credential, subscription_id, config)
    create_key_vault(credential, subscription_id, config)
    
    # Save updated configuration
    save_config(config, config_path)
    
    logger.info("Azure setup completed successfully!")

if __name__ == "__main__":
    main()