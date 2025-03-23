

class Kernel:
    """
    Mock implementation of the Semantic Kernel for testing.
    """
    def __init__(self):
        self.skills = Skills()
        self.services = {}
    
    def add_chat_service(self, service_id, service):
        """Add a chat service to the kernel"""
        self.services[service_id] = service
        return self
    
    def add_text_completion_service(self, service_id, service):
        """Add a text completion service to the kernel"""
        self.services[service_id] = service
        return self
    
    def get_service(self, service_id):
        """Get a service from the kernel"""
        return self.services.get(service_id)
    
    def import_semantic_skill_from_directory(self, skill_directory, skill_name=None):
        """Import a semantic skill from a directory"""
        return self
    
    def create_new_context(self):
        """Create a new context for function execution"""
        return Context()
    
    async def run_async(self, function, input_vars=None):
        """Run a function asynchronously"""
        if input_vars:
            return f"Mock result with vars: {input_vars}"
        return "Mock result"

class Context:
    """
    Mock context for Semantic Kernel
    """
    def __init__(self):
        self.variables = {}
    
    def __setitem__(self, key, value):
        self.variables[key] = value
    
    def __getitem__(self, key):
        return self.variables.get(key)

class Skills:
    """
    Mock skills collection for Semantic Kernel
    """
    def __init__(self):
        self.functions = {}
    
    def get_function(self, skill_name, function_name):
        """Get a function from a skill"""
        key = f"{skill_name}.{function_name}"
        return self.functions.get(key, MockFunction(function_name))

class MockFunction:
    """
    Mock function for Semantic Kernel
    """
    def __init__(self, name):
        self.name = name
    
    async def invoke_async(self, context=None, **kwargs):
        """Invoke the function asynchronously"""
        return f"Mock result from {self.name}"

class ChatRequestSettings:
    """
    Mock chat request settings
    """
    def __init__(self, temperature=0.7, max_tokens=1000, top_p=0.95):
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p

class ChatHistory:
    """
    Mock chat history
    """
    def __init__(self):
        self.messages = []
    
    def add_system_message(self, content):
        """Add a system message to the chat history"""
        self.messages.append(Message("system", content))
    
    def add_user_message(self, content):
        """Add a user message to the chat history"""
        self.messages.append(Message("user", content))
    
    def add_assistant_message(self, content):
        """Add an assistant message to the chat history"""
        self.messages.append(Message("assistant", content))

class Message:
    """
    Mock message for chat history
    """
    def __init__(self, role, content):
        self.role = role
        self.content = content