"""
Test script for Multilingual Chatbot
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def test_chat(message, language='English'):
    """Test the chatbot with a message"""
    print(f"\n💬 Testing: '{message}' ({language})")
    
    payload = {
        'message': message,
        'language': language
    }
    
    response = requests.post(
        f"{BASE_URL}/api/chat",
        json=payload
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print(f"🤖 Response: {data.get('response', 'No response')}")
            print(f"📋 Intent: {data.get('intent', 'Unknown')}")
        else:
            print(f"❌ Error: {data.get('error', 'Unknown error')}")
    else:
        print(f"❌ HTTP Error: {response.status_code}")

def test_all_languages():
    """Test chatbot in all languages"""
    print("=" * 50)
    print("🧪 MULTILINGUAL CHATBOT TEST")
    print("=" * 50)
    
    # Test greetings
    print("\n--- GREETINGS ---")
    test_chat("Hello", "English")
    test_chat("Mhoro", "Shona")
    test_chat("Sawubona", "Ndebele")
    
    # Test crop questions
    print("\n--- CROP INFORMATION ---")
    test_chat("Tell me about maize", "English")
    test_chat("Ndinoda ruzivo nezve chibage", "Shona")
    test_chat("Ngicela ulwazi nge-umbila", "Ndebele")
    
    # Test specific topics
    print("\n--- FARMING TOPICS ---")
    test_chat("How do I prepare soil?", "English")
    test_chat("Ndinogadzirira sei ivhu?", "Shona")
    test_chat("Ngilungisa kanjani umhlabathi?", "Ndebele")
    
    test_chat("What about pests?", "English")
    test_chat("Zvipembenene?", "Shona")
    test_chat("Izinambuzane?", "Ndebele")
    
    test_chat("When should I harvest?", "English")
    test_chat("Ndinofanira kukohwa rini?", "Shona")
    test_chat("Ngivuna nini?", "Ndebele")
    
    # Test financial inclusion topics
    print("\n--- FINANCIAL INCLUSION ---")
    test_chat("How can I get a loan?", "English")
    test_chat("Ndingawana sei kiredhiti?", "Shona")
    test_chat("Ngingayithola kanjani imali mboleko?", "Ndebele")
    
    # Test data sovereignty
    print("\n--- DATA SOVEREIGNTY ---")
    test_chat("Who can see my data?", "English")
    test_chat("Ndiani anogona kuona data yangu?", "Shona")
    test_chat("Ngubani ongabona idatha yami?", "Ndebele")
    
    # Test general question
    print("\n--- GENERAL QUESTIONS ---")
    test_chat("Help me with farming", "English")
    test_chat("Ndifuna rubatsiro nekurima", "Shona")
    test_chat("Ngicela usizo ngolimo", "Ndebele")

if __name__ == "__main__":
    test_all_languages()