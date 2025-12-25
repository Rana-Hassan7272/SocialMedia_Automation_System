"""
Twitter API Configuration Checker.
Diagnoses Twitter API setup issues.
"""

from src.config import settings

print("🔍 Twitter API Configuration Checker\n")
print("=" * 60)

# Check if Twitter is configured
print("1. Checking if Twitter credentials are set...")
try:
    is_configured = settings.is_twitter_configured()
    print(f"   ✅ Twitter configured: {is_configured}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Check individual credentials
print("\n2. Checking individual credentials...")

credentials = {
    "API Key (Consumer Key)": settings.twitter_api_key,
    "API Secret (Consumer Secret)": settings.twitter_api_secret,
    "Access Token": settings.twitter_access_token,
    "Access Token Secret": settings.twitter_access_token_secret
}

for name, value in credentials.items():
    if value and len(value) > 5:
        masked = value[:5] + "..." + value[-5:]
        print(f"   ✅ {name}: {masked}")
    else:
        print(f"   ❌ {name}: NOT SET or TOO SHORT")

# Try to initialize Twitter client
print("\n3. Testing Twitter client initialization...")
try:
    from src.utils import TwitterClient
    client = TwitterClient()
    print("   ✅ Twitter client initialized successfully")
    
    # Try to get authenticated user info
    print("\n4. Testing API connection...")
    try:
        me = client.client.get_me()
        if me.data:
            print(f"   ✅ Connected as: @{me.data.username}")
        else:
            print("   ⚠️  Connected but couldn't get user info")
    except Exception as e:
        print(f"   ❌ API test failed: {str(e)}")
        if "403" in str(e):
            print("\n   💡 403 Error means:")
            print("      - Your app doesn't have 'Read and Write' permissions")
            print("      - OR you need to regenerate Access Token after changing permissions")
            print("\n   📋 Steps to fix:")
            print("      1. Go to https://developer.twitter.com/en/portal/dashboard")
            print("      2. Select your app")
            print("      3. Go to 'App permissions'")
            print("      4. Change to 'Read and Write'")
            print("      5. Go to 'Keys and tokens'")
            print("      6. REGENERATE Access Token & Secret")
            print("      7. Update .env with NEW tokens")
        
except Exception as e:
    print(f"   ❌ Failed to initialize: {str(e)}")

print("\n" + "=" * 60)
print("\n📚 Required credentials in .env:")
print("   TWITTER_API_KEY=your_consumer_key")
print("   TWITTER_API_SECRET=your_consumer_secret")
print("   TWITTER_ACCESS_TOKEN=your_access_token")
print("   TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret")
print("\n⚠️  All 4 are required for posting tweets!")
