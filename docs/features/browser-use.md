# Advanced Browser Automation & Control

Navigate websites, extract data, and automate complex web tasks using DOM-first browser automation with intelligent fallbacks.

## Overview

WYN360 CLI provides advanced web interaction capabilities:

1. **Direct Website Fetching** - Read specific URLs directly
2. **DOM-First Browser Automation** - Fast, cost-effective automation using page structure
3. **Stagehand Code Generation** - AI-generated automation for complex scenarios
4. **Vision Fallback** - Vision-based analysis for visual-heavy interfaces
5. **Interactive Error Recovery** - LLM-assisted troubleshooting and recovery

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

## Advanced Browser Automation

### Multi-Layered Approach
The system intelligently selects the best automation method:

🔍 **DOM Analysis (Primary)** → 🤖 **Stagehand AI** → 👁️ **Vision Fallback**

### Browser Visibility Control

Control browser visibility for debugging and development:

```bash
# Show browser window during automation (great for debugging)
wyn360 --show-browser

# Environment variable option
export WYN360_BROWSER_SHOW=1
wyn360

# Default headless mode (production)
wyn360
```

### Automation Capabilities
- **Cost-Optimized** - 80-90% cheaper than vision-only approaches
- **Multi-Step Tasks** - Search, filter, compare, extract data automatically
- **Form Handling** - Login, fill forms, submit data with error handling
- **Interactive Recovery** - LLM-assisted error analysis and user-guided recovery
- **Pattern Learning** - Caches successful approaches for performance

### Example: E-commerce Automation

```
You: Browse Amazon and find the cheapest wireless mouse under $20 with good reviews

WYN360: [Launches intelligent browser automation]

🎯 **Intelligent Browser Automation Started**
📊 **Approach:** DOM Analysis (confidence: 87%)

Step 1: 🔍 Analyzing page structure ✓
Step 2: 🔎 Executing search for "wireless mouse" ✓
Step 3: 💰 Applying price filter (under $20) ✓
Step 4: ⭐ Filtering by ratings (4+ stars) ✓
Step 5: 📋 Comparing top results ✓

✅ **Task Completed Successfully!**
💡 **Approach Used:** DOM-First Analysis
⚡ **Performance:** 8 seconds, $0.02 cost

**Result:** Logitech M185 Wireless Mouse
- **Price:** $14.99
- **Rating:** 4.5/5 stars (15,234 reviews)
- **Features:** 2.4GHz wireless, 12-month battery life
- **Link:** [Product Page]

**Cost Breakdown:**
- DOM Analysis: $0.015
- Action Execution: $0.005
- Total Savings vs Vision: 91%
```

### Example: Interactive Error Recovery

```
You: Complete my shopping cart checkout

WYN360: [Automation encounters unexpected issue]

🔄 **Automation Challenge Detected**

🧠 **LLM Analysis:** The checkout page requires email verification. A verification code was sent to your email.

📋 **Smart Recovery Options:**
1. 🔄 Retry same approach with 30s wait
2. 🔀 Try Stagehand approach for complex forms
3. 🖥️ Show browser for manual email verification
4. ✏️ Modify task: "Navigate to email verification step"
5. 👤 Manual intervention mode
6. ❌ Abort checkout process

Your choice [1-6]: 3

🖥️ **Browser now visible for manual verification**
Please complete the email verification, then press Enter to continue automation...

[User completes verification]
✅ **Verification completed! Resuming automation...**

Step 6: 🛒 Proceeding to payment selection ✓
Step 7: 💳 Filling payment information ✓
Step 8: ✅ Completing checkout ✓

🎉 **Checkout completed successfully!**
```

## Automation Approaches

### 1. DOM Analysis (Primary)
- **Speed:** ⚡ 2-3 seconds per action
- **Cost:** 💰 ~$0.001 per action
- **Best For:** Standard web interactions, forms, searches
- **Success Rate:** ~85% of web tasks

### 2. Stagehand AI Generation
- **Speed:** 🚀 5-8 seconds per complex action
- **Cost:** 💰 ~$0.01 per generated pattern
- **Best For:** Complex multi-step workflows, dynamic content
- **Success Rate:** ~92% with caching

### 3. Vision Fallback
- **Speed:** 🐌 15-20 seconds per action
- **Cost:** 💰 ~$0.05 per screenshot analysis
- **Best For:** Visual-heavy interfaces, image-based navigation
- **Usage:** <5% of tasks (edge cases only)

## Setup Requirements

