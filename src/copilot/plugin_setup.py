
import json
import os
from datetime import datetime

class MortgagePlugin:
    def __init__(self, config_path=None):
        self.api_base_url = "https://your-api-url.com/api"  # This will be replaced with your actual API URL
        self.version = "1.0.0"
        self.plugin_manifest = self._create_plugin_manifest()
        
    def _create_plugin_manifest(self):
        """Creates the plugin manifest for Copilot Studio"""
        return {
            "schemaVersion": "1.0",
            "id": "mortgage-lending-assistant",
            "name": "Mortgage Lending Assistant",
            "version": self.version,
            "description": "Plugin to process mortgage applications and handle customer inquiries",
            "publisher": "Your Company",
            "privacyUrl": "https://www.example.com/privacy",
            "termsOfUseUrl": "https://www.example.com/terms",
            "endpoints": [
                {
                    "name": "submitApplication",
                    "description": "Submit a new mortgage application",
                    "url": f"{self.api_base_url}/applications/new",
                    "authentication": "apiKey",
                    "apiKeyLocation": "header",
                    "apiKeyName": "X-API-Key"
                },
                {
                    "name": "checkApplicationStatus",
                    "description": "Check the status of an existing application",
                    "url": f"{self.api_base_url}/applications/status",
                    "authentication": "apiKey",
                    "apiKeyLocation": "header",
                    "apiKeyName": "X-API-Key"
                },
                {
                    "name": "validateDocument",
                    "description": "Validate a document before submission",
                    "url": f"{self.api_base_url}/documents/validate",
                    "authentication": "apiKey",
                    "apiKeyLocation": "header",
                    "apiKeyName": "X-API-Key"
                },
                {
                    "name": "explainDocumentRequirements",
                    "description": "Explain the requirements for a specific document type",
                    "url": f"{self.api_base_url}/documents/requirements",
                    "authentication": "apiKey",
                    "apiKeyLocation": "header",
                    "apiKeyName": "X-API-Key"
                }
            ]
        }
        
    def generate_manifest_file(self, output_path='deployment/copilot_studio/manifest.json'):
        """Generates the manifest file for deploying to Copilot Studio"""
        # Ensure the directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(self.plugin_manifest, f, indent=4)
            
        print(f"Generated plugin manifest at {output_path}")
        
    def export_conversation_flows(self, output_dir='deployment/copilot_studio/flows'):
        """Export conversation flows for Copilot Studio"""
        # Ensure the directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Import flows
        from .conversation_flows.new_application_flow import NewApplicationFlow
        from .conversation_flows.application_status_flow import ApplicationStatusFlow
        
        # Get flow definitions
        flows = [
            NewApplicationFlow.get_flow_definition(),
            ApplicationStatusFlow.get_flow_definition()
        ]
        
        # Export each flow
        for flow in flows:
            flow_path = os.path.join(output_dir, f"{flow['id']}.json")
            with open(flow_path, 'w') as f:
                json.dump(flow, f, indent=4)
                
        print(f"Exported {len(flows)} flows to {output_dir}")
        
    def export_entity_mappings(self, output_path='deployment/copilot_studio/entities.json'):
        """Export entity mappings for Copilot Studio"""
        # Ensure the directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Import entity mappings
        from .entity_mappings import EntityMappings
        
        # Get entity definitions
        entities = EntityMappings.get_entity_definitions()
        
        # Export entities
        with open(output_path, 'w') as f:
            json.dump(entities, f, indent=4)
            
        print(f"Exported entity mappings to {output_path}")
        
    def export_all(self, base_dir='deployment/copilot_studio'):
        """Export all Copilot Studio artifacts"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_dir = f"{base_dir}_{timestamp}"
        
        self.generate_manifest_file(os.path.join(export_dir, "manifest.json"))
        self.export_conversation_flows(os.path.join(export_dir, "flows"))
        self.export_entity_mappings(os.path.join(export_dir, "entities.json"))
        
        # Create a README file
        readme_path = os.path.join(export_dir, "README.md")
        with open(readme_path, 'w') as f:
            f.write(f"# Mortgage Lending Assistant Copilot Studio Export\n\n")
            f.write(f"Export generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"## Contents\n\n")
            f.write(f"- manifest.json: Plugin definition\n")
            f.write(f"- flows/: Conversation flow definitions\n")
            f.write(f"- entities.json: Entity mapping definitions\n\n")
            f.write(f"## Import Instructions\n\n")
            f.write(f"1. In Copilot Studio, go to Settings > Plugin Manager\n")
            f.write(f"2. Click 'Add Custom Plugin'\n")
            f.write(f"3. Upload the manifest.json file\n")
            f.write(f"4. Create topics for each conversation flow\n")
            f.write(f"5. Import entities from entities.json\n")
        
        print(f"Exported all Copilot Studio artifacts to {export_dir}")