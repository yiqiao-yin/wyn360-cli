# Autonomous Vision-Based Browsing

> **Phase 5: Complete Implementation** (v0.3.52 - v0.3.56)

WYN360-CLI now features autonomous browsing powered by Claude Vision API. The agent can navigate websites, interact with elements, and extract information by "seeing" and understanding web pages just like a human would.

## Overview

Autonomous browsing enables Claude to:
- **See** web pages through screenshots
- **Understand** page content using Claude Vision
- **Decide** which actions to take (click, type, scroll, etc.)
- **Execute** browser actions automatically
- **Extract** structured data from websites

This creates a fully autonomous agent that can complete multi-step web tasks without manual intervention.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Autonomous Browsing Loop                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────┐
        │   1. Take Screenshot (PNG, 1024x768) │
        └──────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────┐
        │  2. Analyze with Claude Vision API   │
        │     - What do I see?                 │
        │     - What should I do next?         │
        │     - Am I done?                     │
        └──────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────┐
        │   3. Parse Decision (JSON)           │
        │     {status, action, confidence}     │
        └──────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────┐
        │   4. Execute Action (Playwright)     │
        │     - click, type, scroll, extract   │
        └──────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────┐
        │   5. Check Completion                │
        │     - Complete? → Return result      │
        │     - Continue? → Take screenshot    │
        │     - Stuck? → Handle error          │
        └──────────────────────────────────────┘
```

## Components

### 1. BrowserController
Pure browser automation using Playwright. Handles:
- Browser lifecycle (launch, navigate, cleanup)
- Actions (click, type, scroll, navigate, extract, wait)
- Screenshot capture (optimized for vision)
- Error handling and retries (Phase 5.4)

**File:** `wyn360_cli/browser_controller.py`

### 2. VisionDecisionEngine
AI-powered decision making using Claude Vision. Handles:
- Screenshot analysis
- Action decisions
- Confidence scoring
- Stuck detection

**File:** `wyn360_cli/vision_engine.py`

### 3. BrowserTaskExecutor
Orchestration layer. Handles:
- Main execution loop
- Task state management
- Progress tracking
- Success/failure detection

**File:** `wyn360_cli/browser_task_executor.py`

### 4. Agent Integration
User-facing tool integrated into WYN360Agent:
- `browse_and_find()` tool
- Result formatting
- Tool chaining support

**File:** `wyn360_cli/agent.py`

## Usage

### Basic Usage

```python
# Using the CLI (recommended)
wyn360

# Then ask the agent:
"Browse to Amazon and find the cheapest sneaker with 2-day shipping"
```

The agent will automatically use the `browse_and_find` tool to:
1. Navigate to amazon.com
2. Search for sneakers
3. Apply 2-day shipping filter
4. Compare prices
5. Extract the cheapest option

### Programmatic Usage

```python
from wyn360_cli.agent import WYN360Agent

agent = WYN360Agent(api_key="your_api_key")

# Execute autonomous browsing task
result = await agent.browse_and_find(
    ctx=None,
    task="Find the cheapest sneaker with 2-day shipping",
    url="https://amazon.com",
    max_steps=20,  # Maximum actions to attempt
    headless=False  # Visible browser (watch the agent work)
)

print(result)  # Formatted result with extracted data
```

## Examples

### Example 1: Structured Shopping Task

**Task:** Find a specific product with criteria

```python
result = await agent.browse_and_find(
    task="Find the cheapest wireless mouse under $20 with good reviews",
    url="https://amazon.com"
)
```

**What the agent does:**
1. Navigates to Amazon
2. Searches for "wireless mouse"
3. Applies price filter (<$20)
4. Sorts by customer rating
5. Selects best match
6. Extracts: name, price, rating, link

**Expected result:**
```json
{
  "status": "success",
  "result": {
    "product": "Logitech M185 Wireless Mouse",
    "price": "$14.99",
    "rating": "4.5 stars",
    "reviews": "15,234",
    "link": "https://amazon.com/..."
  },
  "steps_taken": 8
}
```

### Example 2: Open-Ended Exploration

**Task:** Explore and analyze

```python
result = await agent.browse_and_find(
    task="Browse the electronics section and tell me what's trending",
    url="https://amazon.com",
    max_steps=30  # More steps for exploration
)
```

**What the agent does:**
1. Navigates to electronics
2. Checks "Best Sellers" or "Hot Deals"
3. Reads product names and descriptions
4. Identifies patterns/trends
5. Summarizes findings

**Expected result:**
```json
{
  "status": "success",
  "result": {
    "trending_categories": [
      "Smart Home Devices",
      "Wireless Earbuds",
      "Portable Chargers"
    ],
    "top_products": [
      "Echo Dot (5th Gen)",
      "Apple AirPods Pro",
      "Anker PowerCore"
    ],
    "insights": "Smart home devices are dominating..."
  },
  "steps_taken": 18
}
```

### Example 3: Authenticated Workflows

**Task:** Access content behind login

```python
# First, login
await agent.login_to_website(
    ctx=None,
    url="https://amazon.com/login",
    username="user@example.com",
    password="password123"
)

