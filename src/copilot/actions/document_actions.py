
from ...agents.document_agent import DocumentAnalysisAgent

class DocumentActions:
    def __init__(self):
        self.document_agent = DocumentAnalysisAgent()
    
    async def validate_document(self, document_type, document_content):
        """Validate a document before submission"""
        return await self.document_agent.validate_document(document_type, document_content)
    
    async def explain_document_requirements(self, document_type):
        """Explain the requirements for a specific document type"""
        return await self.document_agent.get_document_requirements(document_type)