"""
Test script to verify Groq function calling works with natural language
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

# First register/login to get a token
def get_auth_token():
    # Try to login first
    login_data = {
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    
    if response.status_code == 200:
        return response.json()["access_token"]
    
    # If login fails, register
    register_data = {
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
    if response.status_code == 200:
        return response.json()["access_token"]
    
    raise Exception(f"Failed to authenticate: {response.text}")

def send_chat_message(token, message, conversation_id=None):
    """Send a chat message"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "message": message
    }
    
    if conversation_id:
        data["conversation_id"] = conversation_id
    
    response = requests.post(f"{BASE_URL}/api/chat", json=data, headers=headers)
    return response.json()

# Test natural language inputs
def main():
    print("🔐 Getting authentication token...")
    token = get_auth_token()
    print("✅ Authenticated!")
    
    conversation_id = None
    
    # Test 1: Add task with natural language (no quotes)
    print("\n📝 Test 1: 'buy groceries'")
    result = send_chat_message(token, "buy groceries", conversation_id)
    conversation_id = result.get("conversation_id")
    print(f"Response: {result.get('response')}")
    
    # Test 2: Add another task
    print("\n📝 Test 2: 'purchase milk and bread'")
    result = send_chat_message(token, "purchase milk and bread", conversation_id)
    print(f"Response: {result.get('response')}")
    
    # Test 3: List tasks
    print("\n📋 Test 3: 'show my tasks'")
    result = send_chat_message(token, "show my tasks", conversation_id)
    print(f"Response: {result.get('response')}")
    
    # Test 4: Another way to add
    print("\n📝 Test 4: 'call the doctor'")
    result = send_chat_message(token, "call the doctor", conversation_id)
    print(f"Response: {result.get('response')}")
    
    # Test 5: List again
    print("\n📋 Test 5: 'what's on my list?'")
    result = send_chat_message(token, "what's on my list?", conversation_id)
    print(f"Response: {result.get('response')}")
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    main()
