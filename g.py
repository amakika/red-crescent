import requests
import json

# API URLs
LOGIN_URL = "https://red-crescent-production.up.railway.app/api/login/"
USERS_URL = "https://red-crescent-production.up.railway.app/api/users/"

# Test user credentials
TEST_USER = {
    "username": "testuser",  # Replace with actual test username
    "password": "testpass123"   # Replace with actual test password
}

def get_auth_token():
    """Authenticate and retrieve the JWT token."""
    try:
        print(f"Authenticating at: {LOGIN_URL}")
        response = requests.post(
            LOGIN_URL,
            json=TEST_USER,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            print("\n✅ Login successful!")
            return response.json().get('access')  # Return the access token
        else:
            print(f"\n❌ Login failed. Status code: {response.status_code}")
            print("Response:", response.text)
            return None
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request failed: {str(e)}")
        return None

def test_users_endpoint(token):
    """Test the /api/users/ endpoint with the provided token."""
    try:
        print(f"\nTesting users endpoint at: {USERS_URL}")
        
        # Make the GET request with the token
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        response = requests.get(USERS_URL, headers=headers)
        
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
            print("\n✅ Users endpoint successful!")
        elif response.status_code == 401:
            print("\n❌ Unauthorized: Invalid or missing token")
        elif response.status_code == 500:
            print("\n❌ Server error: Check server logs")
        else:
            print(f"\n❌ Unexpected status code: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request failed: {str(e)}")

if __name__ == "__main__":
    # Step 1: Authenticate and get the token
    token = get_auth_token()
    
    if token:
        # Step 2: Test the /api/users/ endpoint with the token
        test_users_endpoint(token)
    else:
        print("\n❌ Cannot proceed without a valid token.")