# src/copilot/actions/application_actions.py
from ...agents.orchestrator import OrchestratorAgent

class ApplicationActions:
    def __init__(self):
        self.orchestrator = OrchestratorAgent()
    
    async def submit_application(self, applicant_data, loan_details, property_info):
        """Submit a new mortgage application"""
        return await self.orchestrator.process_new_application(
            applicant_data, loan_details, property_info
        )
    
    async def check_application_status(self, application_id):
        """Check the status of an existing application"""
        return await self.orchestrator.get_application_status(application_id)
    
    async def provide_additional_documents(self, application_id, document_type, document_content):
        """Add additional documents to an existing application"""
        return await self.orchestrator.add_document(
            application_id, document_type, document_content
        )