# Then use saved session for authenticated browsing
result = await agent.browse_and_find(
    task="Find the most expensive item in my wishlist",
    url="https://amazon.com/wishlist"
)
```

**What the agent does:**
1. Uses saved session cookies (from login_to_website)
2. Navigates to wishlist
3. Browses through items
4. Compares prices
5. Identifies most expensive item

### Example 4: Multi-Tool Workflow

**Task:** Chain web search with autonomous browsing

```python
# Agent automatically chains tools when needed

# You just ask:
"Search for the best online electronics stores, then browse the top result
and tell me their current deals"
```

**What the agent does:**
1. Uses WebSearchTool to find electronics stores
2. Extracts top URL from search results
3. Uses browse_and_find on that URL
4. Navigates to deals section
5. Extracts current promotions

## Best Practices

### 1. Start with Specific URLs
❌ **Bad:** `url="https://google.com"`
✅ **Good:** `url="https://amazon.com/electronics"`

Starting closer to your goal reduces steps and improves success rate.

### 2. Use Clear Task Descriptions
❌ **Bad:** "Find something good"
✅ **Good:** "Find the cheapest wireless keyboard under $30 with backlight"

Specific criteria help the vision model make better decisions.

### 3. Set Appropriate max_steps
- **Simple tasks** (search + extract): 10-15 steps
- **Medium tasks** (search, filter, sort, extract): 15-20 steps
- **Complex tasks** (multi-page, exploration): 20-30 steps

Too few steps = incomplete tasks. Too many = unnecessary API costs.

### 4. Handle Authentication First
```python
# Always login before browsing authenticated pages
await agent.login_to_website(url, username, password)
# Then browse
await agent.browse_and_find(task, authenticated_url)
```

Sessions persist for 30 minutes, so you can make multiple browse_and_find calls.

### 5. Use Visible Mode for Testing
```python
# Development/testing: watch the agent work
result = await agent.browse_and_find(task, url, headless=False)

# Production: run invisibly
result = await agent.browse_and_find(task, url, headless=True)
```

Visible mode helps you understand what the agent is doing and debug issues.

## Configuration

### Timeout Settings
Adjust in `BrowserConfig` (wyn360_cli/browser_controller.py):

```python
NAVIGATION_TIMEOUT = 60000  # 60s for page navigation
ACTION_TIMEOUT = 10000      # 10s for element interactions
DEFAULT_TIMEOUT = 30000     # 30s default
```

### Retry Settings
```python
MAX_RETRIES = 2             # Retry failed actions 2 times
RETRY_DELAY = 1.0           # Wait 1s between retries
```

### Performance Settings
```python
WAIT_AFTER_NAVIGATION = 1.0  # Wait 1s after navigation for JS
WAIT_AFTER_ACTION = 0.5      # Wait 0.5s after actions for updates
```

## Troubleshooting

### Task Not Completing

**Symptom:** Agent reaches max_steps without finishing

**Solutions:**
1. **Increase max_steps:** Some tasks require more actions
   ```python
   result = await agent.browse_and_find(task, url, max_steps=30)
   ```

2. **Simplify the task:** Break into smaller sub-tasks
   ```python
   # Instead of: "Find X, compare prices, and buy"
   # Do: "Find X and tell me the price"
   ```

3. **Check the URL:** Start closer to the target
   ```python
   # Instead of: https://amazon.com
   # Use: https://amazon.com/s?k=wireless+mouse
   ```

### Wrong Actions / Getting Stuck

**Symptom:** Agent clicks wrong elements or repeats actions

**Solutions:**
1. **Refine task description:** Be more specific
   ```python
   # Instead of: "Find a good mouse"
   # Use: "Find the cheapest wireless mouse with >4 stars"
   ```

2. **Check for popups:** Some sites have cookie banners that block content
   - The agent should auto-dismiss these (Phase 5.4 improvement)
   - If not, report as an issue

3. **Verify website accessibility:** Some sites block automation
   - Try the same task manually first
   - Check if CAPTCHA is present (agent will report stuck)

### Bedrock Mode Error

**Symptom:** `❌ Autonomous browsing requires vision capabilities`

**Solution:** Vision features require Anthropic API (not available in Bedrock)
```bash
# Enable Anthropic API mode
export ANTHROPIC_API_KEY=your_key_here
unset CLAUDE_CODE_USE_BEDROCK

