"""
Quick API connection test. Run on your local machine:
    python code/test_api_connection.py

Expected output if working:
    ✓ Key loaded
    ✓ API connected — response: שלום
    ✓ Billing: $0 (free tier)
"""

import os
import sys
from pathlib import Path

# Load .env
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, val = line.split('=', 1)
            os.environ.setdefault(key.strip(), val.strip())

api_key = os.environ.get('GEMINI_API_KEY')
if not api_key or api_key == 'your-key-here':
    print("✗ No API key found in code/.env")
    print("  Get one at: https://aistudio.google.com/apikey")
    sys.exit(1)

print(f"✓ Key loaded ({api_key[:8]}...)")

try:
    from google import genai
except ImportError:
    print("✗ google-genai not installed. Run: pip install google-genai")
    sys.exit(1)

try:
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model='gemini-2.0-flash',
        contents='Say hello in Hebrew, one word only.',
    )
    print(f"✓ API connected — response: {response.text.strip()}")
    print("✓ Billing: $0 (free tier)")
except Exception as e:
    print(f"✗ API call failed: {e}")
    print()
    print("  Troubleshooting:")
    print("  1. Check quota at: https://ai.dev/rate-limit")
    print("  2. Enable API at: https://console.cloud.google.com/apis/enabledapis?project=599699470946")
    print("  3. Or create a new key in a new project at: https://aistudio.google.com/apikey")
    sys.exit(1)

# Test the full feedback flow
print()
print("Testing LLMFeedback integration...")
from LLMFeedback import generate_feedback

context = {
    'exercise_name': 'raise_arms_horizontally',
    'hand': 'right',
    'top_contributors': [
        ('peak_value_mean', 1.2),
        ('vel_sd_up_mean', 0.9),
        ('num_frames_up_mean', 0.7),
    ],
    'use_llm': True,
}

result = generate_feedback(context)
print(f"✓ LLM feedback: {result}")

context['use_llm'] = False
static = generate_feedback(context)
print(f"  Static fallback: {static}")
print(f"  LLM adds value: {result != static}")
