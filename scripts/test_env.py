#!/usr/bin/env python
"""
Test environment configuration for the Mortgage Lending MVP.

This script verifies that environment variables are loaded correctly
and that connections to Azure services can be established.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import datetime
import pprint

# Add project root to path
script_path = Path(__file__).resolve()
project_root = script_path.parent.parent
sys.path.append(str(project_root))

# Load environment variables
load_dotenv(project_root / ".env")

def test_environment():
    """Test that environment variables are loaded correctly."""
    required_vars = [
        "APP_ENV",
        "LOG_LEVEL",
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_ENDPOINT",
        "COSMOS_URI",
        "COSMOS_KEY",
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("Error: The following required environment variables are missing:")
        for var in missing_vars:
            print(f"  - {var}")
        return False
    
    print("Environment variables loaded successfully.")
    return True

def test_azure_openai():
    """Test connection to Azure OpenAI service."""
    try:
        from openai import AzureOpenAI
        
        client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        )
        
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello, test connection."}
            ],
            max_tokens=50
        )
        
        print("Azure OpenAI connection successful:")
        print(f"Response: {response.choices[0].message.content}")
        return True
    except Exception as e:
        print(f"Error connecting to Azure OpenAI: {str(e)}")
        return False

def test_cosmos_db():
    """Test connection to Cosmos DB."""
    try:
        from azure.cosmos import CosmosClient
        
        client = CosmosClient(
            url=os.getenv("COSMOS_URI"),
            credential=os.getenv("COSMOS_KEY")
        )
        
        # Check if database exists
        database_name = os.getenv("COSMOS_DATABASE")
        databases = list(client.list_databases())
        database_exists = any(db['id'] == database_name for db in databases)
        
        if database_exists:
            database = client.get_database_client(database_name)
            print(f"Found database: {database_name}")
            
            # Check if containers exist
            container_names = [
                os.getenv("COSMOS_CONTAINER_APPLICATIONS"),
                os.getenv("COSMOS_CONTAINER_DOCUMENTS"),
                os.getenv("COSMOS_CONTAINER_AUDIT")
            ]
            
            for container_name in container_names:
                if container_name:
                    containers = list(database.list_containers())
                    container_exists = any(container['id'] == container_name for container in containers)
                    status = "Exists" if container_exists else "Does not exist"
                    print(f"Container '{container_name}': {status}")
        else:
            print(f"Database '{database_name}' does not exist yet.")
        
        print("Cosmos DB connection successful.")
        return True
    except Exception as e:
        print(f"Error connecting to Cosmos DB: {str(e)}")
        return False

def test_document_intelligence():
    """Test connection to Azure Document Intelligence."""
    try:
        from azure.ai.documentintelligence import DocumentIntelligenceClient
        from azure.core.credentials import AzureKeyCredential
        
        # Check if credentials are available
        key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")
        endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
        
        if not key or not endpoint:
            print("Document Intelligence credentials not configured.")
            return False
        
        # Create client
        credential = AzureKeyCredential(key)
        client = DocumentIntelligenceClient(endpoint, credential)
        
        # Get available models (a simple API call to test connectivity)
        models = client.list_document_models()
        model_list = [model.model_id for model in models]
        
        print("Document Intelligence connection successful.")
        print("Available models:")
        for model_id in model_list:
            print(f"  - {model_id}")
        
        return True
    except Exception as e:
        print(f"Error connecting to Document Intelligence: {str(e)}")
        return False

def print_environment_summary():
    """Print a summary of the environment configuration."""
    print("\nEnvironment Summary:")
    print("-" * 50)
    
    env_vars = {
        "APP_ENV": os.getenv("APP_ENV"),
        "LOG_LEVEL": os.getenv("LOG_LEVEL"),
        "OpenAI Deployment": os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
        "OpenAI API Version": os.getenv("AZURE_OPENAI_API_VERSION"),
        "Cosmos DB": os.getenv("COSMOS_DATABASE"),
        "Security Features": {
            "PII Detection Threshold": os.getenv("PII_DETECTION_THRESHOLD"),
            "Jailbreak Detection": os.getenv("ENABLE_JAILBREAK_DETECTION"),
        },
        "Agent Configuration": {
            "Max Reasoning Iterations": os.getenv("MAX_REASONING_ITERATIONS"),
            "Confidence Threshold": os.getenv("CONFIDENCE_THRESHOLD"),
            "Default Temperature": os.getenv("DEFAULT_AGENT_TEMPERATURE"),
        }
    }
    
    pp = pprint.PrettyPrinter(indent=2)
    pp.pprint(env_vars)

def main():
    """Run the environment tests."""
    print(f"Testing environment configuration at {datetime.datetime.now()}")
    print("-" * 50)
    
    # Run tests
    env_ok = test_environment()
    if not env_ok:
        print("Environment test failed. Please check your .env file.")
        return
    
    print_environment_summary()
    
    print("\nTesting Service Connections:")
    print("-" * 50)
    
    # Test services - you may want to comment out tests for services you haven't set up yet
    openai_ok = test_azure_openai()
    cosmos_ok = test_cosmos_db()
    document_ok = test_document_intelligence()
    
    # Summary
    print("\nTest Summary:")
    print("-" * 50)
    print(f"Environment Variables: {'✓' if env_ok else '✗'}")
    print(f"Azure OpenAI: {'✓' if openai_ok else '✗'}")
    print(f"Cosmos DB: {'✓' if cosmos_ok else '✗'}")
    print(f"Document Intelligence: {'✓' if document_ok else '✗'}")

if __name__ == "__main__":
    main()