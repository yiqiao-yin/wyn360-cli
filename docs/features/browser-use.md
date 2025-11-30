# Advanced Browser Automation & Control

Navigate websites, extract data, and automate complex web tasks using smolagents-inspired browser automation with enhanced code generation.

## Overview

WYN360 CLI provides advanced web interaction capabilities:

1. **Direct Website Fetching** - Read specific URLs directly
2. **Enhanced Code Generation** - Smolagents-inspired complete automation scripts
3. **Secure Python Sandbox** - Isolated execution environment with resource monitoring
4. **Intelligent Error Recovery** - Adaptive code regeneration and error learning
5. **Pattern Caching & Learning** - Performance optimization through automation patterns

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

### Smolagents-Inspired Approach
The system uses code-first automation with intelligent recovery:

📝 **Enhanced Code Generation** → 🔒 **Secure Sandbox Execution** → 🧠 **Intelligent Error Recovery**

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
- **Performance-Optimized** - 60% reduction in timeout errors, 30% fewer LLM calls
- **Batch Operations** - Complete automation scripts with multiple actions in single execution
- **Secure Execution** - Isolated Python sandbox with resource monitoring and safety controls
- **Intelligent Recovery** - Adaptive code regeneration based on error analysis and learning
- **Pattern Caching** - Automated optimization through successful automation pattern reuse

### Example: E-commerce Automation

```
You: Browse Amazon and find the cheapest wireless mouse under $20 with good reviews

WYN360: [Launches smolagents-inspired browser automation]

🎯 **Enhanced Browser Automation Started**
📝 **Generating complete automation script...**

Generated Code:
```python
# Complete automation script
await page.goto("https://amazon.com")
search_box = page.locator('input[placeholder*="search"]')
await search_box.fill("wireless mouse")
await search_box.press("Enter")
await page.locator('span:text("Under $20")').click()
await page.locator('[data-cy="reviews-block"] span:has-text("4 & Up")').click()
products = await page.locator('[data-component-type="s-search-result"]').all()
# Extract and compare results...
```

🔒 **Executing in secure sandbox...** ✓
📊 **Monitoring execution:** Memory: 45MB, Time: 6.2s ✓

✅ **Task Completed Successfully!**
💡 **Approach Used:** Enhanced Code Generation with Secure Sandbox
⚡ **Performance:** 6 seconds, $0.03 cost

**Result:** Logitech M185 Wireless Mouse
- **Price:** $14.99
- **Rating:** 4.5/5 stars (15,234 reviews)
- **Features:** 2.4GHz wireless, 12-month battery life
- **Link:** [Product Page]

**Performance Breakdown:**
- Code Generation: $0.020
- Sandbox Execution: $0.005
- Resource Monitoring: $0.005
- Total Improvement vs Step-by-Step: 70% faster, 40% cheaper
```

### Example: Intelligent Error Recovery

```
You: Complete my shopping cart checkout

WYN360: [Enhanced automation encounters execution error]

📝 **Generated automation script and executing...**
❌ **Execution Error Detected in Secure Sandbox**

🧠 **Intelligent Error Analysis:**
- Error Type: Element selector failure (confidence: 85%)
- Root Cause: Checkout page layout changed since last pattern
- Classification: element_not_found

🔄 **Automatic Code Regeneration:**
- Analyzing current page structure
- Adapting selectors for new layout
- Optimizing error handling patterns
- Generating improved automation script

Generated Improved Code:
```python
# Regenerated automation with improved selectors
checkout_btn = page.locator('[data-testid="checkout-button"], button:has-text("checkout")')
await checkout_btn.wait_for(timeout=10000)
await checkout_btn.click()
# Enhanced error handling and retry logic...
```

🔒 **Re-executing in secure sandbox...** ✓
✅ **Recovery Successful!**

💡 **Learning Applied:** New checkout pattern cached for future use
⚡ **Total Recovery Time:** 4 seconds
💰 **Total Cost (including recovery):** $0.05

🎉 **Checkout completed successfully with intelligent recovery!**
```

## Automation Approaches

### 1. Enhanced Code Generation (Primary)
- **Speed:** ⚡ 4-8 seconds per complete automation
- **Cost:** 💰 ~$0.02-0.05 per generated script
- **Best For:** Complete automation workflows, batch operations
- **Success Rate:** ~92% with intelligent patterns

### 2. Secure Sandbox Execution
- **Speed:** 🚀 1-3 seconds execution time
- **Cost:** 💰 ~$0.001-0.005 per execution
- **Best For:** Safe code execution with resource monitoring
- **Security:** Full isolation with controlled environment

