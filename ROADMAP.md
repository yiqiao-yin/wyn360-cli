# WYN360 CLI - Feature Roadmap & Expansion Ideas

This document outlines potential features and enhancements to expand WYN360 CLI's capabilities.

## 🎯 Current Capabilities (v0.3.5)

**What We Have:**
- ✅ File operations (read, write, list, get project info)
- ✅ Command execution with confirmation
- ✅ Code generation from natural language
- ✅ Intent recognition (create vs update)
- ✅ Multi-line input support
- ✅ Comprehensive error handling
- ✅ Tool calling with retry logic
- ✅ Conversation history and context management (Phase 1)
- ✅ Token tracking and cost monitoring (Phase 1)
- ✅ Session save/load functionality (Phase 1)
- ✅ Slash commands for context management (Phase 1)
- ✅ Git operations (status, diff, log, branch) (Phase 2)
- ✅ Code search across files (Phase 2)
- ✅ File management (delete, move, create dirs) (Phase 2)
- ✅ Dynamic model switching (haiku/sonnet/opus) (Phase 3)
- ✅ Model information display with pricing (Phase 3)
- ✅ /model command for mid-session model changes (Phase 3)
- ✅ User configuration file (~/.wyn360/config.yaml) (Phase 4)
- ✅ Project configuration file (.wyn360.yaml) (Phase 4)
- ✅ Custom instructions and project context (Phase 4)
- ✅ /config command to view settings (Phase 4)
- ✅ Streaming responses - token-by-token output (Phase 5)
- ✅ Real-time feedback and progress visibility (Phase 5)

---

## 🚀 Suggested Expansions

### Phase 1: Enhanced Context Management ✅ COMPLETED (v0.2.8)

#### 1.1 Conversation History in API Calls
**Current:** History stored locally but not sent to API
**Proposed:** Send conversation history to maintain context across turns

**Benefits:**
- Agent remembers previous interactions
- "Continue from where we left off" workflows
- Better follow-up question handling

**Implementation:**
```python
# In agent.py chat() method
messages = [{"role": "system", "content": system_prompt}]
messages.extend(self.conversation_history)
result = await self.agent.run(user_message, message_history=messages)
```

**Considerations:**
- Token usage increases significantly
- Need context window management (max tokens)
- Add option to disable for cost savings

**Priority:** HIGH - Most requested feature

---

#### 1.2 Context Management Commands
**Feature:** User control over conversation context

**Commands:**
```bash
/clear      # Clear conversation history
/history    # Show conversation history
/save       # Save session to file
/load       # Load previous session
/token      # Show token usage stats
```

**Implementation:**
- Add slash command parsing in CLI
- Store sessions as JSON
- Display token counts per message

**Priority:** MEDIUM

---

### Phase 2: Additional Tools ✅ COMPLETED (v0.2.9)

#### 2.1 Git Operations Tool
**Why:** Most developers use git constantly

**Tool Functions:**
```python
async def git_status(self, ctx: RunContext[None]) -> str:
    """Get current git status"""

async def git_diff(self, ctx: RunContext[None], file_path: str = None) -> str:
    """Show git diff for file or all changes"""

async def git_commit(self, ctx: RunContext[None], message: str) -> str:
    """Create git commit with message"""

async def git_branch(self, ctx: RunContext[None]) -> str:
    """List branches"""
```

**Use Cases:**
- "Show me what files changed"
- "Commit these changes with message 'Add feature X'"
- "What branch am I on?"

**Priority:** HIGH - Frequently needed

---

#### 2.2 Search/Grep Tool
**Why:** Find code patterns across files

**Tool Function:**
```python
async def search_files(
    self,
    ctx: RunContext[None],
    pattern: str,
    file_pattern: str = "*.py"
) -> str:
    """Search for pattern in files matching file_pattern"""
```

**Use Cases:**
- "Find all functions that use 'requests' library"
- "Where is the User class defined?"
- "Show me all TODO comments"

**Priority:** HIGH - Essential for large codebases

---

#### 2.3 File Management Tools
**Why:** Complete file system operations

**Tool Functions:**
```python
async def delete_file(self, ctx: RunContext[None], file_path: str) -> str:
    """Delete a file (with confirmation)"""

async def move_file(
    self,
    ctx: RunContext[None],
    source: str,
    destination: str
) -> str:
    """Move or rename file"""

async def create_directory(self, ctx: RunContext[None], dir_path: str) -> str:
    """Create directory structure"""
```

**Priority:** MEDIUM

---

### Phase 3: Model Selection & Optimization ✅ COMPLETED (v0.3.0)

#### 3.1 Dynamic Model Switching
**Feature:** Choose model based on task complexity

