from flask import Flask, request, jsonify
import json
import os
from openai import OpenAI
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize OpenAI client with fallback
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if OPENAI_API_KEY:
    client = OpenAI(api_key=OPENAI_API_KEY)
    LLM_ENABLED = True
    logger.info("OpenAI client initialized successfully")
else:
    client = None
    LLM_ENABLED = False
    logger.warning("OpenAI API key not found. Running in mock mode.")

class PneumaFAQBot:
    def __init__(self):
        # Define 3 key intents as per assignment
        self.intents = {
            'deals_and_offers': {
                'keywords': ['deal', 'offer', 'discount', 'save', 'sweet', 'special', 'promo', 'coupon'],
                'system_prompt': """You are Pneuma's deals specialist. You help users discover and understand our current sweet-spot deals and exclusive offers.

Key facts about Pneuma deals:
- We offer curated deals across dining, travel, electronics, and lifestyle categories
- "Sweet-spot deals" are our signature high-value offers with 20-50% savings
- Deals refresh daily with new partners joining regularly
- Users can access deals through the Pneuma mobile app
- We partner with trusted brands and verified merchants only

Keep responses:
- Enthusiastic but genuine about savings
- Focused on current value propositions
- Brief and actionable
- Always direct users to check the app for latest offers

If you don't know specific deal details, direct users to the app or support@pneuma.com.""",
                'sample_phrases': [
                    "What deals do you have today?",
                    "Show me sweet spot offers",
                    "Any discounts on dining?",
                    "What's the best deal right now?"
                ]
            },
            'mileage_and_rewards': {
                'keywords': ['mile', 'point', 'transfer', 'redeem', 'reward', 'loyalty', 'earn', 'accumulate'],
                'system_prompt': """You are Pneuma's rewards program expert. You help users understand how to earn, transfer, and maximize their points and miles.

Key facts about Pneuma rewards:
- Users earn points on every purchase through partner merchants
- Points can be transferred to 15+ airline and hotel partners
- Transfer ratios vary by partner (typically 1:1 or 2:1)
- Standard users: 25K points/month transfer limit
- Premium users: 100K points/month transfer limit
- Elite users: Unlimited transfers
- Transfers process within 24-48 hours
- Points expire after 18 months of account inactivity

Keep responses:
- Clear and step-by-step for transfers
- Specific about limits and timeframes
- Educational about maximizing value
- Always mention checking account settings for personal limits

If asked about specific transfer rates or partner details, direct to the app's Rewards section.""",
                'sample_phrases': [
                    "How do I transfer miles?",
                    "What's my transfer limit?",
                    "Can I move points to Delta?",
                    "How long do transfers take?"
                ]
            },
            'account_and_setup': {
                'keywords': ['account', 'setup', 'sign up', 'register', 'login', 'getting started', 'how to', 'begin'],
                'system_prompt': """You are Pneuma's onboarding assistant. You help new users get started and existing users with account basics.

Key facts about Pneuma accounts:
- Free to sign up with email or phone number
- Available on iOS and Android
- Account verification required for rewards transfers
- Three tiers: Standard (free), Premium ($9.99/month), Elite ($19.99/month)
- Premium/Elite users get higher transfer limits and exclusive deals
- Account settings allow customization of deal categories and notifications
- Support available at support@pneuma.com for account issues

Keep responses:
- Welcoming and encouraging for new users
- Step-by-step for setup instructions
- Clear about different account tiers
- Helpful for troubleshooting basic issues

For complex account problems, always direct to support@pneuma.com.""",
                'sample_phrases': [
                    "How do I sign up?",
                    "What is Pneuma?",
                    "How do I get started?",
                    "I can't log into my account"
                ]
            }
        }
    
    def classify_intent(self, message):
        """Classify user intent based on keywords"""
        message_lower = message.lower()
        
        # Score each intent based on keyword matches
        intent_scores = {}
        for intent_name, intent_data in self.intents.items():
            score = 0
            for keyword in intent_data['keywords']:
                if keyword in message_lower:
                    score += 1
            intent_scores[intent_name] = score
        
        # Return intent with highest score, default to account_and_setup
        if max(intent_scores.values()) == 0:
            return 'account_and_setup'
        
        return max(intent_scores.items(), key=lambda x: x[1])[0]
    
    def generate_response(self, message, intent):
        """Generate response using OpenAI or fallback to mock responses"""
        if not LLM_ENABLED or client is None:
            # Fallback to mock responses when API key is not available
            return self.get_mock_response(message, intent)
        
        try:
            system_prompt = self.intents[intent]['system_prompt']
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            # Fall back to mock response on API failure
            return self.get_mock_response(message, intent)
    
    def get_mock_response(self, message, intent):
        """Generate mock responses for testing without API key"""
        mock_responses = {
            'deals_and_offers': {
                'default': "🔥 Great question about deals! Here are today's sweet-spot offers:\n• 25% off dining at partner restaurants\n• Double points on travel bookings\n• Flash electronics sale up to 40% off\n\nCheck the Pneuma app for the complete list - deals refresh daily! 📱",
                'keywords': {
                    'today': "Today's hot deals include dining discounts, travel rewards, and tech savings! Open your Pneuma app to see all current sweet-spot offers. 🎯",
                    'dining': "🍽️ Dining deals are amazing right now - 25% off at top restaurants plus double points! Check the Deals section in your Pneuma app.",
                    'best': "Our best deals right now: Premium restaurant discounts, travel point multipliers, and electronics flash sales. All verified partners with real savings!"
                }
            },
            'mileage_and_rewards': {
                'default': "✈️ Transferring miles with Pneuma is simple:\n\n1. Open the Rewards section in your app\n2. Select 'Transfer Points'\n3. Choose your airline/hotel partner\n4. Enter amount and confirm\n\nTransfers process in 24-48 hours. Your current limits are visible in Account Settings.",
                'keywords': {
                    'transfer': "Points transfer is easy! Go to Rewards → Transfer Points in your app. Choose from 15+ airline and hotel partners. Most transfers complete within 24-48 hours.",
                    'limit': "Transfer limits depend on your tier:\n• Standard: 25,000 points/month\n• Premium: 100,000 points/month\n• Elite: Unlimited\n\nCheck Account → Transfer Settings for your current limits.",
                    'delta': "Yes! Delta is one of our top transfer partners. Typical ratio is 1:1 for points to SkyMiles. Transfer through the Rewards section in your Pneuma app."
                }
            },
            'account_and_setup': {
                'default': "Welcome to Pneuma! 🎉 Getting started is easy:\n\n1. Download the Pneuma app (iOS/Android)\n2. Sign up with email or phone\n3. Verify your account\n4. Start browsing deals and earning points!\n\nNeed help? Contact support@pneuma.com",
                'keywords': {
                    'sign up': "Signing up is free and takes 2 minutes! Download the Pneuma app, enter your email/phone, verify your account, and you're ready to start saving! 🚀",
                    'pneuma': "Pneuma helps you get maximum value from your spending through curated deals and rewards. We're your personal savings sidekick with trusted partner discounts! 😊",
                    'login': "Having trouble logging in? Try resetting your password in the app, or contact our support team at support@pneuma.com - they'll get you sorted quickly!"
                }
            }
        }
        
        # Get intent-specific responses
        intent_responses = mock_responses.get(intent, mock_responses['account_and_setup'])
        
        # Check for keyword matches
        message_lower = message.lower()
        for keyword, response in intent_responses.get('keywords', {}).items():
            if keyword in message_lower:
                return response
        
        # Return default response for intent
        return intent_responses['default']
    
    def process_message(self, message):
        """Main processing function"""
        try:
            # Classify the intent
            intent = self.classify_intent(message)
            logger.info(f"Classified intent: {intent} for message: {message}")
            
            # Generate response using LLM
            response = self.generate_response(message, intent)
            
            return {
                'success': True,
                'intent': intent,
                'response': response
            }
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return {
                'success': False,
                'response': "Sorry, I had trouble processing that. Could you try asking again? If the issue persists, contact support@pneuma.com"
            }

