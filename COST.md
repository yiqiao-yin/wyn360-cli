# WYN360 CLI - Cost Analysis & Estimation

This document provides a detailed breakdown of the costs associated with using WYN360 CLI, which is powered by Anthropic Claude.

## 💰 Pricing (Anthropic Claude Sonnet 4)

As of January 2025, the default model `claude-sonnet-4-20250514` pricing:

### Token Costs

| Token Type | Cost per Million Tokens |
|------------|------------------------|
| **Input Tokens** | $3.00 |
| **Output Tokens** | $15.00 |

### Web Search Costs (Phase 11.1 - v0.3.21)

| Feature | Cost |
|---------|------|
| **Web Search** | $10.00 per 1,000 searches |
| **Session Limit** | 5 searches (default, configurable) |
| **Per Search** | $0.01 |

**Important:** Web search costs are **in addition to** token costs. Each search incurs:
- Fixed search cost: $0.01
- Token costs for processing results: ~$0.001-0.015 (varies by result size)
- Total per search: ~$0.011-0.025

**Formula:**
```
Total Cost = (Input Tokens / 1,000,000 × $3)
           + (Output Tokens / 1,000,000 × $15)
           + (Web Searches × $0.01)
           + (Search Result Token Processing)
```

## 📊 Token Breakdown Per Request

Every interaction with WYN360 CLI consists of several components that contribute to token usage:

### 1. System Prompt (~1,000 tokens)

The system prompt is sent with **every request** and includes:
- Role description and capabilities (~100 tokens)
- File operation intelligence guidelines (~200 tokens)
- Command execution guidelines (~150 tokens)
- HuggingFace integration guidelines (~100 tokens)
- Test generation guidelines (~100 tokens)
- **Web search guidelines (~100 tokens)** - NEW in v0.3.21
- Best practices and examples (~250 tokens)

**Cost per request:** ~$0.003 (input only)

### 2. Tool Definitions (~1,800 tokens)

All 20 tools are registered with the agent and their schemas are sent with each request (19 custom + 1 builtin):

**Core Tools (Phase 1):**
- `read_file` - Read file contents (~100 tokens)
- `write_file` - Create/update files (~120 tokens)
- `list_files` - Scan directory (~80 tokens)
- `get_project_info` - Project summary (~100 tokens)
- `execute_command` - Run shell commands (~200 tokens)

**Extended Tools (Phase 2 - Added in v0.2.9):**
- `git_status` - Show git status (~80 tokens)
- `git_diff` - Show git changes (~80 tokens)
- `git_log` - Show commit history (~80 tokens)
- `git_branch` - List branches (~80 tokens)
- `search_files` - Pattern search across files (~100 tokens)
- `delete_file` - Delete files safely (~80 tokens)
- `move_file` - Move/rename files (~80 tokens)
- `create_directory` - Create nested directories (~80 tokens)

**HuggingFace Tools (Phase 6/7 - Added in v0.3.16-v0.3.17):**
- `check_hf_authentication` - Check HF auth status (~80 tokens)
- `authenticate_hf` - Authenticate with HF (~80 tokens)
- `create_hf_readme` - Create Space README (~100 tokens)
- `create_hf_space` - Create new HF Space (~100 tokens)
- `push_to_hf_space` - Push files to Space (~100 tokens)

**Test Generation Tool (Phase 7.2 - Added in v0.3.18):**
- `generate_tests` - Auto-generate pytest test stubs (~100 tokens)

**Web Search Builtin Tool (Phase 11.1 - Added in v0.3.21):**
- `web_search` - Real-time internet search (~60 tokens for definition)
  - **Note:** This is a builtin tool, not a custom @tool function
  - Invoked automatically by Claude when current information is needed
  - Additional cost: $0.01 per search (5 searches max per session)

**Cost per request:** ~$0.0054 (input only, excluding web search usage costs)

### 3. User Message (~50-500 tokens)

Varies based on complexity:
- Simple: "Create a hello world script" (~10 tokens)
- Medium: "Add authentication to my FastAPI app" (~15 tokens)
- Complex: Multi-line detailed requirements (~200-500 tokens)