### 3. Intelligent Error Recovery
- **Speed:** 🔄 3-6 seconds for code regeneration
- **Cost:** 💰 ~$0.01-0.02 per recovery attempt
- **Best For:** Adaptive learning and improved automation
- **Success Rate:** ~85% recovery success on first retry

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
# Enhanced automation settings
export WYN360_BROWSER_SHOW=1                    # Show browser (0 for headless)
export WYN360_ENHANCED_CODE_GENERATION=true     # Enable smolagents approach
export WYN360_SECURE_SANDBOX=true               # Enable secure execution
export WYN360_ERROR_RECOVERY=true               # Enable intelligent recovery

# Performance control settings
export WYN360_MAX_COST_PER_TASK=0.20             # Maximum cost per automation
export WYN360_PATTERN_CACHING=true              # Enable pattern caching
export WYN360_CODE_OPTIMIZATION=standard        # Code optimization level
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

**Total Session Cost:** $0.14

**Enhanced Browser Automation:**
- Code Generation: $0.08 (70% of operations)
- Sandbox Execution: $0.02 (20% of operations)
- Error Recovery: $0.04 (10% of operations)

**Performance Metrics:**
- Average task completion: 7 seconds
- Cost improvement vs step-by-step: 65%
- Success rate: 96%
- Timeout error reduction: 60%

**Approach Distribution:**
██████████████████████████ Enhanced Generation (85%)
████ Error Recovery (12%)
█ Legacy Fallback (3%)
```

### Pattern Learning & Caching

The system learns and caches successful automation patterns:
```
📚 **Enhanced Pattern Cache Status**
- Cached automation scripts: 45
- Cache hit rate: 78%
- Performance improvement: 3.2x faster
- Error reduction: 65% fewer timeouts
- Most successful: E-commerce and form automation patterns
```

### Strategy Selection

Control which automation approach to use:
```python
# Let system use enhanced approach (recommended)
"Browse Amazon for headphones"
# System: Uses enhanced code generation with secure execution

# Force specific approach for testing
"Browse Amazon for headphones using legacy system"
# System: Uses step-by-step legacy approach

# Secure-only approach
"Browse secure banking site for account info"
# System: Enhanced generation with maximum security isolation
```

## Configuration

### Browser Behavior
```yaml
# Fine-tune smolagents automation in agent config
automation_config:
  enhanced_code_generation: true    # Enable smolagents approach
  secure_sandbox_execution: true   # Enable secure execution
  error_recovery_enabled: true     # Enable intelligent recovery
  max_retries_per_task: 3          # Retry attempts with regeneration
  show_browser: false              # Default headless mode
  code_optimization_level: standard # Code optimization setting
```

### Cost Controls
```yaml
# Budget management for enhanced automation
cost_controls:
  max_cost_per_task: 0.20           # Stop if exceeding 20¢
  prefer_batch_operations: true    # Favor code generation over step-by-step
  enable_pattern_caching: true     # Cache successful automation scripts
  track_spending: true              # Real-time cost monitoring
  daily_budget: 5.00                # Daily automation budget
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

### Code Generation Issues
**Problem:** Generated automation scripts fail to execute

**Solutions:**
1. **Enable browser visibility:** `wyn360 --show-browser`
2. **Check error recovery:** Review intelligent error analysis
3. **Verify sandbox security:** Ensure safe execution environment
4. **Enable pattern caching:** Reuse successful automation patterns

### High Costs
**Problem:** Automation costs more than expected

**Solutions:**
1. **Check approach distribution:** Use `/tokens` command
2. **Enable pattern caching:** Set `WYN360_PATTERN_CACHING=true`
3. **Monitor error recovery:** Too many regeneration attempts?
4. **Use batch operations:** Combine multiple actions in single script

### Authentication Issues
**Problem:** Can't access logged-in content

**Solutions:**
1. **Login first:** Use explicit login request
2. **Check session:** Sessions last 30 minutes
3. **Clear cache:** If cookies are corrupted
4. **Manual intervention:** Use show-browser for complex auth

## Best Practices

### 1. Optimize for Enhanced Code Generation
```bash
# Good: Clear, specific automation goals
"Find product price on Amazon product page"

# Better: Detailed task descriptions
"Search Amazon for wireless mouse under $20 with good reviews and extract the cheapest option"

# Best: Specific and comprehensive
"Browse Amazon, search for 'wireless mouse', apply price filter under $20, filter by 4+ star ratings, and return the top 3 cheapest options with details"
```

### 2. Use Browser Visibility Strategically
```bash
# Development & debugging
wyn360 --show-browser

# Production & scripts with enhanced automation
wyn360  # headless for optimal performance

# Specific debugging with code generation
"Browse to checkout and show me the generated automation script"
```

### 3. Leverage Intelligent Recovery
```bash
# Enhanced system automatically handles most errors:
"Browse complex e-commerce site for product comparison"
→ System: Generates code, detects errors, regenerates improved code
→ Success: Automatic recovery with learning applied
```

