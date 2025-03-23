# src/copilot/conversation_flows/application_status_flow.py
class ApplicationStatusFlow:
    """Conversation flow for checking application status"""
    
    @staticmethod
    def get_flow_definition():
        return {
            "id": "application_status_flow",
            "name": "Check Application Status",
            "description": "Allows users to check the status of their mortgage application",
            "triggers": [
                "Check my application status",
                "What's the status of my application",
                "Application update"
            ],
            "nodes": [
                {
                    "id": "request_application_id",
                    "type": "question",
                    "message": "I'd be happy to check the status of your application. Could you please provide your application ID?",
                    "entities": ["application.id"]
                },
                {
                    "id": "check_status",
                    "type": "action",
                    "action": "check_application_status",
                    "action_parameters": {
                        "application_id": "{{application.id}}"
                    },
                    "next_node": "display_status"
                },
                {
                    "id": "display_status",
                    "type": "message",
                    "message": "Your application (ID: {{application.id}}) is currently {{status}}. It was submitted on {{submission_date}} and last updated on {{last_updated}}. Next steps:\n\n{{#each next_steps}}- {{this}}\n{{/each}}"
                }
            ]
        }