**Average cost:** ~$0.00015 - $0.0015 (input)

### 4. Conversation History (NEW in v0.2.8) (Variable)

Starting with v0.2.8, conversation history is maintained across interactions to provide better context:

**How it works:**
- Every user message and assistant response is stored
- The entire conversation history is sent with each subsequent request
- This allows the agent to maintain context across multiple turns
- History accumulates throughout the session

**Token Impact:**
- **Turn 1:** 0 tokens (no history yet)
- **Turn 2:** ~50-800 tokens (previous turn)
- **Turn 3:** ~100-1,600 tokens (2 previous turns)
- **Turn 10:** ~450-8,000 tokens (9 previous turns)

**Cost implications:**
```
Without history (v0.2.7 and earlier):
  Each request: ~1,500 tokens baseline (5 tools)

With history + all tools (v0.3.21):
  Turn 1:  ~2,850 tokens baseline (20 tools, web search capable)
  Turn 5:  ~5,350-7,850 tokens (includes 4 previous turns)
  Turn 10: ~9,350-13,850 tokens (includes 9 previous turns)

Note: Add $0.01-0.025 per web search if used
```

**Average conversation history cost per turn:**
- Turns 1-3: +$0.001 - $0.005
- Turns 4-7: +$0.005 - $0.015
- Turns 8-15: +$0.015 - $0.040
- Turns 16+: +$0.040 - $0.100

**Managing history costs:**
- Use `/clear` to reset conversation history when starting a new task
- Use `/save` before `/clear` to preserve important conversations
- Use `/tokens` to monitor cumulative costs during long sessions
- Balance context quality (better with history) vs cost (increases per turn)

### 5. Tool Call Execution (Variable)

When the agent calls tools, additional tokens are used:

#### Tool Call Request (~50-100 tokens per call)
```json
{
  "tool": "read_file",
  "parameters": {"file_path": "app.py"}
}
```

#### Tool Response (Highly Variable)

| Tool | Typical Response Size | Token Estimate |
|------|----------------------|----------------|
| `read_file` | File contents | 100-5,000+ tokens |
| `write_file` | Success message | 20-50 tokens |
| `list_files` | File list | 50-500 tokens |
| `get_project_info` | Project summary | 100-1,000 tokens |
| `execute_command` | Command output | 50-2,000+ tokens |

**Average tool execution:** ~$0.003 - $0.015 per tool call

### 6. Assistant Response (~200-1,500 tokens)

The final response varies by complexity:
- Simple confirmation: ~50 tokens
- Code generation: ~500-1,500 tokens
- Explanation + code: ~800-2,000 tokens

**Average cost:** ~$0.003 - $0.03 (output)

## 📈 Cost Estimates for Common Use Cases

### Use Case 1: Simple Code Generation (Blank Project)

**Scenario:** "Create a Streamlit hello world app"

**Token Breakdown:**
```
System Prompt:        850 tokens (input)
Tool Definitions:     600 tokens (input)
User Message:          15 tokens (input)
Tool Calls:             0 (no file reading needed)
Assistant Response:   800 tokens (output, includes code)
---------------------------------------------------
Total Input:        1,465 tokens
Total Output:         800 tokens
```

**Cost Calculation:**
```
Input:  1,465 / 1,000,000 × $3  = $0.004395
Output:   800 / 1,000,000 × $15 = $0.012000
---------------------------------------------------
Total Cost: $0.016395 (~$0.016 per request)
```

**Monthly estimate (50 requests):** ~$0.82

---

### Use Case 2: Update Existing File

**Scenario:** "Add logging to my script.py"

**Token Breakdown:**
```
System Prompt:        850 tokens (input)
Tool Definitions:     600 tokens (input)
User Message:          20 tokens (input)
---------------------------------------------------
Tool Call 1 - read_file:
  Request:             50 tokens (input)
  Response:         1,200 tokens (input, file contents)
---------------------------------------------------
Tool Call 2 - write_file:
  Request:            100 tokens (input)
  Response:            30 tokens (input, success message)
---------------------------------------------------
Assistant Response:   600 tokens (output, explanation)
---------------------------------------------------
Total Input:        3,450 tokens
Total Output:         600 tokens
```

