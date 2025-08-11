#!/usr/bin/env python3
"""
Setup script for SimilarWeb AI Scraper
"""

import os
import subprocess
import sys
from pathlib import Path

def install_requirements():
    """Install required packages"""
    requirements = [
        "playwright>=1.40.0",
        "beautifulsoup4>=4.12.0",
        "google-generativeai>=0.3.0",
        "python-dotenv>=1.0.0",
        "pillow>=10.0.0",
        "aiofiles>=23.0.0",
        "asyncio"
    ]
    
    print("📦 Installing Python packages...")
    for req in requirements:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", req])
            print(f"✅ Installed: {req}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {req}: {e}")

def setup_playwright():
    """Setup Playwright browsers"""
    print("🎭 Setting up Playwright browsers...")
    try:
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
        subprocess.check_call([sys.executable, "-m", "playwright", "install-deps"])
        print("✅ Playwright setup complete")
    except subprocess.CalledProcessError as e:
        print(f"❌ Playwright setup failed: {e}")

def create_env_file():
    """Create .env file template"""
    env_content = '''# Google AI API Key for vision model (REQUIRED)
GOOGLE_API_KEY=your_google_ai_api_key_here

# Proxy configuration (JSON array) - OPTIONAL
SCRAPER_PROXIES=[
    {"server": "http://proxy1.example.com:8080", "username": "user1", "password": "pass1"},
    {"server": "http://proxy2.example.com:8080", "username": "user2", "password": "pass2"}
]

# Test configuration
TEST_HEADLESS=false
TEST_NUM_URLS=20
'''
    
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write(env_content)
        print("📝 Created .env file template")
    else:
        print("⚠️ .env file already exists")

def create_proxy_file():
    """Create proxy file template"""
    proxy_content = '''# Proxy format: ip:port:username:password
# Example:
# 192.168.1.1:8080:user1:pass1
# 10.0.0.1:3128:user2:pass2
'''
    
    if not os.path.exists('proxies.txt'):
        with open('proxies.txt', 'w') as f:
            f.write(proxy_content)
        print("📝 Created proxies.txt template")
    else:
        print("⚠️ proxies.txt file already exists")

def create_directories():
    """Create necessary directories"""
    directories = ['test_results', 'logs', 'temp']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    print("📁 Created necessary directories")

def main():
    print("🚀 Setting up SimilarWeb AI Scraper...")
    print("="*50)
    
    install_requirements()
    setup_playwright()
    create_env_file()
    create_proxy_file()
    create_directories()
    
    print("\n" + "="*50)
    print("✅ Setup complete!")
    print("\n📋 Next steps:")
    print("1. Edit .env file with your Google AI API key")
    print("2. (Optional) Add your proxy configuration to proxies.txt or .env")
    print("3. Run the scraper:")
    print("   python similarweb_test_runner.py --help")
    print("   python similarweb_test_runner.py --test-type all --num-urls 20")
    print("\n🔗 Get Google AI API key: https://makersuite.google.com/app/apikey")

if __name__ == "__main__":
    main()
