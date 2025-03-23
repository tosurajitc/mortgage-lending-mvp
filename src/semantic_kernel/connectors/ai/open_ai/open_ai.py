# src/semantic_kernel/connectors/ai/open_ai/open_ai.py

class AzureOpenAITextCompletion:
    """
    Mock implementation of Azure OpenAI Text Completion for testing.
    """
    def __init__(
        self,
        deployment_name: str,
        endpoint: str,
        api_key: str,
        api_version: str = "2023-07-01-preview"
    ):
        self.deployment_name = deployment_name
        self.endpoint = endpoint
        self.api_key = api_key
        self.api_version = api_version
    
    async def complete_async(self, prompt: str, settings=None):
        """Mock completion method"""
        return f"Mock response to: {prompt}"

class AzureChatCompletion:
    """
    Mock implementation of Azure OpenAI Chat Completion for testing.
    """
    def __init__(
        self,
        deployment_name: str,
        endpoint: str,
        api_key: str,
        api_version: str = "2023-07-01-preview"
    ):
        self.deployment_name = deployment_name
        self.endpoint = endpoint
        self.api_key = api_key
        self.api_version = api_version
    
    async def chat_async(self, chat_history, settings=None):
        """Mock chat completion method"""
        class MockResponse:
            def __init__(self, content):
                self.message = MockMessage(content)
        
        class MockMessage:
            def __init__(self, content):
                self.content = content
        
        # Get the last message
        last_message = "No messages in history"
        if hasattr(chat_history, "messages") and len(chat_history.messages) > 0:
            last_message = chat_history.messages[-1].content
        
        return MockResponse(f"Mock response to: {last_message}")