# Initialize the bot
bot = PneumaFAQBot()

@app.route('/')
def home():
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pneuma WhatsApp Bot - LLM Powered</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .container {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            padding: 40px;
            max-width: 800px;
            width: 100%;
            animation: slideUp 0.6s ease-out;
        }
        
        @keyframes slideUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .header {
            text-align: center;
            margin-bottom: 40px;
        }
        
        .logo {
            font-size: 3rem;
            font-weight: bold;
            background: linear-gradient(45deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 10px;
        }
        
        .subtitle {
            color: #666;
            font-size: 1.2rem;
            margin-bottom: 10px;
        }
        
        .status {
            display: inline-flex;
            align-items: center;
            background: #25d366;
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 500;
        }
        
        .status::before {
            content: '●';
            margin-right: 8px;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .intents-section {
            margin-bottom: 40px;
        }
        
        .intents-title {
            font-size: 1.5rem;
            color: #333;
            margin-bottom: 20px;
            text-align: center;
        }
        
        .intent-card {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 25px;
            border-radius: 15px;
            margin-bottom: 20px;
            transition: transform 0.3s ease;
        }
        
        .intent-card:hover {
            transform: translateY(-5px);
        }
        
        .intent-title {
            font-size: 1.2rem;
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
        }
        
        .intent-samples {
            color: #666;
            font-size: 0.9rem;
            font-style: italic;
        }
        
        .chat-section {
            background: #f8f9ff;
            border-radius: 15px;
            padding: 30px;
        }
        
        .chat-header {
            display: flex;
            align-items: center;
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 2px solid #e0e6ed;
        }
        
        .whatsapp-icon {
            width: 40px;
            height: 40px;
            background: #25d366;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 15px;
            color: white;
            font-size: 1.2rem;
        }
        
        .chat-title {
            font-size: 1.4rem;
            color: #333;
            font-weight: 600;
        }
        
        .chat-form {
            display: flex;
            gap: 15px;
            align-items: stretch;
        }
        
        .message-input {
            flex: 1;
            padding: 15px 20px;
            border: 2px solid #e0e6ed;
            border-radius: 25px;
            font-size: 1rem;
            outline: none;
            transition: all 0.3s ease;
        }
        
        .message-input:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .send-btn {
            background: linear-gradient(45deg, #25d366, #20b358);
            color: white;
            border: none;
            padding: 15px 25px;
            border-radius: 25px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .send-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(37, 211, 102, 0.3);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">PNEUMA</div>
            <div class="subtitle">LLM-Powered WhatsApp Bot</div>
            <div class="status">
                GPT-3.5 Connected
            </div>
        </div>
        
        <div class="intents-section">
            <div class="intents-title">3 Key Intents</div>
            
            <div class="intent-card">
                <div class="intent-title">🎯 Deals & Offers</div>
                <div class="intent-samples">
                    "What deals do you have today?", "Show me sweet spot offers", "Any discounts on dining?"
                </div>
            </div>
            
            <div class="intent-card">
                <div class="intent-title">✈️ Mileage & Rewards</div>
                <div class="intent-samples">
                    "How do I transfer miles?", "What's my transfer limit?", "Can I move points to Delta?"
                </div>
            </div>
            
            <div class="intent-card">
                <div class="intent-title">👤 Account & Setup</div>
                <div class="intent-samples">
                    "How do I sign up?", "What is Pneuma?", "How do I get started?"
                </div>
            </div>
        </div>
        
        <div class="chat-section">
            <div class="chat-header">
                <div class="whatsapp-icon">🤖</div>
                <div class="chat-title">Test LLM Bot</div>
            </div>
            
            <form class="chat-form" action="/test" method="post">
                <input type="text" class="message-input" name="message" placeholder="Ask about deals, rewards, or account setup..." required>
                <button type="submit" class="send-btn">
                    Send to GPT
                </button>
            </form>
        </div>
    </div>
</body>
</html>"""

@app.route('/test', methods=['POST'])
def test_bot():
    """Test endpoint for LLM responses"""
    message = request.form.get('message', '')
    if not message:
        return jsonify({'error': 'No message provided'}), 400
    
    result = bot.process_message(message)
    
    # Format the response for HTML display
    formatted_response = result['response'].replace('\n', '<br>')
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pneuma Bot - LLM Response</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            padding: 40px;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        
        .logo {{
            font-size: 2.5rem;
            font-weight: bold;
            background: linear-gradient(45deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 10px;
        }}
        
        .chat-container {{
            background: #f8f9ff;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 20px;
        }}
        
        .message-bubble {{
            margin-bottom: 20px;
            padding: 15px 20px;
            border-radius: 18px;
            max-width: 80%;
            word-wrap: break-word;
        }}
        
        .user-message {{
            background: #667eea;
            color: white;
            margin-left: auto;
        }}
        
        .bot-message {{
            background: white;
            color: #333;
            border: 2px solid #e0e6ed;
            margin-right: auto;
        }}
        
        .message-info {{
            font-size: 0.8rem;
            color: #666;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .intent-badge {{
            background: #25d366;
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.7rem;
            font-weight: 500;
            text-transform: uppercase;
        }}
        
        .back-btn {{
            display: inline-flex;
            align-items: center;
            gap: 10px;
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            text-decoration: none;
            padding: 12px 24px;
            border-radius: 25px;
            font-weight: 600;
            transition: all 0.3s ease;
        }}
        
        .back-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">PNEUMA</div>
            <h2>{f"LLM-Generated Response" if LLM_ENABLED else "Mock Response (No API Key)"}</h2>
        </div>
        
        <div class="chat-container">
            <div class="message-info">
                <span>{f"🤖 GPT-3.5 Turbo" if LLM_ENABLED else "🤖 Mock Bot"}</span>
                <span class="intent-badge">{result.get('intent', 'unknown')}</span>
            </div>
            
            <div class="message-bubble user-message">
                {message}
            </div>
            
            <div class="message-bubble bot-message">
                {formatted_response}
            </div>
        </div>
        
        <a href="/" class="back-btn">
            <span>←</span>
            Test Another Message
        </a>
    </div>
</body>
</html>"""

@app.route('/webhook', methods=['POST'])
def whatsapp_webhook():
    """WhatsApp webhook endpoint for real integration"""
    try:
        data = request.get_json()
        logger.info(f"Received webhook data: {json.dumps(data, indent=2)}")
        
        # Handle different webhook formats
        message_text = None
        from_number = None
        
        # Twilio format
        if 'Body' in data:
            message_text = data['Body']
            from_number = data.get('From', 'unknown')
        # Generic webhook format
        elif 'message' in data and 'text' in data['message']:
            message_text = data['message']['text']
            from_number = data.get('from', 'unknown')
        # Direct message format for testing
        elif 'message' in data:
            message_text = data['message']
            from_number = data.get('from', 'test_user')
        
        if not message_text:
            return jsonify({'error': 'No message text found'}), 400
        
        # Process with LLM
        result = bot.process_message(message_text)
        
        if result['success']:
            response_data = {
                'success': True,
                'reply': result['response'],
                'intent': result['intent'],
                'from': from_number
            }
            logger.info(f"LLM Response: {result['response']}")
            return jsonify(response_data)
        else:
            logger.error(f"Bot processing failed: {result['response']}")
            return jsonify({'error': result['response']}), 500
            
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/webhook', methods=['GET'])
def webhook_verification():
    """Webhook verification for WhatsApp providers"""
    verify_token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    # Replace with your actual verify token
    expected_token = os.getenv('WEBHOOK_VERIFY_TOKEN', 'pneuma_verify_token_123')
    
    if verify_token == expected_token:
        return challenge
    else:
        return 'Invalid verification token', 403

@app.route('/curl-test')
def curl_test_instructions():
    """Instructions for testing with curl"""
    return """<!DOCTYPE html>
<html>
<head>
    <title>Pneuma Bot - Curl Test Instructions</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        pre { background: #2d3748; color: #e2e8f0; padding: 15px; border-radius: 5px; overflow-x: auto; }
        .endpoint { background: #e6fffa; padding: 10px; border-left: 4px solid #319795; margin: 10px 0; }
        h1 { color: #2d3748; }
        h3 { color: #4a5568; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Pneuma WhatsApp Bot - Curl Testing</h1>
        
        <h3>Test the LLM-powered webhook with curl:</h3>
        
        <div class="endpoint">
            <strong>Endpoint:</strong> POST /webhook
        </div>
        
        <h3>Test Deals & Offers Intent:</h3>
        <pre>curl -X POST http://localhost:5000/webhook \
  -H "Content-Type: application/json" \
  -d '{"message": "What deals do you have today?", "from": "test_user"}'</pre>
        
        <h3>Test Mileage & Rewards Intent:</h3>
        <pre>curl -X POST http://localhost:5000/webhook \
  -H "Content-Type: application/json" \
  -d '{"message": "How do I transfer my miles to Delta?", "from": "test_user"}'</pre>
        
        <h3>Test Account & Setup Intent:</h3>
        <pre>curl -X POST http://localhost:5000/webhook \
  -H "Content-Type: application/json" \
  -d '{"message": "How do I sign up for Pneuma?", "from": "test_user"}'</pre>
        
        <h3>Twilio Format Test:</h3>
        <pre>curl -X POST http://localhost:5000/webhook \
  -H "Content-Type: application/json" \
  -d '{"Body": "Show me sweet spot offers", "From": "+1234567890"}'</pre>
        
        <p><strong>Note:</strong> Make sure your .env file has OPENAI_API_KEY set for LLM responses to work.</p>
        
        <a href="/" style="color: #667eea;">← Back to Home</a>
    </div>
</body>
</html>"""

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)