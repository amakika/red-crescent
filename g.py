import requests
import json

# Configuration
API_URL = "https://redcresent22.onrender.com/api/login"
TEST_USER = {
    "username": "yasin",  # Replace with actual test username
    "password": "yasinatay"   # Replace with actual test password
}

def test_login_endpoint():
    try:
        print(f"Testing login endpoint at: {API_URL}")
        
        # Make the POST request
        response = requests.post(
            API_URL,
            json=TEST_USER,
            headers={'Content-Type': 'application/json'}
        )
        
        # Print response details
        print("\nResponse Status Code:", response.status_code)
        print("Response Headers:", response.headers)
        
        try:
            response_data = response.json()
            print("Response Body:", json.dumps(response_data, indent=2))
        except ValueError:
            print("Response Body (non-JSON):", response.text)
        
        # Evaluate the response
        if response.status_code == 200:
            print("\n✅ Login successful!")
            print("Access Token:", response_data.get('access'))
        elif response.status_code == 400:
            print("\n❌ Bad request: Missing or invalid parameters")
        elif response.status_code == 401:
            print("\n❌ Unauthorized: Invalid credentials")
        elif response.status_code == 500:
            print("\n❌ Server error: Check server logs")
        else:
            print(f"\n❌ Unexpected status code: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request failed: {str(e)}")

if __name__ == "__main__":
    test_login_endpoint()