**Implementation:**
```python
# In CLI
wyn360 --model haiku      # Fast & cheap for simple tasks
wyn360 --model sonnet     # Default - balanced
wyn360 --model opus       # Most capable - expensive

# Or dynamic in-session
"Use Haiku for this simple task"
"Switch to Opus for complex refactoring"
```

**Cost Optimization:**
| Model | Input Cost | Output Cost | Best For |
|-------|-----------|-------------|----------|
| Haiku | $0.25/M | $1.25/M | Simple file ops, quick questions |
| Sonnet | $3.00/M | $15.00/M | General coding, analysis |
| Opus | $15.00/M | $75.00/M | Complex reasoning, architecture |

**Priority:** MEDIUM - Good for power users

---

#### 3.2 Automatic Model Selection
**Feature:** Agent chooses appropriate model for task

**Logic:**
```python
def suggest_model(task_description: str) -> str:
    if is_simple_task(task_description):
        return "haiku"  # "read file", "list files"
    elif is_complex_task(task_description):
        return "opus"   # "refactor architecture", "design system"
    else:
        return "sonnet"  # Default
```

**Priority:** LOW - Nice to have

---

### Phase 4: Configuration & Personalization ✅ COMPLETED (v0.3.1)

#### 4.1 Configuration File
**Feature:** Persistent user preferences

**File:** `~/.wyn360/config.yaml`
```yaml
# Default settings
model: claude-sonnet-4-20250514
max_tokens: 4096
temperature: 0.7

# Custom system prompt additions
custom_instructions: |
  - Always use type hints
  - Follow PEP 8 strictly
  - Add docstrings to all functions

# Shortcuts
aliases:
  test: "run pytest tests/ -v"
  lint: "run ruff check ."

# Favorite directories
workspaces:
  - ~/projects/app1
  - ~/projects/ml-research
```

**Priority:** MEDIUM - Improves UX for regular users

---

#### 4.2 Project-Specific Context
**Feature:** Auto-load project context

**File:** `.wyn360.yaml` in project root
```yaml
# Project-specific instructions
context: |
  This is a FastAPI project with:
  - PostgreSQL database
  - Redis caching
  - Celery for background tasks

# Project-specific tools
dependencies:
  - fastapi
  - sqlalchemy
  - celery

# Common commands
commands:
  dev: "uvicorn app.main:app --reload"
  test: "pytest tests/ -v --cov"
```

**Priority:** MEDIUM - Great for teams

---

### Phase 5: Streaming Responses ✅ COMPLETED (v0.3.2, bugfixes v0.3.3-0.3.4)

#### 5.1 Token-by-Token Streaming
**Why:** See responses as they generate (like ChatGPT)

**Current Experience:**
```
You: Generate a large script
[Spinner for 10 seconds]
WYN360: [Entire response appears at once]
```

**Proposed Experience:**
```
You: Generate a large script
WYN360: I'll create a comprehensive... [tokens appear as generated]
```

**Implementation:**
```python
# Use async streaming API
async for chunk in agent.run_stream(user_message):
    print(chunk, end='', flush=True)
```

**Benefits:**
- Feels faster (immediate feedback)
- Can cancel long responses
- Better UX for lengthy outputs

**Priority:** HIGH - Significant UX improvement

---

### Phase 6: Advanced Workflows (MEDIUM PRIORITY)

#### 6.1 Multi-File Refactoring
**Feature:** Refactor across multiple files in one operation

**Use Case:**
```
You: Rename the User class to Account across all files

WYN360:
Found User class in:
- models/user.py
- services/user_service.py
- api/user_routes.py

I'll refactor all 3 files:
1. Read all files
2. Update class name and imports
3. Write back with changes
```

**Priority:** MEDIUM - Powerful for large refactors

---

#### 6.2 Test Generation Mode
**Feature:** Automatically generate tests for code

**Use Case:**
```
You: Generate tests for calculator.py

WYN360:
Reading calculator.py...
Found functions: add(), subtract(), multiply(), divide()

Creating test_calculator.py with:
- test_add_positive_numbers
- test_add_negative_numbers
- test_divide_by_zero_raises_error
[... comprehensive test suite]
```

**Priority:** MEDIUM - High value for developers

---

#### 6.3 Documentation Generation
**Feature:** Auto-generate documentation

**Use Case:**
```
You: Generate API documentation for my FastAPI app

WYN360:
Analyzing routes...
Creating API_DOCS.md with:
- Endpoints
- Request/Response schemas
- Example usage
- Authentication
```

**Priority:** LOW - Nice to have

---

### Phase 7: Integration Features (LOW PRIORITY)

#### 7.1 GitHub Integration
**Feature:** Direct GitHub operations

