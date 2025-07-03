# 🤖 AI Agentic Browser

> Ever wished you could tell your browser "Hey, go grab all the product prices from that e-commerce site" and it would just... do it? That's exactly what this does, but smarter.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

## 🎯 What's This All About?

Tired of writing complex scrapers that break every time a website changes its layout? Yeah, me too. 

This AI-powered browser actually *sees* web pages like you do. It doesn't care if Amazon redesigns their product pages or if LinkedIn adds new anti-bot measures. Just tell it what you want in plain English, and it figures out how to get it.

Think of it as having a really smart intern who never gets tired, never makes mistakes, and can handle any website you throw at them - even the ones with annoying CAPTCHAs.

## 🎬 See It In Action

Trust me, it's pretty cool watching an AI navigate websites like a human

[Demo Video](https://www.veed.io/view/34c948d5-9019-4055-b28a-67779917642f?panel=share)

## ✨ Why You'll Love This

### 🧠 It Actually "Sees" Websites
- Uses Google's Gemini AI to look at pages like you do
- Automatically figures out if it's looking at Amazon, LinkedIn, or your random blog
- Clicks the right buttons even when websites change their design
- Works on literally any website (yes, even the weird ones)

### 🔄 Handles the Annoying Stuff
- Gets blocked by Cloudflare? No problem, switches proxies automatically
- Encounters a CAPTCHA? Solves it with AI vision
- Website thinks it's a bot? Laughs in artificial intelligence
- Proxy goes down? Switches to a backup faster than you can blink

### 📊 Gives You Data How You Want It
- Say "save as PDF" and boom, you get a PDF
- Ask for CSV and it structures everything perfectly
- Want JSON? It knows what you mean
- Organizes everything with timestamps and metadata (because details matter)

### 🖥️ Watch It Work Live
- Stream the browser view in real-time (it's oddly satisfying)
- Click and type remotely if you need to step in
- Multiple people can watch the same session
- Perfect for debugging or just showing off

## 🚀 Getting Started (It's Actually Pretty Easy)

### What You'll Need
- Python 3.8 or newer (check with `python --version`)
- A Google AI API key (free to get, just sign up at ai.google.dev)
- Some proxies if you're planning to scrape heavily (optional but recommended)

### Let's Get This Running

1. **Grab the code**
   ```bash
   git clone https://github.com/ai-naymul/AI-Agent-Scraper.git
   cd ai-agentic-browser
   ```

2. **Install the good stuff**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   uv pip install -r requirements.txt
   ```

3. **Add your secrets**
   ```bash
   # Create a .env file (don't worry, it's gitignored)
   echo 'GOOGLE_API_KEY=your_actual_api_key_here' > .env
   echo 'SCRAPER_PROXIES=[{"server": "http://proxy1:port", "username": "user", "password": "pass"}]' >> .env
   ```

4. **Fire it up**
   ```bash
   python -m uvicorn backend.main:app --reload
   ```

5. **See the magic**
   Open `http://localhost:8000` and start telling it what to do

## 💡 Real Examples (Because Everyone Loves Examples)

### Just Getting Started
```javascript
"Go to Hacker News and save the top stories as JSON"
```
That's it. Seriously. It'll figure out the rest.

### Shopping for Data
```javascript
"Search Amazon for wireless headphones under $100 and export the results to CSV"
```
It'll navigate, search, filter, and organize everything nicely for you.

### Social Media Intel
```javascript
"Go to LinkedIn, find AI engineers in San Francisco, and save their profiles"
```
Don't worry, it handles all the login prompts and infinite scroll nonsense.

### The Wild West
```javascript
"Visit this random e-commerce site and grab all the product prices"
```
Even works on sites you've never seen before. That's the beauty of AI vision.

## 🏗️ Core Components

### 🌐 Smart Browser Controller
- Automatic anti-bot detection using AI vision
- Proxy rotation on detection/blocking
- CAPTCHA solving capabilities
- Browser restart with new proxies

### 👁️ Vision Model Integration
- Dynamic website analysis
- Anti-bot system detection
- Element interaction decisions
- CAPTCHA recognition and solving

### 📤 Universal Extractor
- AI-powered content extraction
- Multiple output format support
- Structured data organization
- Metadata preservation

### 🔧 Proxy Management
- Health tracking and statistics
- Performance-based selection
- Site-specific blocking lists
- Automatic failure recovery

## 🔥 The Cool Technical Stuff

### 📋 Smart Format Detection
Just talk to it naturally:
- "save as PDF" → Gets you a beautiful PDF
- "export to CSV" → Perfectly structured spreadsheet
- "give me JSON" → Clean, organized data structure

### 🛡️ Anti-Bot Ninja Mode
- Spots Cloudflare challenges before they even load
- Solves CAPTCHAs like a human (but faster)
- Detects rate limits and backs off gracefully
- Switches identities when websites get suspicious

### 📈 Dashboard That Actually Helps
- See which proxies are working (and which ones suck)
- Watch your browser sessions live
- Track how much you're spending on AI tokens
- Performance stats that make sense

## ⚙️ Configuration

### Proxy Configuration
```json
{
  "SCRAPER_PROXIES": [
    {
      "server": "http://proxy1.example.com:8080",
      "username": "user1",
      "password": "pass1",
      "location": "US"
    },
    {
      "server": "http://proxy2.example.com:8080",
      "username": "user2",
      "password": "pass2",
      "location": "EU"
    }
  ]
}
```

### Environment Variables
```bash
# Required
GOOGLE_API_KEY=your_gemini_api_key_here

# Optional
SCRAPER_PROXIES=your_proxy_configuration
```

## 🤝 Want to Help Make This Better?

Found a bug? Have a crazy idea? Want to add support for your favorite website? I'd love the help!

Here's how to jump in:
1. Fork this repo (there's a button for that)
2. Create a branch with a name that makes sense (`git checkout -b fix-amazon-pagination`)
3. Make your changes (and please test them!)
4. Commit with a message that explains what you did
5. Push it up and open a pull request

For big changes, maybe open an issue first so we can chat about it.

## 🙏 Acknowledgments

- [Playwright](https://playwright.dev/) for browser automation
- [Google Gemini](https://ai.google.dev/) for vision AI capabilities
- [FastAPI](https://fastapi.tiangolo.com/) for the backend framework
- Open source community for inspiration and tools