import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_copilot_connection():
    # Backend API base URL
    BASE_URL = os.getenv('BACKEND_API_URL', 'http://localhost:8000')
    
    # Copilot Studio API key
    API_KEY = os.getenv('COPILOT_STUDIO_API_KEY')
    
    # Test endpoint
    test_endpoint = f"{BASE_URL}/copilot/test-connection"
    
    # Headers
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {API_KEY}'
    }
    
    try:
        # Send GET request
        response = requests.get(
            test_endpoint, 
            headers=headers
        )
        
        # Check response
        print("Response Status Code:", response.status_code)
        print("Response Content:", response.json())
        
    except requests.exceptions.RequestException as e:
        print(f"Connection error: {e}")

# Run the test
if __name__ == "__main__":
    test_copilot_connection()