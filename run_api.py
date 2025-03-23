# run_api.py
import sys
import os
import importlib
import uvicorn

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Define a function to modify imports dynamically
def fix_imports():
    # Try to patch the base_agent module
    try:
        # First try to fix the utils import
        sys.modules['utils'] = importlib.import_module('src.utils')
        sys.modules['utils.logging_utils'] = importlib.import_module('src.utils.logging_utils')
        
        # Then try to fix the security import
        sys.modules['security'] = importlib.import_module('src.security')
        sys.modules['security.validation'] = importlib.import_module('src.security.validation')
        
        # Fix the copilot imports
        sys.modules['copilot'] = importlib.import_module('src.copilot')
        sys.modules['copilot.actions'] = importlib.import_module('src.copilot.actions')
        
        # Fix any other imports that might be needed
        print("Import paths patched successfully")
    except Exception as e:
        print(f"Error patching imports: {str(e)}")
        # Continue anyway - at least we tried

# Try to fix imports
fix_imports()

# Run the API
if __name__ == "__main__":
    print("Starting API server...")
    uvicorn.run("src.api.endpoints:app", host="127.0.0.1", port=8000, reload=True)