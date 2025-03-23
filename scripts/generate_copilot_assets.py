# scripts/generate_copilot_assets.py
import argparse
import os
import sys

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.copilot.plugin_setup import MortgagePlugin

def main():
    parser = argparse.ArgumentParser(description="Generate Copilot Studio assets")
    parser.add_argument("--output", default="deployment/copilot_studio", help="Output directory")
    parser.add_argument("--manifest-only", action="store_true", help="Generate only the manifest file")
    parser.add_argument("--flows-only", action="store_true", help="Generate only the conversation flows")
    parser.add_argument("--entities-only", action="store_true", help="Generate only the entity mappings")
    
    args = parser.parse_args()
    
    plugin = MortgagePlugin()
    
    if args.manifest_only:
        plugin.generate_manifest_file(os.path.join(args.output, "manifest.json"))
    elif args.flows_only:
        plugin.export_conversation_flows(os.path.join(args.output, "flows"))
    elif args.entities_only:
        plugin.export_entity_mappings(os.path.join(args.output, "entities.json"))
    else:
        plugin.export_all(args.output)
    
if __name__ == "__main__":
    main()