### Install Browser Binaries
```bash
# Install Playwright browser
playwright install chromium

# Verify installation
playwright --version
```

### Environment Configuration
```bash
# Browser control settings
export WYN360_BROWSER_SHOW=1                    # Show browser (0 for headless)
export WYN360_DOM_CONFIDENCE_THRESHOLD=0.7      # DOM confidence threshold
export WYN360_STAGEHAND_CACHE=true              # Enable pattern caching

# Cost control settings
export WYN360_MAX_COST_PER_TASK=0.50             # Maximum cost per automation
export WYN360_PREFER_CHEAP_APPROACHES=true      # Favor DOM over vision
```

### Authentication Setup (Optional)
For sites requiring login:
```
You: Login to GitHub using my credentials

WYN360: [Initiates secure authentication flow]
🔐 Please enter your credentials:
Username: [securely prompted]
Password: [securely masked]

✅ Successfully logged in to GitHub
💾 Session saved for 30 minutes
🔒 Credentials securely handled (not stored)
```

## Advanced Features

### Cost & Performance Tracking

Check detailed automation analytics:
```
You: /tokens

WYN360: 📊 **Token Usage & Cost Breakdown**

**Total Session Cost:** $0.23

**Browser Automation:**
- DOM Analysis: $0.05 (75% of actions)
- Stagehand Generation: $0.08 (20% of actions)
- Vision Fallback: $0.10 (5% of actions)

**Performance Metrics:**
- Average task completion: 12 seconds
- Cost savings vs vision-only: 87%
- Success rate: 94%

**Approach Distribution:**
█████████████████████ DOM (75%)
█████ Stagehand (20%)
██ Vision (5%)
```

### Pattern Learning & Caching

The system learns and caches successful automation patterns:
```
📚 **Pattern Cache Status**
- Cached patterns: 23
- Cache hit rate: 67%
- Performance improvement: 2.3x faster
- Most successful: E-commerce search patterns
```

### Strategy Selection

Control which automation approach to use:
```python
# Let system choose automatically (recommended)
"Browse Amazon for headphones"
# System: Uses DOM analysis (fastest/cheapest)

# Force specific approach for testing
"Browse Amazon for headphones using vision"
# System: Uses vision-based analysis

# Hybrid approach
"Browse complex booking site for flights"
# System: DOM → Stagehand → Vision as needed
```

## Configuration

### Browser Behavior
```yaml
# Fine-tune automation in agent config
automation_config:
  dom_confidence_threshold: 0.7      # Higher = more DOM usage
  enable_stagehand_cache: true       # Cache successful patterns
  vision_fallback_enabled: true     # Allow vision when needed
  max_retries_per_approach: 2       # Retry attempts
  show_browser: false               # Default headless mode
```

### Cost Controls
```yaml
# Budget management
cost_controls:
  max_cost_per_task: 0.50           # Stop if exceeding 50¢
  prefer_cheap_approaches: true     # Favor DOM/Stagehand over vision
  track_spending: true              # Real-time cost monitoring
  daily_budget: 10.00               # Daily automation budget
```

## Troubleshooting

### Browser Not Showing
**Problem:** `--show-browser` flag not working

**Solutions:**
```bash
# Check environment variable
echo $WYN360_BROWSER_SHOW

# Set explicitly
export WYN360_BROWSER_SHOW=1
wyn360

# Or use CLI flag (overrides environment)
wyn360 --show-browser
```

### Task Not Completing
**Problem:** Automation fails or gets stuck

**Solutions:**
1. **Enable browser visibility:** `wyn360 --show-browser`
2. **Check interactive recovery:** Follow LLM suggestions
3. **Try different approach:** Ask for "using Stagehand" or "using vision"
4. **Simplify task:** Break complex requests into smaller steps

### High Costs
**Problem:** Automation costs more than expected

**Solutions:**
1. **Check approach distribution:** Use `/tokens` command
2. **Lower vision usage:** Increase DOM confidence threshold
3. **Enable caching:** Set `WYN360_STAGEHAND_CACHE=true`
4. **Use targeted URLs:** Start closer to your goal

### Authentication Issues
**Problem:** Can't access logged-in content

**Solutions:**
1. **Login first:** Use explicit login request
2. **Check session:** Sessions last 30 minutes
3. **Clear cache:** If cookies are corrupted
4. **Manual intervention:** Use show-browser for complex auth

## Best Practices