**Cost Calculation:**
```
Input:  3,450 / 1,000,000 × $3  = $0.01035
Output:   600 / 1,000,000 × $15 = $0.00900
---------------------------------------------------
Total Cost: $0.01935 (~$0.019 per request)
```

**Monthly estimate (30 updates):** ~$0.58

---

### Use Case 3: Execute Python Script

**Scenario:** "Run my analysis.py script"

**Token Breakdown:**
```
System Prompt:        850 tokens (input)
Tool Definitions:     600 tokens (input)
User Message:          12 tokens (input)
---------------------------------------------------
Tool Call - execute_command:
  Request:             80 tokens (input)
  Response:         1,500 tokens (input, command output)
---------------------------------------------------
Assistant Response:   400 tokens (output, summary)
---------------------------------------------------
Total Input:        3,042 tokens
Total Output:         400 tokens
```

**Cost Calculation:**
```
Input:  3,042 / 1,000,000 × $3  = $0.009126
Output:   400 / 1,000,000 × $15 = $0.006000
---------------------------------------------------
Total Cost: $0.015126 (~$0.015 per request)
```

**Monthly estimate (20 executions):** ~$0.30

---

### Use Case 4: Complex Project Analysis

**Scenario:** "Analyze my codebase and suggest improvements"

**Token Breakdown:**
```
System Prompt:        850 tokens (input)
Tool Definitions:     600 tokens (input)
User Message:          25 tokens (input)
---------------------------------------------------
Tool Call 1 - get_project_info:
  Request:             60 tokens (input)
  Response:           800 tokens (input, project summary)
---------------------------------------------------
Tool Call 2 - list_files:
  Request:             50 tokens (input)
  Response:           300 tokens (input, file list)
---------------------------------------------------
Tool Call 3 - read_file (main.py):
  Request:             50 tokens (input)
  Response:         2,500 tokens (input, file contents)
---------------------------------------------------
Tool Call 4 - read_file (config.py):
  Request:             50 tokens (input)
  Response:         1,000 tokens (input, file contents)
---------------------------------------------------
Assistant Response: 1,800 tokens (output, detailed analysis)
---------------------------------------------------
Total Input:        6,285 tokens
Total Output:       1,800 tokens
```

**Cost Calculation:**
```
Input:  6,285 / 1,000,000 × $3  = $0.018855
Output: 1,800 / 1,000,000 × $15 = $0.027000
---------------------------------------------------
Total Cost: $0.045855 (~$0.046 per request)
```

**Monthly estimate (10 analyses):** ~$0.46

---

### Use Case 5: UV Project Setup

**Scenario:** "Initialize UV project and add dependencies"

**Token Breakdown:**
```
System Prompt:        850 tokens (input)
Tool Definitions:     600 tokens (input)
User Message:          30 tokens (input)
---------------------------------------------------
Tool Call 1 - execute_command (uv init):
  Request:             80 tokens (input)
  Response:           400 tokens (input, init output)
---------------------------------------------------
Tool Call 2 - execute_command (uv add):
  Request:             90 tokens (input)
  Response:           600 tokens (input, package install output)
---------------------------------------------------
Assistant Response:   700 tokens (output, setup guide)
---------------------------------------------------
Total Input:        3,350 tokens
Total Output:         700 tokens
```

**Cost Calculation:**
```
Input:  3,350 / 1,000,000 × $3  = $0.01005
Output:   700 / 1,000,000 × $15 = $0.01050
---------------------------------------------------
Total Cost: $0.02055 (~$0.021 per request)
```

**Monthly estimate (5 setups):** ~$0.11

---

### Use Case 6: Web Search - Weather Query (NEW in v0.3.21)

**Scenario:** "What's the weather in San Francisco?"

