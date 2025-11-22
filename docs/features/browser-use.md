# Browser Use & Autonomous Browsing

Navigate websites, extract data, and automate web tasks using AI-powered browser automation.

## Overview

WYN360 CLI provides two levels of web interaction:

1. **Direct Website Fetching** - Read specific URLs directly
2. **Autonomous Browsing** - AI navigates websites and completes complex tasks

## Direct Website Fetching

### Basic Usage
```
You: Read https://github.com/yiqiao-yin/wyn360-cli

WYN360: [Fetches the specific URL directly]

📄 **Fetched:** https://github.com/yiqiao-yin/wyn360-cli

# WYN360 CLI
An intelligent AI coding assistant CLI tool...

[Full page content converted to markdown]
```

### Features
- **LLM-Optimized** - Automatic conversion to clean markdown
- **Smart Caching** - 30-minute TTL for faster repeated access
- **Smart Truncation** - Preserves document structure within token limits

## Autonomous Browsing

### Capabilities
- **Vision-Powered** - AI "sees" and understands web pages
- **Multi-Step Tasks** - Search, filter, compare, extract data
- **Form Handling** - Login, fill forms, submit data
- **Error Recovery** - Automatic retry and timeout handling

### Example Task
```
You: Browse Amazon and find the cheapest wireless mouse under $20 with good reviews

WYN360: [Launches browser, navigates, searches, filters]

🤖 **Autonomous Browsing Task Started**

Step 1: Navigating to Amazon.com ✓
Step 2: Searching for "wireless mouse" ✓
Step 3: Applying price filter (under $20) ✓
Step 4: Sorting by customer ratings ✓
Step 5: Analyzing top results ✓

✅ **Task Completed Successfully!**

**Result:** Logitech M185 Wireless Mouse
- **Price:** $14.99
- **Rating:** 4.5/5 stars (15,234 reviews)
- **Features:** 2.4GHz wireless, 12-month battery life
- **Link:** [Product Page]
```

## Setup Requirements

### Install Browser Binaries
```bash
playwright install chromium
```

### Authentication (Optional)
For sites requiring login:
```
You: Login to GitHub with my credentials

WYN360: [Handles authentication securely]
✓ Successfully logged in to GitHub
✓ Session saved for future use
```

## Configuration

```yaml
# Browser settings
browser_use_cache_enabled: true
browser_use_cache_ttl: 1800  # 30 minutes
browser_use_max_tokens: 10000
browser_use_truncate_strategy: "smart"
```

## See Also

- **[Autonomous Browsing Guide](../architecture/autonomous-browsing.md)** - Complete technical documentation
- **[Usage Examples](../usage/use-cases.md#browser-automation)** - Real-world workflows