**Capabilities:**
```python
async def create_pr(
    self,
    ctx: RunContext[None],
    title: str,
    body: str,
    base: str = "main"
) -> str:
    """Create GitHub pull request"""

async def list_issues(self, ctx: RunContext[None]) -> str:
    """List GitHub issues"""

async def create_issue(
    self,
    ctx: RunContext[None],
    title: str,
    body: str
) -> str:
    """Create GitHub issue"""
```

**Use Case:**
```
You: Create a PR for my changes with title "Add authentication"

WYN360:
Created PR #123: Add authentication
https://github.com/user/repo/pull/123
```

**Priority:** LOW - Useful but not essential

---

#### 7.2 Database Tools
**Feature:** Direct database operations

**Capabilities:**
```python
async def run_query(
    self,
    ctx: RunContext[None],
    query: str,
    connection_string: str
) -> str:
    """Execute SQL query and return results"""

async def describe_table(
    self,
    ctx: RunContext[None],
    table_name: str
) -> str:
    """Show table schema"""
```

**Priority:** LOW - Niche use case

---

### Phase 8: Safety & Quality (HIGH PRIORITY)

#### 8.1 Pre-Execution Validation
**Feature:** Validate code before execution

**Checks:**
```python
# Before running command
- Static analysis (syntax errors)
- Security scanning (dangerous operations)
- Dependency checking (missing imports)
```

**Example:**
```
You: Run script.py

WYN360:
⚠️  WARNING: Security issues detected:
- Line 15: eval() is potentially unsafe
- Line 23: os.system() without sanitization

Continue anyway? (y/N):
```

**Priority:** HIGH - Safety first

---

#### 8.2 Automatic Backups
**Feature:** Create backups before modifications

**Implementation:**
```python
# Before write_file with overwrite=True
backup_path = f".wyn360_backup/{file_path}.{timestamp}"
shutil.copy(file_path, backup_path)
```

**Commands:**
```bash
/backup list     # Show all backups
/backup restore  # Restore from backup
/backup clean    # Clean old backups
```

**Priority:** MEDIUM - Prevents accidents

---

#### 8.3 Undo/Rollback
**Feature:** Undo last operation

**Implementation:**
```python
# Track all operations in session
operations = [
    {"type": "write_file", "path": "app.py", "backup": "..."},
    {"type": "delete_file", "path": "old.py", "backup": "..."},
]

# Rollback command
/undo  # Undo last operation
/undo 3  # Undo last 3 operations
```

**Priority:** MEDIUM - Safety net

---

### Phase 9: Monitoring & Analytics (LOW PRIORITY)

#### 9.1 Token Usage Tracking
**Feature:** Track and display token usage

**Dashboard:**
```
You: /stats

WYN360 Session Statistics:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Messages:        25
Input tokens:    45,230  ($0.136)
Output tokens:   12,450  ($0.187)
Total cost:      $0.323
Average/message: $0.013
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Most expensive operations:
1. Project analysis       $0.046
2. Multi-file refactor   $0.038
3. Test generation       $0.032
```

**Priority:** LOW - Nice for cost tracking

---

#### 9.2 Performance Metrics
**Feature:** Track response times and success rates

**Metrics:**
```
- Average response time
- Tool success rate
- Most used tools
- Error frequency
```

**Priority:** LOW - Mostly for development

---

### Phase 10: Collaboration Features (LOW PRIORITY)

#### 10.1 Session Sharing
**Feature:** Share WYN360 sessions with team

**Implementation:**
```bash
# Export session
wyn360 --export session.json

# Import on another machine
wyn360 --import session.json
```

**Use Case:** Share coding session with colleague for review

**Priority:** LOW - Team feature

---

#### 10.2 Prompt Library
**Feature:** Share and reuse prompts

**Implementation:**
```yaml
# prompts.yaml
prompts:
  refactor_for_testing:
    text: "Refactor this code to be more testable by extracting dependencies"

  add_logging:
    text: "Add comprehensive logging to this module using Python logging"

  optimize_performance:
    text: "Analyze and optimize this code for better performance"
```

**Usage:**
```
You: @refactor_for_testing app.py

WYN360: [Applies the refactor_for_testing prompt to app.py]
```

**Priority:** LOW - Power user feature

---

## 📊 Implementation Priority Matrix

### HIGH Priority (Implement Soon)
1. ✨ **Conversation History in API** - Most impactful
2. ✨ **Git Operations Tool** - Frequently needed
3. ✨ **Search/Grep Tool** - Essential for large codebases
4. ✨ **Streaming Responses** - Major UX improvement
5. ✨ **Pre-Execution Validation** - Safety critical

### MEDIUM Priority (Next Phase)
6. 🔧 **Context Management Commands** - User control
7. 🔧 **Model Selection** - Cost optimization
8. 🔧 **Configuration File** - Personalization
9. 🔧 **File Management Tools** - Complete file operations
10. 🔧 **Multi-File Refactoring** - Advanced workflow
11. 🔧 **Test Generation** - High value
12. 🔧 **Automatic Backups** - Safety
13. 🔧 **Undo/Rollback** - Safety net