**Token Breakdown:**
```
System Prompt:      1,000 tokens (input, includes web search guidelines)
Tool Definitions:   1,800 tokens (input, 20 tools)
User Message:          15 tokens (input)
---------------------------------------------------
Web Search Call:
  Request:             50 tokens (input)
  Search Cost:         $0.01 (flat fee per search)
  Response:           300 tokens (input, weather data from web)
---------------------------------------------------
Assistant Response:   250 tokens (output, formatted weather info)
---------------------------------------------------
Total Input:        3,165 tokens
Total Output:         250 tokens
Web Search:         1 search
```

**Cost Calculation:**
```
Input:  3,165 / 1,000,000 × $3  = $0.009495
Output:   250 / 1,000,000 × $15 = $0.003750
Web Search: 1 × $0.01          = $0.010000
---------------------------------------------------
Total Cost: $0.023245 (~$0.023 per weather query)
```

**Monthly estimate (20 weather queries):** ~$0.46

**Note:** Session limit of 5 searches prevents excessive costs. Start new session if limit reached.

---

### Use Case 7: Web Search - URL Reading (NEW in v0.3.21)

**Scenario:** "Read this article: https://python.org/downloads/release/python-3130/"

**Token Breakdown:**
```
System Prompt:      1,000 tokens (input)
Tool Definitions:   1,800 tokens (input)
User Message:          20 tokens (input)
---------------------------------------------------
Web Search Call:
  Request:             60 tokens (input)
  Search Cost:         $0.01 (flat fee per search)
  Response:         1,200 tokens (input, article content)
---------------------------------------------------
Assistant Response:   800 tokens (output, summary and analysis)
---------------------------------------------------
Total Input:        4,080 tokens
Total Output:         800 tokens
Web Search:         1 search
```

**Cost Calculation:**
```
Input:  4,080 / 1,000,000 × $3  = $0.012240
Output:   800 / 1,000,000 × $15 = $0.012000
Web Search: 1 × $0.01          = $0.010000
---------------------------------------------------
Total Cost: $0.034240 (~$0.034 per URL read)
```

**Monthly estimate (10 URL reads):** ~$0.34

---

### Use Case 8: Web Search - Latest Information (NEW in v0.3.21)

**Scenario:** "What's new in Python 3.13?"

**Token Breakdown:**
```
System Prompt:      1,000 tokens (input)
Tool Definitions:   1,800 tokens (input)
User Message:          15 tokens (input)
---------------------------------------------------
Web Search Call 1 (main query):
  Request:             50 tokens (input)
  Search Cost:         $0.01 (flat fee)
  Response:           800 tokens (input, search results)
---------------------------------------------------
Web Search Call 2 (follow-up for details):
  Request:             50 tokens (input)
  Search Cost:         $0.01 (flat fee)
  Response:           600 tokens (input, additional details)
---------------------------------------------------
Assistant Response: 1,200 tokens (output, comprehensive summary)
---------------------------------------------------
Total Input:        4,315 tokens
Total Output:       1,200 tokens
Web Searches:       2 searches
```

**Cost Calculation:**
```
Input:  4,315 / 1,000,000 × $3  = $0.012945
Output: 1,200 / 1,000,000 × $15 = $0.018000
Web Searches: 2 × $0.01        = $0.020000
---------------------------------------------------
Total Cost: $0.050945 (~$0.051 per info query)
```

**Monthly estimate (8 info queries):** ~$0.41

**Note:** Complex queries may use 1-2 searches. Simple queries typically use 1 search.

---

## 💡 Monthly Cost Estimates by Usage Pattern

### Light User (10-20 requests/month)
**Profile:** Occasional quick scripts, simple code generation

**Estimated monthly cost:** $0.20 - $0.40

**Breakdown:**
- 10 simple code generations: ~$0.16
- 5 file updates: ~$0.10
- 5 command executions: ~$0.08

---

### Regular User (50-100 requests/month)
**Profile:** Daily coding tasks, project maintenance

**Estimated monthly cost:** $1.00 - $2.50

**Breakdown:**
- 30 code generations: ~$0.50
- 40 file updates: ~$0.80
- 20 command executions: ~$0.30
- 10 project analyses: ~$0.46

---

### Heavy User (200-500 requests/month)
**Profile:** Primary coding assistant, extensive project work

**Estimated monthly cost:** $5.00 - $15.00

