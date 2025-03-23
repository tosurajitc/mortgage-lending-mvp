"""
Semantic Kernel Setup Module
Initializes and configures the Semantic Kernel integration for the mortgage system.
"""

import os
import asyncio
from typing import Optional, Dict, Any, List
import src.semantic_kernel as sk
from src.semantic_kernel.connectors.ai.open_ai import AzureOpenAITextCompletion, AzureChatCompletion

from src.utils.config import get_config
from src.utils.logging_utils import get_logger

logger = get_logger("semantic_kernel.setup")

# Global kernel instance
_kernel = None


def get_kernel() -> sk.Kernel:
    """
    Get the global Semantic Kernel instance, initializing it if needed.
    
    Returns:
        Configured Semantic Kernel instance
    """
    global _kernel
    
    if _kernel is None:
        _kernel = initialize_kernel()
        
    return _kernel


def initialize_kernel() -> sk.Kernel:
    """
    Initialize a new Semantic Kernel instance with Azure OpenAI configuration.
    
    Returns:
        Configured Semantic Kernel instance
    """
    logger.info("Initializing Semantic Kernel")
    
    kernel = sk.Kernel()
    config = get_config()
    
    # Get Azure OpenAI credentials from environment variables or config
    azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT") or config.get("openai", {}).get("endpoint")
    azure_api_key = os.environ.get("AZURE_OPENAI_API_KEY") or config.get("openai", {}).get("api_key")
    azure_deployment = config.get("openai", {}).get("deployment", "gpt-4-turbo")
    azure_api_version = config.get("openai", {}).get("api_version", "2023-07-01-preview")
    
    # Set up Azure OpenAI service
    try:
        # Add Azure OpenAI chat service
        kernel.add_chat_service(
            "azure_chat",
            AzureChatCompletion(
                deployment_name=azure_deployment,
                endpoint=azure_endpoint,
                api_key=azure_api_key,
                api_version=azure_api_version
            )
        )
        
        # Add Azure OpenAI text completion service (for non-chat scenarios)
        kernel.add_text_completion_service(
            "azure_text",
            AzureOpenAITextCompletion(
                deployment_name=config.get("openai", {}).get("text_deployment", "text-davinci-003"),
                endpoint=azure_endpoint,
                api_key=azure_api_key,
                api_version=azure_api_version
            )
        )
        
        logger.info("Azure OpenAI services added to Semantic Kernel")
        
    except Exception as e:
        logger.error(f"Error configuring Azure OpenAI services: {str(e)}")
        # Fall back to a local service if available
        try:
            kernel.add_chat_service(
                "local_llm",
                sk.connectors.ai.local.LocalLLM(
                    model_path="./models/local_model"
                )
            )
            logger.info("Fallback to local LLM service")
        except Exception as local_error:
            logger.error(f"Error configuring fallback local LLM: {str(local_error)}")
            
    # Import and register plugins
    _register_plugins(kernel)
    
    return kernel


def _register_plugins(kernel: sk.Kernel) -> None:
    """
    Register Semantic Kernel plugins with the kernel.
    
    Args:
        kernel: The Semantic Kernel instance
    """
    logger.info("Registering Semantic Kernel plugins")
    
    try:
        # Register the document analysis plugin
        document_plugin_directory = os.path.join(
            os.path.dirname(__file__), 
            "plugins", 
            "document_plugin"
        )
        kernel.import_semantic_skill_from_directory(document_plugin_directory, "document_plugin")
        logger.info("Registered document analysis plugin")
        
        # Register the underwriting plugin
        underwriting_plugin_directory = os.path.join(
            os.path.dirname(__file__), 
            "plugins", 
            "underwriting_plugin"
        )
        kernel.import_semantic_skill_from_directory(underwriting_plugin_directory, "underwriting_plugin")
        logger.info("Registered underwriting plugin")
        
        # Register the compliance plugin
        compliance_plugin_directory = os.path.join(
            os.path.dirname(__file__), 
            "plugins", 
            "compliance_plugin"
        )
        kernel.import_semantic_skill_from_directory(compliance_plugin_directory, "compliance_plugin")
        logger.info("Registered compliance plugin")
        
        # Register the customer service plugin
        customer_plugin_directory = os.path.join(
            os.path.dirname(__file__), 
            "plugins", 
            "customer_plugin"
        )
        kernel.import_semantic_skill_from_directory(customer_plugin_directory, "customer_plugin")
        logger.info("Registered customer service plugin")
        
    except Exception as e:
        logger.error(f"Error registering plugins: {str(e)}")


async def execute_semantic_function(function_name: str, plugin_name: str, 
                            parameters: Dict[str, Any] = None) -> str:
    """
    Execute a semantic function with the provided parameters.
    
    Args:
        function_name: Name of the semantic function
        plugin_name: Name of the plugin containing the function
        parameters: Dictionary of parameters for the function
        
    Returns:
        String result from the semantic function
    """
    kernel = get_kernel()
    parameters = parameters or {}
    
    try:
        # Get the function
        sk_function = kernel.skills.get_function(plugin_name, function_name)
        
        # Create a context with the parameters
        context = kernel.create_new_context()
        for key, value in parameters.items():
            context[key] = str(value)
        
        # Execute the function
        result = await kernel.run_async(sk_function, input_vars=context.variables)
        return str(result)
        
    except Exception as e:
        logger.error(f"Error executing semantic function {plugin_name}.{function_name}: {str(e)}")
        raise


async def chat_with_llm(messages: List[Dict[str, Any]], 
                      temperature: float = 0.7,
                      max_tokens: int = 1000) -> str:
    """
    Send a conversation to the LLM and get a response.
    
    Args:
        messages: List of message dictionaries with 'role' and 'content'
        temperature: Temperature parameter for generation (0.0-1.0)
        max_tokens: Maximum number of tokens to generate
        
    Returns:
        String response from the LLM
    """
    kernel = get_kernel()
    
    try:
        # Set up the chat settings
        settings = sk.ChatRequestSettings(
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=0.95
        )
        
        # Create a chat history from the messages
        chat_history = sk.ChatHistory()
        for message in messages:
            role = message.get("role", "user").lower()
            content = message.get("content", "")
            
            if role == "system":
                chat_history.add_system_message(content)
            elif role == "assistant":
                chat_history.add_assistant_message(content)
            elif role == "user":
                chat_history.add_user_message(content)
        
        # Get the chat completion service
        service = kernel.get_service("azure_chat")
        
        # Send the request and get the response
        result = await service.chat_async(chat_history, settings)
        
        return result.message.content
        
    except Exception as e:
        logger.error(f"Error in chat with LLM: {str(e)}")
        raise


def reset_kernel() -> None:
    """
    Reset the global kernel instance, forcing reinitialization on next use.
    """
    global _kernel
    _kernel = None
    logger.info("Kernel reset - will be reinitialized on next use")