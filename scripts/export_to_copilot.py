
import os
import json
import argparse
from src.copilot.conversation_flows.new_application_flow import NewApplicationFlow
from src.copilot.entity_mappings import EntityMappings
from src.copilot.plugin_setup import MortgagePlugin

def export_flows(output_dir):
    """Export conversation flows for import into Copilot Studio"""
    os.makedirs(output_dir, exist_ok=True)
    
    # Export flows
    flows = [
        NewApplicationFlow.get_flow_definition(),
        # Add other flows
    ]
    
    for flow in flows:
        with open(os.path.join(output_dir, f"{flow['id']}.json"), 'w') as f:
            json.dump(flow, f, indent=2)
    
    # Export entities
    entities = EntityMappings.get_entity_definitions()
    with open(os.path.join(output_dir, "entities.json"), 'w') as f:
        json.dump(entities, f, indent=2)
    
    # Export plugin manifest
    plugin = MortgagePlugin()
    plugin.generate_manifest_file(os.path.join(output_dir, "manifest.json"))
    
    print(f"Exported {len(flows)} flows, {len(entities)} entities, and plugin manifest to {output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export flows to Copilot Studio")
    parser.add_argument("--output", default="deployment/copilot_studio", help="Output directory")
    args = parser.parse_args()
    
    export_flows(args.output)