# Then restart wyn360
wyn360
```

### CAPTCHA / Login Required

**Symptom:** Agent reports stuck immediately

**Cause:** Website requires human verification or authentication

**Solutions:**
1. For login: Use `login_to_website` first
2. For CAPTCHA: No automated solution (human verification required)
3. Alternative: Use APIs instead of web scraping

## Cost Considerations

### Vision API Costs

Claude Vision API charges based on:
- **Images:** ~1792 tokens per screenshot (1024x768 PNG)
- **Text:** Standard token rates for prompts/responses

**Rough Estimates (as of 2025):**
- Per screenshot: ~$0.01 - $0.02 (including prompt + response)
- Typical task (15 steps): ~$0.15 - $0.30
- Complex task (30 steps): ~$0.30 - $0.60

### Optimization Tips

1. **Reduce max_steps:** Lower limit = fewer screenshots
   ```python
   # Only use what you need
   max_steps=10  # Simple tasks
   max_steps=20  # Default
   max_steps=30  # Complex only
   ```

2. **Use targeted URLs:** Start closer to goal
3. **Batch similar tasks:** Reuse sessions, avoid re-navigation
4. **Cache when possible:** For repeated queries, cache results

### Cost Tracking

Check token usage in agent:
```python
print(f"Input tokens: {agent.total_input_tokens}")
print(f"Output tokens: {agent.total_output_tokens}")
print(f"Vision calls: {agent.vision_image_count}")
```

See `docs/COST.md` for detailed cost analysis.

## Limitations

### Current Limitations

1. **Vision-Only (Anthropic API):**
   - Not available in Bedrock mode
   - Requires ANTHROPIC_API_KEY

2. **Single-Page Focus:**
   - Works on one page at a time
   - No parallel browsing (yet - planned for Phase 5.6)

3. **No CAPTCHA Handling:**
   - Cannot solve CAPTCHAs automatically
   - Will detect and report stuck

4. **JavaScript-Heavy Sites:**
   - May struggle with SPAs that rely heavily on JS
   - Configurable wait times help (WAIT_AFTER_NAVIGATION)

5. **Rate Limiting:**
   - Some sites may block automated access
   - Use reasonable delays, respect robots.txt

### Future Improvements (Roadmap)

- **Phase 5.6:** Screenshot optimization, multi-page workflows
- **Phase 6:** Optional browser-use integration
- **Phase 7+:** Learning & improvement, cost optimization

## Examples Repository

See `USE_CASES.md` for more real-world examples:
- E-commerce price comparison
- Research and data gathering
- Competitive analysis
- Content monitoring

## API Reference

### browse_and_find()

```python
async def browse_and_find(
    ctx: RunContext[None],
    task: str,
    url: str,
    max_steps: int = 20,
    headless: bool = False
) -> str:
    """
    Autonomously browse a website to complete a multi-step task using vision.

    Args:
        task: Natural language description of what to accomplish
        url: Starting URL (e.g., "https://amazon.com")
        max_steps: Maximum browser actions to attempt (default: 20)
        headless: Run browser invisibly (default: False - visible)

    Returns:
        Formatted result string with:
        - Status (success/partial/failed)
        - Extracted data
        - Steps taken
        - Reasoning/summary

    Raises:
        VisionDecisionError: If vision analysis fails
        BrowserControllerError: If browser operation fails
    """
```

## Support & Contributing

- **Issues:** Report bugs at https://github.com/anthropics/claude-code/issues
- **Discussions:** Ask questions in GitHub Discussions
- **Contributing:** See CONTRIBUTING.md for guidelines

## License

Part of WYN360-CLI, licensed under the same terms.

---

*Generated with WYN360-CLI v0.3.56*
*Phase 5: Autonomous Vision-Based Browsing (Complete)*