### 1. Optimize for Speed & Cost
```bash
# Good: Specific, DOM-friendly tasks
"Find product price on Amazon product page"

# Better: Start closer to goal
"Find price of ASIN B08XYZ123 on Amazon"

# Best: Combine with targeted URLs
"Check price of [specific product URL]"
```

### 2. Use Browser Visibility Strategically
```bash
# Development & debugging
wyn360 --show-browser

# Production & scripts
wyn360  # headless for speed

# Specific debugging
"Browse to checkout using show browser"
```

### 3. Leverage Error Recovery
```bash
# When automation gets stuck, follow LLM suggestions:
"The page requires CAPTCHA verification"
→ Choice: Show browser for manual completion
→ Complete manually, then resume automation
```

### 4. Monitor Performance
```bash
# Regular cost checking
/tokens

# Adjust thresholds based on usage
export WYN360_DOM_CONFIDENCE_THRESHOLD=0.8  # More DOM usage
```

## Real-World Examples

### E-commerce Price Comparison
```
You: Compare wireless earbuds prices across Amazon, Best Buy, and Target

WYN360: [Automated cross-site comparison]
🔍 **Multi-Site Price Comparison**

**Amazon:** Sony WF-1000XM4 - $199.99 (4.3⭐)
**Best Buy:** Sony WF-1000XM4 - $189.99 (4.5⭐) ← Best Deal
**Target:** Sony WF-1000XM4 - $209.99 (4.2⭐)

💡 **Recommendation:** Best Buy offers the lowest price
⚡ **Performance:** DOM analysis for all sites (2.3s average)
💰 **Cost:** $0.04 total (vs $0.45 with vision-only)
```

### Research & Data Extraction
```
You: Gather the latest iPhone reviews and ratings from tech websites

WYN360: [Intelligent content extraction]
📱 **iPhone Review Compilation**

**TechRadar:** iPhone 15 Pro - 4.5/5
- Pros: Excellent camera, titanium build
- Cons: High price, no significant innovation

**GSMArena:** iPhone 15 Pro - 8.7/10
- Battery: 89h endurance rating
- Camera: 48MP main, improved night mode

**The Verge:** iPhone 15 Pro - 8/10
- "Incremental but meaningful improvements"
- USB-C transition praised

🎯 **Extraction Method:** DOM + Stagehand for dynamic content
⏱️ **Time:** 45 seconds across 3 sites
💸 **Cost:** $0.12 (85% savings vs vision)
```

## Performance Metrics

### **Benchmark Comparison**

| Task Type | Vision-Only (Old) | DOM-First (New) | Improvement |
|-----------|------------------|-----------------|-------------|
| **Product Search** | $0.25, 45s | $0.03, 12s | 88% cost ↓, 73% time ↓ |
| **Form Submission** | $0.40, 60s | $0.08, 18s | 80% cost ↓, 70% time ↓ |
| **Data Extraction** | $0.15, 30s | $0.02, 8s | 87% cost ↓, 73% time ↓ |
| **Multi-Page Flow** | $0.50, 90s | $0.12, 25s | 76% cost ↓, 72% time ↓ |

### **Success Rates by Approach**
- **DOM Analysis:** 85% success rate
- **Stagehand AI:** 92% success rate
- **Vision Fallback:** 96% success rate
- **Combined System:** 94% overall success rate

## API Integration

For programmatic usage:

```python
from wyn360_cli.agent import WYN360Agent

# Initialize with browser control
agent = WYN360Agent(
    api_key="your_key",
    show_browser=False,  # Headless by default
    max_cost_per_task=0.50
)

# Intelligent automation
result = await agent.browse_page_intelligently(
    ctx=None,
    url="https://example-site.com",
    task="Find and extract pricing information",
    strategy="auto"  # auto, dom, stagehand, vision
)

# Structured data extraction
data = await agent.extract_page_data(
    ctx=None,
    url="https://product-page.com",
    schema={
        "title": str,
        "price": float,
        "rating": float,
        "availability": bool
    }
)
```

## See Also

- **[Complete Technical Guide](../architecture/autonomous-browsing.md)** - Full architecture documentation
- **[Usage Examples](../usage/use-cases.md#browser-automation)** - Real-world automation workflows
- **[Cost Optimization Guide](../cost-management.md)** - Managing automation expenses
- **[Troubleshooting Guide](../troubleshooting/browser-automation.md)** - Common issues and solutions

---

*Updated for WYN360-CLI v0.3.68*
*DOM-First Browser Automation with Intelligent Fallbacks*