**Breakdown:**
- 100 code generations: ~$1.60
- 150 file updates: ~$2.90
- 100 command executions: ~$1.50
- 50 project analyses: ~$2.30
- Complex multi-tool sessions: ~$5.00+

---

### Team/Enterprise (1000+ requests/month)
**Profile:** Multiple developers, CI/CD integration

**Estimated monthly cost:** $30.00 - $100.00+

**Considerations:**
- Shared API key across team
- Automated workflows
- Larger codebases (more tokens per file)
- More complex operations

---

## 🎯 Cost Optimization Strategies

### 1. **Minimize File Reads**

**Problem:** Reading large files adds significant input tokens.

**Solution:**
```python
# Instead of: "Read all my files and analyze them"
# Try: "Analyze app.py only"
```

**Savings:** Can reduce cost by 50-80% for large codebases

---

### 2. **Use Specific Requests**

**Problem:** Vague requests trigger multiple tool calls.

**Before:**
```
"Improve my project"
→ Triggers: list_files, read_file (×5), get_project_info
→ Cost: ~$0.06
```

**After:**
```
"Add error handling to app.py line 45"
→ Triggers: read_file (×1), write_file (×1)
→ Cost: ~$0.02
```

**Savings:** ~66% cost reduction

---

### 3. **Batch Related Operations**

**Problem:** Multiple separate sessions repeat system prompt/tool definitions.

**Instead of:**
```
Session 1: "Create app.py"         → $0.016
Session 2: "Create utils.py"       → $0.016
Session 3: "Create config.py"      → $0.016
Total: $0.048
```

**Use:**
```
Session 1: "Create app.py, utils.py, and config.py"
Total: ~$0.025
```

**Savings:** ~48% cost reduction

---

### 4. **Limit Command Output**

**Problem:** Verbose command output increases tokens.

**Strategy:**
- Use command flags to limit output: `ls -1` instead of `ls -la`
- Filter output in commands: `pytest -q` instead of `pytest -v`
- Redirect stderr when not needed

**Savings:** 20-40% on command execution costs

---

### 5. **Clear Conversation History Periodically**

**Problem:** Long conversation history increases context tokens (if implemented).

**Current:** WYN360 stores history in memory but doesn't send full history yet.

**Future consideration:** If conversation history is sent with each request, periodically restart CLI to clear history.

---

### 6. **Use Smaller Model for Simple Tasks**

**Current:** Uses `claude-sonnet-4-20250514` by default

**Alternative:** Could add option for Claude Haiku for simple tasks:
- Haiku pricing: ~$0.25 per million input tokens (88% cheaper)
- Good for: Simple file operations, quick questions

**Command:**
```bash
wyn360 --model claude-haiku-3-5-20250304
```

**Potential savings:** 80-90% for simple operations

---

## 📊 Token Usage Tracking

### Method 1: Check Anthropic Console

1. Visit: https://console.anthropic.com/
2. Navigate to "Usage" tab
3. View token usage by day/month
4. Calculate costs using pricing table

### Method 2: API Response Headers (Future Enhancement)

Could add token tracking to WYN360:

```python
# Potential feature
result = await agent.chat(user_input)
print(f"Tokens used - Input: {result.input_tokens}, Output: {result.output_tokens}")
print(f"Estimated cost: ${result.cost:.4f}")
```

### Method 3: Estimate from Response Length

**Rough estimation:**
- 1 token ≈ 4 characters for English text
- 1 token ≈ 0.75 words on average

**Example:**
```python
response_length = len(response_text)
estimated_output_tokens = response_length / 4
estimated_cost = estimated_output_tokens / 1_000_000 * 15
```

---

## 🔍 Real-World Cost Examples

### Example 1: Building a Streamlit App (Full Session)

**Session transcript:**
```
1. "Create a Streamlit data visualization app"      → $0.016
2. "Add file upload functionality"                   → $0.019
3. "Add CSV parsing with pandas"                     → $0.018
4. "Add bar chart visualization"                     → $0.020
5. "Run the app with streamlit run app.py"          → $0.015
-----------------------------------------------------------
Total session cost: $0.088
```