### LOW Priority (Future Consideration)
14. 💡 **GitHub Integration** - Nice to have
15. 💡 **Database Tools** - Niche
16. 💡 **Token Usage Dashboard** - Analytics
17. 💡 **Session Sharing** - Collaboration
18. 💡 **Prompt Library** - Power users
19. 💡 **Documentation Generation** - Automation

---

## 🎯 Recommended Development Roadmap

### v0.3.0 - Context & History
**Focus:** Conversation context management
- Add conversation history to API calls
- Implement /clear, /history commands
- Add token usage tracking
- Session save/load

**Timeline:** 2-3 weeks

---

### v0.4.0 - Enhanced Tools
**Focus:** Additional tool capabilities
- Git operations tool
- Search/grep functionality
- File management (delete, move, mkdir)
- Pre-execution validation

**Timeline:** 3-4 weeks

---

### v0.5.0 - Streaming & UX
**Focus:** Real-time experience
- Token-by-token streaming
- Better progress indicators
- Configuration file support
- Project-specific context

**Timeline:** 2-3 weeks

---

### v0.6.0 - Advanced Workflows
**Focus:** Complex operations
- Multi-file refactoring
- Test generation mode
- Automatic backups
- Undo/rollback

**Timeline:** 3-4 weeks

---

### v0.7.0+ - Integrations
**Focus:** External services
- GitHub integration
- Model selection
- Database tools
- Analytics dashboard

**Timeline:** TBD

---

## 💡 Quick Wins (Easy to Implement)

### 1. Add Version Command
```bash
wyn360 --version  # Show current version
```

### 2. Add Help in Session
```bash
You: /help
WYN360: [Shows available commands and tips]
```

### 3. Keyboard Shortcuts Documentation
```bash
You: /shortcuts
WYN360:
- Ctrl+C: Cancel current operation
- Ctrl+D: Exit
- Ctrl+Enter: New line
- Enter: Submit
```

### 4. Exit Code Summary
After each command, show summary:
```
✅ Command executed successfully (exit code 0)
   Duration: 2.3s
   Output lines: 45
```

### 5. Better Error Messages
Instead of: "An error occurred: Tool 'write_file' exceeded max retries"
Show: "I tried 3 times but couldn't write the file. This usually means..."

---

## 🔮 Future Vision (v1.0+)

**Long-term possibilities:**

### 1. **WYN360 as Code Review Assistant**
- Automated PR reviews
- Security vulnerability detection
- Best practices suggestions
- Performance optimization recommendations

### 2. **WYN360 as CI/CD Integration**
- Automatic test generation in CI pipeline
- Documentation generation on commit
- Code quality checks
- Deployment assistance

### 3. **WYN360 as Teaching Tool**
- Explain code line-by-line
- Generate learning examples
- Create coding challenges
- Interactive tutorials

### 4. **WYN360 as Architecture Advisor**
- System design suggestions
- Refactoring recommendations
- Technology selection
- Performance optimization

### 5. **WYN360 IDE Plugin**
- VSCode extension
- JetBrains plugin
- Vim integration
- Embedded in popular IDEs

---

## 📝 Community Feature Requests

**How to contribute ideas:**

1. Open GitHub issue with label `feature-request`
2. Describe use case and expected behavior
3. Discuss implementation approach
4. Community votes on priority

**Template:**
```markdown
## Feature Request: [Name]

**Use Case:**
[Describe the problem this solves]

**Proposed Solution:**
[How it should work]

**Example:**
[Show example interaction]

**Priority:** [High/Medium/Low]
```

---

## 🤝 Contributing

Want to help implement these features?

1. Check the [GitHub Issues](https://github.com/yiqiao-yin/wyn360-cli/issues) for open feature requests
2. Comment on the feature you want to work on
3. Fork the repository
4. Implement the feature with tests
5. Submit a pull request

**Development Setup:**
```bash
git clone https://github.com/yiqiao-yin/wyn360-cli.git
cd wyn360-cli
poetry install
WYN360_SKIP_CONFIRM=1 poetry run pytest tests/ -v
```

---

## 📞 Feedback

**Have suggestions not listed here?**

- 📧 Email: yiqiao.yin@wyn-associates.com
- 🐛 Issues: https://github.com/yiqiao-yin/wyn360-cli/issues
- 💬 Discussions: https://github.com/yiqiao-yin/wyn360-cli/discussions

---

**Last Updated:** January 2025
**Current Version:** 0.3.5
**Next Planned Release:** v0.6.0 (Advanced Workflows)