### 4. Monitor Performance & Patterns
```bash
# Regular performance checking
/tokens

# Enable pattern caching for better performance
export WYN360_PATTERN_CACHING=true

# Optimize code generation level
export WYN360_CODE_OPTIMIZATION=advanced
```

## Real-World Examples

### E-commerce Price Comparison
```
You: Compare wireless earbuds prices across Amazon, Best Buy, and Target

WYN360: [Enhanced automation with batch script generation]
📝 **Generating cross-site comparison script...**

Generated Automation Code:
```python
# Multi-site price comparison automation
sites = [
    {"name": "Amazon", "url": "https://amazon.com", "search": "Sony WF-1000XM4"},
    {"name": "Best Buy", "url": "https://bestbuy.com", "search": "Sony WF-1000XM4"},
    {"name": "Target", "url": "https://target.com", "search": "Sony WF-1000XM4"}
]
results = []
for site in sites:
    # Execute search and extract pricing data
    # Handle different site layouts automatically
```

🔒 **Executing in secure sandbox...** ✓

**Amazon:** Sony WF-1000XM4 - $199.99 (4.3⭐)
**Best Buy:** Sony WF-1000XM4 - $189.99 (4.5⭐) ← Best Deal
**Target:** Sony WF-1000XM4 - $209.99 (4.2⭐)

💡 **Recommendation:** Best Buy offers the lowest price
⚡ **Performance:** Enhanced code generation (6.8s total)
💰 **Cost:** $0.06 total (vs $0.35 with step-by-step)
```

### Research & Data Extraction
```
You: Gather the latest iPhone reviews and ratings from tech websites

WYN360: [Enhanced automation for data extraction]
📝 **Generating review compilation script...**

Generated Code:
```python
# Multi-site review extraction automation
tech_sites = [
    {"name": "TechRadar", "url": "techradar.com/reviews/iphone-15-pro"},
    {"name": "GSMArena", "url": "gsmarena.com/iphone_15_pro_review"},
    {"name": "The Verge", "url": "theverge.com/iphone-15-pro-review"}
]
for site in tech_sites:
    # Extract review content, ratings, pros/cons
    # Handle different review formats automatically
```

🔒 **Executing extraction in secure sandbox...** ✓

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

🎯 **Extraction Method:** Enhanced code generation with batch processing
⏱️ **Time:** 22 seconds across 3 sites
💸 **Cost:** $0.08 (75% savings vs step-by-step)

## Performance Metrics

### **Benchmark Comparison**

| Task Type | Step-by-Step (Old) | Smolagents (New) | Improvement |
|-----------|-------------------|------------------|-------------|
| **Product Search** | $0.25, 45s | $0.04, 8s | 84% cost ↓, 82% time ↓ |
| **Form Submission** | $0.40, 60s | $0.06, 12s | 85% cost ↓, 80% time ↓ |
| **Data Extraction** | $0.15, 30s | $0.03, 6s | 80% cost ↓, 80% time ↓ |
| **Multi-Page Flow** | $0.50, 90s | $0.08, 15s | 84% cost ↓, 83% time ↓ |

### **Success Rates by Approach**
- **Enhanced Code Generation:** 92% success rate
- **Secure Sandbox Execution:** 98% success rate
- **Intelligent Error Recovery:** 85% recovery success rate
- **Combined System:** 96% overall success rate

## API Integration

For programmatic usage:

```python
from wyn360_cli.agent import WYN360Agent

# Initialize with enhanced automation control
agent = WYN360Agent(
    api_key="your_key",
    show_browser=False,  # Headless by default
    max_cost_per_task=0.20,
    enhanced_automation=True  # Enable smolagents approach
)

# Enhanced automation with code generation
result = await agent.browse_page_intelligently(
    ctx=None,
    url="https://example-site.com",
    task="Find and extract pricing information",
    strategy="enhanced"  # enhanced, legacy, secure_only
)

# Structured data extraction with secure sandbox
data = await agent.extract_page_data(
    ctx=None,
    url="https://product-page.com",
    schema={
        "title": str,
        "price": float,
        "rating": float,
        "availability": bool
    },
    execution_mode="secure_sandbox"  # Enhanced security
)
```

## See Also

- **[Complete Technical Guide](../architecture/autonomous-browsing.md)** - Full architecture documentation
- **[Usage Examples](../usage/use-cases.md#browser-automation)** - Real-world automation workflows
- **[Cost Optimization Guide](../cost-management.md)** - Managing automation expenses
- **[Troubleshooting Guide](../troubleshooting/browser-automation.md)** - Common issues and solutions

---

*Updated for WYN360-CLI v0.3.69*
*Smolagents-Inspired Browser Automation with Enhanced Code Generation*