**Result:** Complete working app for less than 9 cents

---

### Example 2: Debugging Session (10 interactions)

**Session transcript:**
```
1. "Read my script.py and find the error"           → $0.022
2. "The error is on line 45, fix it"                → $0.019
3. "Run the script to test"                          → $0.015
4. "Still getting error, read the full traceback"   → $0.018
5. "Add try-except error handling"                   → $0.021
6. "Run it again"                                     → $0.015
7. "Add logging to debug the issue"                  → $0.019
8. "Test with sample input"                          → $0.017
9. "Perfect! Add unit tests"                         → $0.023
10. "Run the tests"                                   → $0.016
-----------------------------------------------------------
Total session cost: $0.185
```

**Result:** Debugged and tested code for ~19 cents

---

### Example 3: Monthly Developer Usage

**Typical month (60 sessions):**
```
Code generation:        30 sessions × $0.016 = $0.48
File updates:           20 sessions × $0.019 = $0.38
Command execution:      15 sessions × $0.015 = $0.23
Project analysis:        5 sessions × $0.046 = $0.23
-----------------------------------------------------------
Total monthly cost: $1.32
```

**Comparison:**
- GitHub Copilot: $10/month (fixed)
- WYN360 CLI: ~$1.32/month (usage-based)
- **Savings:** ~$8.68/month (87% cheaper for typical usage)

---

## ⚠️ Cost Considerations

### What Increases Costs:

1. **Large File Operations**
   - Reading files >5,000 lines: +$0.01-0.05 per file
   - Reading multiple files: Multiplies costs

2. **Verbose Command Output**
   - Long-running scripts with extensive output
   - Unfiltered logs and stack traces

3. **Complex Multi-Step Operations**
   - Multiple tool calls per request
   - Iterative refinement (trial and error)

4. **Conversation Length**
   - Future: If full conversation history is sent
   - Currently: Minimal impact (history not sent to API)

### What Keeps Costs Low:

1. **Focused Requests**
   - Specific file operations
   - Clear, concise instructions

2. **Small Files**
   - Scripts under 500 lines
   - Targeted changes

3. **Single-Shot Operations**
   - Complete requirements in one message
   - Avoid back-and-forth clarifications

---

## 💰 Cost Comparison with Alternatives

| Tool | Pricing Model | Typical Monthly Cost |
|------|---------------|---------------------|
| **WYN360 CLI** | Pay-per-use | $1-5 for regular users |
| **GitHub Copilot** | Fixed subscription | $10/month |
| **Cursor IDE** | Fixed subscription | $20/month |
| **ChatGPT Plus** | Fixed subscription | $20/month |
| **Direct API Usage** | Pay-per-use | $5-50+ (depending on usage) |

**WYN360 Advantages:**
- ✅ Only pay for what you use
- ✅ No monthly commitment
- ✅ Transparent token usage
- ✅ Can be very cost-effective for light users
- ✅ Full control over model selection

**When WYN360 Might Cost More:**
- Heavy daily usage (200+ sessions/day)
- Very large codebases (constant file reading)
- Compared to flat-rate tools if you use heavily

---

## 📝 Summary

### Key Takeaways:

1. **Average cost per request:** $0.015 - $0.025
2. **Typical monthly cost:** $1 - $5 for regular developers
3. **Most expensive operation:** Reading large files
4. **Most economical:** Simple code generation
5. **Optimization:** Use specific requests, batch operations

### Cost Formula:

```
Per Request Cost ≈ Base ($0.0045) + Tool Calls ($0.003-0.015 each) + Response ($0.003-0.03)
```

### Recommendation:

For **most developers**, WYN360 CLI will cost **$1-3 per month** - significantly less than subscription-based alternatives while providing similar capabilities.

---

## 🔗 Additional Resources

- **Anthropic Pricing:** https://www.anthropic.com/pricing
- **Usage Console:** https://console.anthropic.com/
- **WYN360 Documentation:** [USE_CASES.md](USE_CASES.md)
- **Token Counting:** https://platform.openai.com/tokenizer (similar to Claude)

---

**Last Updated:** January 2025
**Version:** 0.3.21
