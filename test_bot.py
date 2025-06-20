# !/usr/bin/env python3
"""
Local testing script for Pneuma WhatsApp Bot
Run this to test the bot without needing WhatsApp integration
"""

import requests
import json
import sys
import time

# Test messages for each intent
TEST_MESSAGES = {
    "General FAQ": [
        "What is Pneuma?",
        "How does it work?",
        "I need help with my account",
        "Tell me about your services"
    ],
    "Deals & Offers": [
        "What are today's deals?",
        "Show me current offers",
        "Any sweet deals available?",
        "I want to save money"
    ],
    "Mileage Transfer": [
        "How do I transfer points?",
        "Can I move my miles?",
        "What are the transfer limits?",
        "I want to redeem rewards"
    ]
}

def test_local_bot(base_url="http://localhost:5000"):
    """Test the bot locally using the /webhook endpoint"""
    
    print("🤖 Testing Pneuma WhatsApp Bot v0.1")
    print("=" * 50)
    
    # Test if server is running
    try:
        response = requests.get(f"{base_url}")
        if response.status_code != 200:
            print("❌ Server not responding. Make sure to run 'python app.py' first!")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure to run 'python app.py' first!")
        print("   Run this in another terminal: python app.py")
        return False
    
    print(f"✅ Server is running at {base_url}")
    print()
    
    # Test each intent category
    for category, messages in TEST_MESSAGES.items():
        print(f"🧪 Testing: {category}")
        print("-" * 30)
        
        for i, message in enumerate(messages, 1):
            print(f"\n{i}. User: {message}")
            
            # Send message to bot
            webhook_data = {
                "Body": message,
                "From": "+1234567890"
            }
            
            try:
                response = requests.post(
                    f"{base_url}/webhook",
                    json=webhook_data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"   Bot ({data.get('intent', 'unknown')}): {data.get('reply', 'No response')}")
                else:
                    print(f"   ❌ Error: {response.status_code} - {response.text}")
                    
            except requests.exceptions.Timeout:
                print("   ❌ Request timed out")
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
            
            # Brief pause between requests
            time.sleep(0.5)
        
        print("\n" + "=" * 50)
    
    print("\n✅ Testing complete!")
    print("\n💡 You can also test interactively at: http://localhost:5000")
    return True

def test_curl_examples():
    """Show curl examples for testing"""
    print("\n🔧 Manual Testing with cURL:")
    print("-" * 30)
    
    curl_examples = [
        {
            "name": "General FAQ",
            "command": '''curl -X POST http://localhost:5000/webhook \\
  -H "Content-Type: application/json" \\
  -d '{"Body": "What is Pneuma?", "From": "+1234567890"}'
'''
        },
        {
            "name": "Deals Query", 
            "command": '''curl -X POST http://localhost:5000/webhook \\
  -H "Content-Type: application/json" \\
  -d '{"Body": "Show me today\\'s deals", "From": "+1234567890"}'
'''
        },
        {
            "name": "Mileage Transfer",
            "command": '''curl -X POST http://localhost:5000/webhook \\
  -H "Content-Type: application/json" \\
  -d '{"Body": "How do I transfer points?", "From": "+1234567890"}'
'''
        }
    ]
    
    for example in curl_examples:
        print(f"\n{example['name']}:")
        print(example['command'])

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--curl":
        test_curl_examples()
    else:
        success = test_local_bot()
        if success:
            test_curl_examples()