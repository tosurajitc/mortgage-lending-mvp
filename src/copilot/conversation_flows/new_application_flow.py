# src/copilot/conversation_flows/new_application_flow.py
class NewApplicationFlow:
    """Conversation flow for handling new mortgage applications"""
    
    @staticmethod
    def get_flow_definition():
        return {
            "id": "new_application_flow",
            "name": "New Mortgage Application",
            "description": "Guides the user through submitting a new mortgage application",
            "triggers": [
                "I want to apply for a mortgage",
                "Start a new application",
                "Apply for home loan"
            ],
            "nodes": [
                {
                    "id": "collect_personal_info",
                    "type": "question",
                    "message": "Let's get started with your mortgage application. First, I'll need some personal information.",
                    "entities": ["applicant.name", "applicant.email", "applicant.phone"]
                },
                # More nodes for collecting employment, income, property info, etc.
                {
                    "id": "submit_application",
                    "type": "action",
                    "action": "submit_application",
                    "next_node": "confirmation"
                },
                {
                    "id": "confirmation",
                    "type": "message",
                    "message": "Thank you! Your application has been submitted. Your application ID is {{application_id}}. We'll begin processing it right away."
                }
            ]
        }