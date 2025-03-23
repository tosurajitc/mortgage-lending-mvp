
class AssistantAgent:
    """
    Mock implementation of the Assistant Agent for testing.
    """
    def __init__(self, name, system_message, llm_config=None):
        self.name = name
        self.system_message = system_message
        self.llm_config = llm_config or {}
    
    async def analyze_document(self, document_data):
        """Mock document analysis"""
        return {
            "analysis": f"Mock analysis of document: {document_data.get('document_type', 'unknown')}",
            "extracted_data": {},
            "confidence": 0.95
        }
    
    async def generate_response(self, prompt):
        """Generate a response"""
        return f"Mock response from {self.name}: {prompt[:30]}..."