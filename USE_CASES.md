# WYN360 CLI - Use Cases & Capabilities

This document provides a comprehensive overview of what WYN360 CLI can do and how to use it effectively.

## 🎯 Core Use Cases

### 1. Start New Projects from Scratch (Blank Directory)

When you're in an empty directory and want to build something from scratch, WYN360 becomes your coding partner.

**How it works:**
- User describes what they want to build in natural language
- Agent generates complete, runnable code
- Automatically extracts code from responses using regex
- Saves files with smart naming conventions

**Smart File Naming:**
- `app.py` - For Streamlit or FastAPI applications
- `main.py` - For general scripts with main() functions
- `script.py` - For simple utility scripts

**Example Interaction:**
```
You: Build a Streamlit chatbot that echoes user input

WYN360:
✓ Generates complete app.py with Streamlit code
✓ Creates requirements.txt with dependencies
✓ Provides setup and run instructions
✓ Includes usage examples
```

**Real-world scenarios:**
- Quick prototypes for demos
- Learning new frameworks
- Starting weekend projects
- Creating utility scripts
- Building proof-of-concepts

---

### 2. Analyze Existing Projects

WYN360 can understand your existing codebase before making suggestions or changes.

**Analysis Capabilities:**
- Scans directory structure and categorizes files
- Reads Python files, configs, and documentation
- Understands project architecture and patterns
- Identifies dependencies and relationships
- Makes context-aware recommendations

**Available Analysis Tools:**

| Tool | Function | Use Case |
|------|----------|----------|
| `list_files()` | Inventory all files by category | "What files do I have?" |
| `read_file()` | Read specific file contents | "Show me my config.py" |
| `get_project_info()` | Generate comprehensive project summary | "Summarize my project structure" |

**Example Interaction:**
```
You: What does my project do?

WYN360:
- Scans all files in the directory
- Identifies main entry points
- Reads configuration files
- Analyzes dependencies
- Provides comprehensive summary
```

**File Categorization:**
- **Python files** (`.py`) - Source code
- **Text files** (`.md`, `.txt`, `.rst`) - Documentation
- **Config files** (`.json`, `.yaml`, `.toml`, `.ini`) - Configuration
- **Other files** - Resources, data, etc.

---

### 3. Add Features to Existing Code

Enhance your existing projects with new functionality while maintaining code quality and consistency.

**How it works:**
1. Agent reads your current code structure
2. Understands existing patterns and conventions
3. Generates new features that integrate seamlessly
4. Can modify/enhance existing files
5. Maintains your coding style

**Example Interaction:**
```
You: Add authentication to my FastAPI app

WYN360:
1. Reads your existing app structure
2. Identifies route definitions
3. Generates authentication middleware
4. Updates routes with auth decorators
5. Provides implementation guide
```

**Common Feature Additions:**
- Authentication and authorization
- Database integration
- API endpoints
- Error handling and logging
- Input validation
- Caching mechanisms
- Testing utilities

---

### 4. Code Generation & Refactoring

Write high-quality Python code or improve existing code.

**Code Generation Features:**
- Production-ready code with error handling
- Comprehensive docstrings and comments
- Type hints and annotations
- Best practices and design patterns
- Unit test suggestions

**Refactoring Capabilities:**
- Improve code structure
- Add documentation
- Optimize performance
- Enhance readability
- Apply design patterns

**Quality Standards:**
- Follows PEP 8 style guidelines
- Includes proper error handling
- Uses meaningful variable names
- Provides clear documentation
- Considers edge cases

**Example Interaction:**
```
You: Refactor my data processing script to use async

WYN360:
- Analyzes current synchronous code
- Identifies I/O-bound operations
- Converts to async/await patterns
- Adds proper exception handling
- Includes usage examples
```

---

### 5. Interactive Coding Assistant

Get help, guidance, and answers to your Python questions.

**Capabilities:**
- Answer coding questions
- Debug issues and errors
- Explain complex concepts
- Provide implementation guidance
- Review code quality
- Suggest improvements

**Example Interactions:**

**Debugging:**
```
You: My script has a connection timeout error

WYN360:
1. Reads your code
2. Identifies the issue
3. Explains the root cause
4. Suggests fix with retry logic
5. Can update the file directly
```

**Learning:**
```
You: How do I implement async in Python?

WYN360:
- Explains async/await concepts
- Provides working examples
- Shows best practices
- Demonstrates common patterns
- Warns about pitfalls
```

**Code Review:**
```
You: Review my API implementation

WYN360:
- Analyzes code structure
- Checks error handling
- Reviews security considerations
- Suggests improvements
- Provides specific fixes
```

---

### 6. Execute Commands and Scripts (NEW in v0.2.2)

Run any shell command, Python script, or CLI tool directly through WYN360 with built-in safety confirmations.

**Capabilities:**
- Execute Python scripts
- Run UV commands for package management
- Start Streamlit/FastAPI applications
- Execute shell scripts
- Run any CLI tool (npm, docker, git, etc.)
- Built-in timeout protection (5 minutes default)
- User confirmation before execution

**Supported Command Types:**

| Command Type | Example | Use Case |
|--------------|---------|----------|
| Python Scripts | `python run_analysis.py` | Run data analysis scripts |
| UV Package Manager | `uv init project`, `uv add torch` | Initialize projects, install packages |
| UV Run | `uv run streamlit run app.py` | Run apps in UV environments |
| Shell Scripts | `bash setup.sh` | Execute automation scripts |
| Any CLI Tool | `npm install`, `docker ps` | Use any command-line tool |

**Safety Features:**
- ⚠️ Confirmation prompt before execution
- ⏱️ Automatic timeout after 5 minutes (configurable)
- 📝 Captures both stdout and stderr
- ✅ Shows exit codes and success status
- 🔒 Runs with user's permissions in current directory

**Example Interaction:**
```
You: Run the adult.py analysis script

WYN360: [Prepares to execute]

======================================================================
⚠️  COMMAND EXECUTION CONFIRMATION
======================================================================
Command: python adult.py
Directory: /your/working/directory
Permissions: Full user permissions
======================================================================

>>> WAITING FOR YOUR RESPONSE <<<

Execute this command? (y/N): y

✅ Command executed successfully (exit code 0)

Output:
Loading Adult dataset...
Preprocessing data...
Training model...
Accuracy: 0.85
Results saved to results.csv
```

**Note:** The confirmation prompt appears while the "thinking" spinner may still be visible. This is normal - just type your response and press Enter.

**UV Workflow Example:**
```
You: Initialize a new UV project called my-app and add streamlit

WYN360: I'll help you set up a UV project:

1. First, initializing the project...

======================================================================
⚠️  COMMAND EXECUTION CONFIRMATION
======================================================================
Command: uv init my-app
Directory: /current/directory
Permissions: Full user permissions
======================================================================

>>> WAITING FOR YOUR RESPONSE <<<

Execute this command? (y/N): y

✅ Project initialized

2. Now adding Streamlit...

[Similar confirmation prompt]
Execute this command? (y/N): y

✅ Streamlit added to dependencies
```

**Bypass Confirmation (For Testing):**
Set environment variable `WYN360_SKIP_CONFIRM=1` to skip confirmation prompts.

---

### 7. Multi-line Input Support (NEW in v0.2.2)

Write complex, multi-line prompts with ease using keyboard shortcuts.

**How it works:**
- **Enter** → Submit your message
- **Ctrl+Enter** → Add a new line (continue typing)

**Example:**
```
You: [Ctrl+Enter for each line]
Create a Streamlit app that:
1. Loads a CSV file
2. Shows summary statistics
3. Displays interactive charts
4. Allows filtering by columns
[Press Enter to submit]

WYN360: [Generates complete multi-featured app]
```

**Why it's useful:**
- Write detailed, structured prompts
- Paste code with proper formatting
- Create multi-step instructions
- Format lists and requirements clearly

---

## 🤖 Intelligent File Operation Handling (NEW in v0.2.1)

WYN360 now includes advanced intelligence for understanding user intent when working with files, automatically determining whether to create new files or update existing ones.

### Intent Recognition

The agent analyzes your natural language to understand what you want:

**Update Existing Files** - When you say:
- "Add feature to my app"
- "Update the chatbot"
- "Improve my script"
- "Modify the config"
- "Change the API endpoint"

**Action taken:**
1. Agent reads the existing file first to understand current state
2. Makes the requested modifications
3. Writes back with `overwrite=True`
4. Shows you what changed

**Create New Files** - When you say:
- "Create a new script called utils.py"
- "Make another chatbot"
- "Build a separate module"
- "Generate a helper file"

**Action taken:**
1. Agent creates the new file
2. Uses `overwrite=False` to prevent accidents
3. Leaves existing files untouched

### Context-Aware Updates

**Before updating any file, the agent:**
1. ✓ Reads the current file contents
2. ✓ Understands the existing structure
3. ✓ Makes intelligent modifications
4. ✓ Preserves what shouldn't change
5. ✓ Explains what was updated

**Example:**
```
You: Add a feature to run hello_world.py when user asks

WYN360:
1. Reading your current app.py...
2. Creating hello_world.py...
3. Updating app.py with new functionality...
✓ Created: hello_world.py
✓ Updated: app.py (added script execution feature)
```

### Self-Correcting Behavior

If the agent makes a wrong choice, it can self-correct:

**Scenario:**
- Agent tries to create file but it already exists
- Gets clear error: "File exists. Use overwrite=True to update"
- Automatically retries with correct settings (up to 3 retries)
- Succeeds on retry

**Benefits:**
- No more "max retries exceeded" errors
- Agent learns from mistakes
- Seamless user experience
- Natural language understanding

### Smart Retry Mechanism

**Configuration:** 3 retries for tool operations

**How it works:**
1. First attempt based on intent recognition
2. If error occurs, analyzes the error message
3. Adjusts parameters (e.g., sets overwrite=True)
4. Retries with corrected parameters
5. Repeats up to 3 times

**This handles:**
- File existence conflicts
- Permission issues
- Temporary failures
- Ambiguous user requests

---

### 8. Git Operations (NEW in v0.2.9)

WYN360 can now interact with git repositories to help you manage version control.

**Example Interaction:**
```
You: What files have I changed?

WYN360: [Calls git_status tool]
Git Status:

On branch main
Changes not staged for commit:
  modified:   agent.py
  modified:   tests/test_agent.py

Untracked files:
  new_feature.py
```

**Available Git Operations:**

| Command | Tool | Use Case |
|---------|------|----------|
| "Show git status" | `git_status()` | See modified and untracked files |
| "What changed in agent.py?" | `git_diff(file_path)` | View specific file changes |
| "Show recent commits" | `git_log(max_count)` | Review commit history |
| "What branch am I on?" | `git_branch()` | List all branches |

**Real-world scenarios:**
```
You: Show me what changed in my last session
WYN360: [Shows git diff output with line-by-line changes]

You: Show the last 5 commits
WYN360: [Displays commit history with messages and SHAs]

You: What branch am I working on?
WYN360: [Shows current branch marked with *]
```

**Benefits:**
- ✅ Quick status checks without leaving the CLI
- ✅ Review changes before committing
- ✅ Understand project history
- ✅ Stay oriented in your git workflow

---

### 9. Code Search (NEW in v0.2.9)

Find code patterns, definitions, and usage across your entire project.

**Example Interaction:**
```
You: Where is the User class defined?

WYN360: [Calls search_files("class User", "*.py")]
Search Results for 'class User' in *.py:

./models/user.py:15:class User(BaseModel):
./tests/test_models.py:8:class UserTest(unittest.TestCase):
```

**Search Capabilities:**

| Query | Tool Call | Result |
|-------|-----------|--------|
| "Find all TODO comments" | `search_files("TODO", "*.py")` | Lists files and line numbers |
| "Where do I import requests?" | `search_files("import requests")` | Shows all import statements |
| "Find database connections" | `search_files("connect", "*.py")` | Locates connection code |
| "Show all API endpoints" | `search_files("@app.route")` | Lists Flask/FastAPI routes |

**Advanced Search Examples:**
```
You: Find all functions that use the requests library
WYN360: [Searches for 'requests.' across Python files]
Found 12 matches across 4 files

You: Show me all error logging statements
WYN360: [Searches for 'logger.error' or 'logging.error']
Located error handling in 8 different locations

You: Where are environment variables used?
WYN360: [Searches for 'os.getenv' and 'os.environ']
Environment variables accessed in config.py and utils.py
```

**Search Features:**
- ✅ Regex pattern support
- ✅ File type filtering (*.py, *.txt, etc.)
- ✅ Line numbers for easy navigation
- ✅ Smart truncation (shows first 100 matches)
- ✅ Case-insensitive searching

---

### 10. File Management (NEW in v0.2.9)

Complete file system operations for organizing your project.

**Delete Files:**
```
You: Delete the old_script.py file

WYN360: [Calls delete_file("old_script.py")]
✓ Successfully deleted file: old_script.py
```

**Move/Rename Files:**
```
You: Rename utils.py to helpers.py

WYN360: [Calls move_file("utils.py", "helpers.py")]
✓ Successfully moved 'utils.py' to 'helpers.py'

You: Move config.py to the src directory

WYN360: [Calls move_file("config.py", "src/config.py")]
✓ Successfully moved 'config.py' to 'src/config.py'
```

**Create Directories:**
```
You: Create a tests directory

WYN360: [Calls create_directory("tests")]
✓ Successfully created directory: tests

You: Create nested directories src/utils/helpers

WYN360: [Calls create_directory("src/utils/helpers")]
✓ Successfully created directory: src/utils/helpers
```

**Project Reorganization Workflow:**
```
You: I want to reorganize my project. Create src, tests, and docs directories

WYN360:
[Creates src directory]
✓ Successfully created directory: src

[Creates tests directory]
✓ Successfully created directory: tests

[Creates docs directory]
✓ Successfully created directory: docs

Your project structure is now organized with src/, tests/, and docs/ directories.

You: Move all .py files except tests to src

WYN360:
[Moves files one by one, preserving structure]
✓ Successfully moved 'app.py' to 'src/app.py'
✓ Successfully moved 'utils.py' to 'src/utils.py'
✓ Successfully moved 'config.py' to 'src/config.py'
```

**Safety Features:**
- ⚠️ Delete operations are irreversible - use with caution
- ✅ Move operations create parent directories automatically
- ✅ Prevents overwriting existing files
- ✅ Clear error messages for permission issues

---

### 11. Model Selection & Optimization (NEW in v0.3.0)

Choose the right AI model for your task to optimize cost and performance.

**Available Models:**

| Model | Speed | Cost | Best For |
|-------|-------|------|----------|
| **Haiku** | Fastest | Cheapest ($0.25/$1.25 per M) | Simple file ops, quick questions |
| **Sonnet** | Balanced | Moderate ($3/$15 per M) | General coding, analysis (default) |
| **Opus** | Slower | Premium ($15/$75 per M) | Complex reasoning, architecture |

**Viewing Current Model:**
```
You: /model

[Model Information Table]
Model: Sonnet 4
Full ID: claude-sonnet-4-20250514
Description: Balanced performance - general coding & analysis
Input Cost: $3.00/M tokens
Output Cost: $15.00/M tokens

Available models: haiku, sonnet, opus
Usage: /model <name>  (e.g., /model haiku)
```

**Switching Models Mid-Session:**
```
You: /model haiku
✓ Switched to Haiku (claude-3-5-haiku-20241022)

You: List all Python files in this directory
WYN360: [Uses Haiku - fast and cheap for simple task]

You: /model opus
✓ Switched to Opus 4 (claude-opus-4-20250514)

You: Refactor my entire application architecture
WYN360: [Uses Opus - most capable for complex reasoning]
```

**Cost Optimization Strategies:**

**Strategy 1: Start with Haiku, upgrade as needed**
```
You: /model haiku

You: Show me the files in this project
WYN360: [Haiku handles this easily - saves money]

You: Now help me redesign the database schema
You: /model opus

WYN360: [Switches to Opus for complex architectural decision]
```

**Strategy 2: Use Sonnet for most work, Haiku for repetitive tasks**
```
You: /model sonnet

You: Add error handling to api.py
WYN360: [Sonnet provides good code quality]

You: /model haiku

You: Run git status
You: List files in tests directory
You: Show me config.json
WYN360: [Haiku handles these simple operations cheaply]
```

**Strategy 3: Model selection by session type**

**Exploration sessions (Haiku):**
- Understanding new codebase
- Reading files
- Running git commands
- Simple searches

**Development sessions (Sonnet - default):**
- Writing new features
- Refactoring code
- Debugging issues
- General coding

**Architecture sessions (Opus):**
- System design
- Complex refactoring
- Performance optimization
- Critical bug fixes

**Real-World Cost Comparison:**

```
Scenario: Adding a new feature (10 interactions)

With Haiku only:
  - 15K input tokens × $0.25/M = $0.004
  - 8K output tokens × $1.25/M = $0.010
  - Total: $0.014

With Sonnet (default):
  - 15K input tokens × $3.00/M = $0.045
  - 8K output tokens × $15.00/M = $0.120
  - Total: $0.165

With Opus:
  - 15K input tokens × $15.00/M = $0.225
  - 8K output tokens × $75.00/M = $0.600
  - Total: $0.825

Optimized (mixed):
  - 3 simple tasks with Haiku: $0.004
  - 5 coding tasks with Sonnet: $0.083
  - 2 complex tasks with Opus: $0.165
  - Total: $0.252 (saves 69% vs all Opus, better quality than all Haiku)
```

**Command-Line Model Selection:**

You can also set the model when starting WYN360:
```bash
# Start with Haiku for quick tasks
wyn360 --model haiku

# Start with Opus for complex work
wyn360 --model opus

# Use full model ID
wyn360 --model claude-sonnet-4-20250514
```

**Pro Tips:**
- ✅ Use `/model` without arguments to check current model and costs
- ✅ Switch models freely - conversation history is preserved
- ✅ Start sessions with cheaper models, upgrade when needed
- ✅ Use Haiku for file operations and git commands
- ✅ Use Opus sparingly for genuinely complex architectural decisions
- ✅ Monitor costs with `/tokens` command
- ⚠️ Model switches only affect future requests, not past ones

---

## 🛠️ Available Tools

WYN360 has access to these specialized tools for file and project operations:

### `read_file(file_path: str)`
**Purpose:** Read the contents of any file in your project

**Parameters:**
- `file_path` - Path to the file to read

**Use cases:**
- "What's in my config.py?"
- "Show me the main.py file"
- "Read my requirements.txt"

**Safety features:**
- File size limits (1MB default)
- UTF-8 encoding
- Error handling for missing files

---

### `write_file(file_path: str, content: str, overwrite: bool)`
**Purpose:** Create new files or update existing ones

**Parameters:**
- `file_path` - Where to write the file
- `content` - What to write
- `overwrite` - Whether to replace existing files (default: False)

**Use cases:**
- "Create a utils.py with helper functions"
- "Update my config.json"
- "Save this code as script.py"

**Safety features:**
- Prevents accidental overwrites
- Creates parent directories automatically
- Validates file paths

---

### `list_files(directory: str)`
**Purpose:** Show all files in a directory, organized by category

**Parameters:**
- `directory` - Directory to scan (default: current directory)

**Returns:**
- Python files
- Text/documentation files
- Configuration files
- Other files

**Use cases:**
- "What files do I have?"
- "Show me all Python files"
- "List the project structure"

**Features:**
- Ignores common patterns (`__pycache__`, `.git`, `node_modules`, etc.)
- Categorizes by file type
- Recursive directory scanning

---

### `get_project_info()`
**Purpose:** Generate a comprehensive project summary

**Returns:**
- Total file count
- Files by category
- Project structure overview
- Blank vs existing project status

**Use cases:**
- "Summarize my project"
- "What kind of project is this?"
- "Give me an overview"

**Analysis includes:**
- File counts and distribution
- Directory structure
- Main components
- Technology stack indicators

---

## 📁 Smart File Handling

### Automatic Code Saving

When you're in a **blank project** (no Python or text files), WYN360 automatically saves generated code:

**Process:**
1. Detects Python code blocks in responses (using ``` regex)
2. Extracts the code
3. Suggests appropriate filename based on content
4. Saves automatically
5. Confirms with message: `✓ Code saved to: filename.py`

**Filename Detection Logic:**
```python
if 'streamlit' in code:
    filename = 'app.py'
elif 'fastapi' in code or 'FastAPI' in code:
    filename = 'app.py'
elif 'def main' in code:
    filename = 'main.py'
elif 'class ' in code:
    filename = 'main.py'
else:
    filename = 'script.py'
```

### File Type Recognition

WYN360 categorizes files to understand your project:

| Category | Extensions | Purpose |
|----------|-----------|----------|
| Python | `.py` | Source code |
| Text | `.md`, `.txt`, `.rst` | Documentation |
| Config | `.json`, `.yaml`, `.toml`, `.ini`, `.cfg` | Configuration |
| Other | All others | Resources, data, etc. |

---

## 💡 Example Workflows

### Workflow 1: Brand New Project
```
Step 1: Navigate to empty directory
$ cd my-new-project

Step 2: Start WYN360
$ wyn360

Step 3: Describe what you want
You: Build a CLI tool that converts CSV to JSON

Step 4: Agent generates and saves code
WYN360:
- Generates complete script with argparse
- Includes CSV parsing logic
- Adds JSON output formatting
- ✓ Code saved to: main.py

Step 5: Review and run
You: How do I use it?

WYN360:
- Provides usage instructions
- Shows example commands
- Explains options
```

---

### Workflow 2: Enhance Existing Project
```
Step 1: Navigate to your project
$ cd my-existing-project

Step 2: Start WYN360
$ wyn360

Step 3: Request enhancement
You: Add logging to my data pipeline

Step 4: Agent analyzes and modifies
WYN360:
- Reads existing pipeline.py
- Understands current structure
- Generates logging configuration
- Shows you the changes
- Explains the additions

Step 5: Review and accept
You: Apply these changes

WYN360:
- Updates the file
- Confirms changes made
- Provides testing guidance
```

---

### Workflow 3: Debug & Fix
```
Step 1: Encounter an error
$ python script.py
Error: Connection timeout

Step 2: Ask WYN360 for help
You: My script has a connection timeout error

Step 3: Agent diagnoses
WYN360:
- Reads your script
- Identifies the problematic code
- Explains the root cause
- Shows the exact issue

Step 4: Get the fix
You: How do I fix it?

WYN360:
- Suggests retry logic
- Provides complete code
- Explains the solution
- Offers to update the file

Step 5: Apply fix
You: Update my script

WYN360:
- Modifies the file
- Confirms the change
- ✓ Code updated successfully
```

---

### Workflow 4: Learning & Guidance
```
You: How do I implement async in Python?

WYN360:
📚 Explanation:
- What async/await does
- When to use it
- How it works

💻 Working Examples:
- Simple async function
- Using asyncio.gather()
- Error handling in async

✨ Best Practices:
- When NOT to use async
- Common pitfalls
- Performance tips

🎯 Real-world Example:
- Complete async HTTP client
- Concurrent API requests
- Proper exception handling
```

---

## 🚀 Key Strengths

### 1. Context-Aware Development
- Reads and understands your project structure before making changes
- Maintains consistency with your existing code style
- Suggests changes that integrate seamlessly

### 2. Production-Ready Code
- Proper error handling and edge cases
- Comprehensive docstrings
- Type hints where appropriate
- Follows best practices

### 3. Interactive & Iterative
- Chat-based interface for natural interaction
- Ask follow-up questions
- Refine solutions iteratively
- Get explanations anytime

### 4. Automatic File Management
- Saves generated code automatically (in blank projects)
- Smart file naming based on content
- Creates directory structures as needed

### 5. Intelligent Code Analysis
- Detects code patterns (Streamlit, FastAPI, etc.)
- Suggests appropriate file names
- Understands project structure

---

## ⚠️ Current Limitations

### 1. Python-Focused
- **Optimized for:** Python projects and development
- **Can discuss:** Other languages, but tooling is Python-centric
- **Best for:** Python developers and learners

### 2. Local Files Only
- **Works with:** Files in current directory and subdirectories
- **Cannot access:** Remote repositories, databases, external APIs
- **Scope:** Local file system only

### 3. No Git Operations
- **Cannot:** Commit, push, pull, or manage git
- **Can:** Generate code that you commit manually
- **Workaround:** Use git commands yourself after agent makes changes

### 4. No Package Installation
- **Cannot:** Run `pip install` or install dependencies
- **Can:** Generate requirements.txt
- **Workaround:** Install packages manually

### 5. Session-Based Memory
- **No persistent memory** between CLI sessions
- Each session starts fresh
- **Workaround:** Provide context in each session

### 6. File Size Limits
- Maximum file size: 1MB per file
- Prevents reading very large files
- **Workaround:** Process large files in chunks

---

## 🎯 Best Use Cases

### ✅ Excellent For:

#### Rapid Prototyping
- Build MVPs quickly
- Test ideas fast
- Create proof-of-concepts
- Generate starter templates

#### Learning Python
- Get explanations for concepts
- See working examples
- Understand best practices
- Debug learning projects

#### Starting New Projects
- Generate project structure
- Create boilerplate code
- Set up configurations
- Initialize common patterns

#### Adding Features
- Extend existing code
- Integrate new functionality
- Refactor safely
- Improve code quality

#### Code Review & Suggestions
- Get improvement ideas
- Identify potential issues
- Learn better patterns
- Optimize performance

---

### ❌ Not Ideal For:

#### Non-Python Projects
- JavaScript/TypeScript (can advise, but limited tooling)
- Java, C++, Go (conceptual help only)
- Mobile development (limited support)

#### Large-Scale Refactoring
- Entire codebase restructuring (better in IDE)
- Renaming across many files (use IDE refactoring tools)
- Complex merge operations

#### Production Deployments
- CI/CD pipeline execution
- Server deployments
- Container orchestration
- Infrastructure as code

#### Version Control Operations
- Git workflows
- Branch management
- Merge conflict resolution
- Pull request creation

#### Database Operations
- Direct database queries
- Schema migrations
- Data manipulation
- Backup/restore operations

---

## 💡 Pro Tips

### 1. Be Specific
**Instead of:** "Make my code better"
**Try:** "Add error handling to my API endpoints"

### 2. Provide Context
**Instead of:** "This doesn't work"
**Try:** "My FastAPI app returns 500 errors when the database is down"

### 3. Iterate
- Start with basic version
- Ask for improvements
- Refine step by step
- Build incrementally

### 4. Use in Combination with IDE
- Generate code with WYN360
- Refine in your IDE
- Use IDE for complex refactoring
- Use WYN360 for quick generation

### 5. Review Generated Code
- Always read generated code
- Understand what it does
- Test before deploying
- Customize as needed

### 6. Use Clear Intent Language
- Say "add feature" or "update" when modifying existing files
- Say "create new" or "make another" for new files
- Be explicit about what you want to change
- The agent understands natural language intent

**Examples:**
- ✅ "Add authentication to my app" (updates existing)
- ✅ "Create a new helper module" (creates new)
- ✅ "Improve error handling" (updates existing)
- ✅ "Build a separate API client" (creates new)

### 7. Manage Context with Slash Commands (NEW in v0.2.8)
- Use `/tokens` to monitor API costs during long sessions
- Use `/save` to preserve important conversations for later
- Use `/load` to continue previous work sessions
- Use `/clear` when starting fresh to reduce token usage
- Use `/history` to review what you've discussed

**Example Workflow:**
```
You: Build a data analysis pipeline
WYN360: [Creates initial pipeline]

You: Add visualization features
WYN360: [Enhances the pipeline]

You: /tokens
[Token Usage Statistics]
Total Cost: $0.03

You: /save my_pipeline_session.json
✓ Session saved

[Later...]
You: /load my_pipeline_session.json
✓ Session loaded (conversation history restored)

You: Add export to Excel feature
WYN360: [Continues from where you left off with full context]
```

**Cost Management Tips:**
- Check `/tokens` regularly to track spending
- Use `/clear` after completing a major feature to reset context
- Save sessions before clearing to preserve your work
- Long conversations cost more due to conversation history in each API call
- Balance between context (better results) and cost (fewer tokens)

---

## 🎓 Learning Path

### Beginner
1. Start in blank directory
2. Ask to build simple scripts
3. Learn from generated code
4. Ask "why" and "how" questions

### Intermediate
1. Bring existing projects
2. Ask for feature additions
3. Request refactoring help
4. Learn best practices

### Advanced
1. Use for rapid prototyping
2. Generate complex architectures
3. Get design pattern suggestions
4. Review and optimize code

---

## 📞 Need Help?

If you run into issues or have questions:

1. **Ask the agent:** WYN360 can explain its own capabilities
2. **Check GitHub:** https://github.com/yiqiao-yin/wyn360-cli
3. **Read the README:** Basic setup and usage
4. **Report issues:** GitHub Issues page

---

## 🚀 Quick Start Examples

### Example 1: Build a Web Scraper
```
You: Create a web scraper that extracts article titles from a news site

WYN360: [Generates complete script with requests, BeautifulSoup, error handling]
✓ Code saved to: scraper.py
```

### Example 2: Data Processing Pipeline
```
You: Build a script that reads CSV, cleans data, and outputs to JSON

WYN360: [Creates comprehensive data pipeline with pandas]
✓ Code saved to: process_data.py
```

### Example 3: API Client
```
You: Create an async HTTP client for a REST API

WYN360: [Generates async client with aiohttp, retry logic, error handling]
✓ Code saved to: api_client.py
```

---

## Use Case 12: Configuration & Personalization

**Feature:** User and project-specific configuration files (v0.3.1)

**Problem:** Every developer has different preferences and every project has unique requirements. Repeating instructions manually is tedious.

**Solution:** WYN360 supports two levels of configuration:
1. **User Config** (`~/.wyn360/config.yaml`) - Your personal preferences across all projects
2. **Project Config** (`.wyn360.yaml`) - Project-specific settings and context

### Configuration Levels

#### User Configuration (~/.wyn360/config.yaml)

```yaml
# Personal preferences that apply to all projects
model: claude-sonnet-4-20250514
max_tokens: 4096
temperature: 0.7

# Custom instructions for all your work
custom_instructions: |
  - Always use type hints in Python
  - Follow PEP 8 style guidelines
  - Add comprehensive docstrings
  - Include error handling

# Quick command aliases
aliases:
  test: "run pytest tests/ -v"
  lint: "run ruff check ."
  format: "run ruff format ."

# Your workspace directories
workspaces:
  - ~/projects
  - ~/work
```

#### Project Configuration (.wyn360.yaml)

```yaml
# Project-specific context - helps AI understand your codebase
context: |
  This is a FastAPI web application with:
  - PostgreSQL database (SQLAlchemy ORM)
  - Redis for caching and session management
  - Celery for background tasks
  - JWT authentication
  - RESTful API design

# Key dependencies
dependencies:
  - fastapi
  - sqlalchemy
  - redis
  - celery
  - pyjwt

# Common project commands
commands:
  dev: "uvicorn app.main:app --reload"
  test: "pytest tests/ -v --cov"
  migrate: "alembic upgrade head"

# Override model for this project (optional)
model: claude-3-5-haiku-20241022  # Use faster model for simple project
```

### Configuration Priority

Configurations merge with this precedence (highest to lowest):
1. **Project config** (`.wyn360.yaml` in current directory)
2. **User config** (`~/.wyn360/config.yaml`)
3. **Default values**

### Example Workflows

#### Workflow 1: Setting Up User Preferences

```bash
# First time setup - create default user config
$ wyn360

WYN360:
No user config found. Create one with:
~/.wyn360/config.yaml

# After creating config:
$ wyn360

• Loaded user config from: /home/user/.wyn360/config.yaml
• Custom instructions loaded
✓ Connected using model: claude-sonnet-4-20250514
```

#### Workflow 2: Project-Specific Context

```yaml
# Create .wyn360.yaml in your project root
context: |
  This is a machine learning project that:
  - Trains sentiment analysis models
  - Uses PyTorch and Hugging Face Transformers
  - Processes large text datasets
  - Requires GPU for training

dependencies:
  - pytorch
  - transformers
  - datasets
  - scikit-learn

commands:
  train: "python train.py --config config.yaml"
  evaluate: "python evaluate.py --model checkpoints/best"
```

**When you run wyn360 in this directory:**
```
$ wyn360

• Loaded user config from: ~/.wyn360/config.yaml
• Loaded project config from: .wyn360.yaml
• Custom instructions loaded
• Project context loaded
✓ Connected using model: claude-sonnet-4-20250514

You: Help me implement a new transformer model

WYN360: I see you're working on a sentiment analysis project with PyTorch
and Transformers. Let me help you implement a new model that integrates with
your existing training pipeline...
[AI now understands your project context automatically!]
```

#### Workflow 3: Viewing Current Configuration

```
You: /config

Current Configuration
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Model                   claude-sonnet-4-20250514
Max Tokens              4096
Temperature             0.7
─────────────────────────────────────────────
User Config             ~/.wyn360/config.yaml
Project Config          .wyn360.yaml
─────────────────────────────────────────────
Custom Instructions     - Always use type hints...
Project Context         This is a FastAPI project...
Dependencies            fastapi, sqlalchemy, redis (+2 more)
Aliases                 test, lint, format

Tip: Create ~/.wyn360/config.yaml for user settings
Tip: Create .wyn360.yaml in project root for project settings
```

### Benefits

**1. Consistency Across Projects**
- Same code style and conventions everywhere
- No need to repeat preferences

**2. Team Collaboration**
- Share `.wyn360.yaml` in git repo
- Everyone gets same project context
- New team members onboard faster

**3. Project-Specific Intelligence**
- AI understands your tech stack
- More relevant code suggestions
- Better architecture decisions

**4. Time Savings**
- No repeating "use type hints" every time
- No explaining project structure repeatedly
- Quick command aliases

### Real-World Example

**Scenario:** You're a Python developer who always uses type hints and works on multiple projects (FastAPI, Django, ML).

**Setup:**

1. **User Config** (`~/.wyn360/config.yaml`):
```yaml
custom_instructions: |
  - Always use type hints
  - Add docstrings to all functions
  - Follow PEP 8
  - Prefer pathlib over os.path

aliases:
  test: "run pytest tests/ -v"
  lint: "run ruff check ."
```

2. **FastAPI Project** (`.wyn360.yaml`):
```yaml
context: |
  FastAPI REST API with PostgreSQL
dependencies: [fastapi, sqlalchemy, pydantic]
commands:
  dev: "uvicorn app:app --reload"
```

3. **ML Project** (`.wyn360.yaml`):
```yaml
context: |
  PyTorch deep learning project
dependencies: [torch, transformers, scikit-learn]
commands:
  train: "python train.py"
model: claude-sonnet-4-20250514  # Use more capable model
```

**Result:** When you work in the FastAPI project, the AI knows about FastAPI and REST APIs. When you switch to the ML project, it knows about PyTorch and transformers. Both use your personal preferences (type hints, docstrings, etc.).

### Tips

**Best Practices:**
1. ✅ Keep user config for personal preferences
2. ✅ Keep project config for project-specific context
3. ✅ Commit `.wyn360.yaml` to git (helps team)
4. ✅ Use project config to specify tech stack
5. ❌ Don't put API keys in config files
6. ❌ Don't make configs too verbose

**Pro Tips:**
- Use `/config` command to verify your settings
- Use project config for complex projects (5+ files)
- Update project context as your project evolves
- Share project config in README for team alignment

---

## Use Case 13: Streaming Responses

**Feature:** Real-time token-by-token streaming (v0.3.2)

**Problem:** Waiting for entire responses can feel slow, especially for long code generations or explanations. Users want immediate feedback.

**Solution:** WYN360 now streams responses token-by-token as they're generated, providing instant visual feedback and a more responsive experience.

### Before Streaming (Old Behavior)

```
You: Generate a large Python script for data analysis

[Spinner animation for 10-15 seconds]

WYN360: [Entire response appears at once after waiting]
```

**User Experience:**
- ❌ Long wait with no feedback
- ❌ Feels slow and unresponsive
- ❌ Can't see progress
- ❌ Can't start reading early parts

### After Streaming (New Behavior)

```
You: Generate a large Python script for data analysis

WYN360: I'll create a comprehensive data analysis script...

[Text appears word-by-word as it's generated]

Let me build this step by step:

1. First, import the necessary libraries:
```python
import pandas as pd
...
```

**User Experience:**
- ✅ Immediate feedback
- ✅ Feels fast and responsive
- ✅ See progress in real-time
- ✅ Start reading while streaming

### Benefits

**1. Faster Perceived Response Time**
- Even though total time is the same, streaming feels much faster
- Immediate feedback creates sense of progress
- Similar to ChatGPT's streaming experience

**2. Better UX for Long Responses**
- Start reading documentation while it generates
- Review code as it appears
- Understand context before completion

**3. Transparency**
- See exactly what the AI is generating
- Can stop if going in wrong direction
- Better sense of AI "thinking" process

### Example Workflows

#### Workflow 1: Long Code Generation

```
You: Create a FastAPI application with authentication, database models,
     and CRUD endpoints for a blog system

WYN360: I'll create a complete FastAPI blog application...

Let me structure this into several files:

1. **app/main.py** - Main application entry point
```python
from fastapi import FastAPI, Depends
from fastapi.security import OAuth2PasswordBearer
...
[Code streams in real-time]
```

2. **app/models.py** - Database models
...
[Continues streaming]
```

**Experience:** You can start reading the main.py code while models.py is still being generated.

#### Workflow 2: Documentation and Explanations

```
You: Explain how asyncio works in Python with examples

WYN360: Asyncio is Python's library for writing concurrent code...

[Explanation streams word-by-word]

Here's how it works:

1. **Event Loop**: The core of asyncio...
2. **Coroutines**: Functions defined with async def...
3. **Tasks**: Wrapped coroutines that run concurrently...

[You can read section 1 while sections 2-3 are still generating]
```

#### Workflow 3: Large Script Generation

**Before (Non-Streaming):**
```
You: Generate a comprehensive data pipeline script

[Wait 15 seconds with spinner]

WYN360: [500 lines of code appear instantly]
[Overwhelming - hard to parse all at once]
```

**After (Streaming):**
```
You: Generate a comprehensive data pipeline script

WYN360: I'll create a data pipeline with these components:
[Starts streaming immediately]

# Step 1: Data ingestion
[Code appears line-by-line]

# Step 2: Data transformation
[Code continues streaming]

# Step 3: Data validation
[More code streams in]

[You're already reading Step 1 while Step 3 is being generated]
```

### Technical Details

**How It Works:**
- Uses pydantic-ai's streaming API
- Tokens are yielded as they're generated by Claude
- Rich console displays them immediately
- Full response is accumulated for history

**Performance:**
- **No slowdown**: Streaming adds no latency
- **Same total time**: Response completes at same time
- **Better perception**: Feels 2-3x faster due to immediate feedback

### Comparison

| Aspect | Non-Streaming | Streaming |
|--------|--------------|-----------|
| **First Token** | 10-15s wait | Instant |
| **Perceived Speed** | Slow | Fast |
| **Reading Start** | After completion | Immediately |
| **Progress Feedback** | None | Real-time |
| **User Experience** | Waiting | Engaging |

### Use Cases Where Streaming Shines

**1. Documentation Generation**
```
You: Document this module with detailed docstrings

WYN360: [Streams documentation as it writes]
# You can read early functions while later ones generate
```

**2. Code Refactoring**
```
You: Refactor this 500-line script

WYN360: [Shows refactored code streaming]
# Review changes as they happen, not all at once
```

**3. Explanations and Tutorials**
```
You: Explain design patterns with examples

WYN360: [Explanation streams naturally]
# Read and understand each pattern before next one generates
```

**4. Large File Generation**
```
You: Create a complete API client with all endpoints

WYN360: [Streams code file by file]
# Start planning implementation while rest generates
```

### Tips

**Pro Tips:**
- Streaming is automatic - no configuration needed
- Works for all response types (code, text, explanations)
- Conversation history is preserved normally
- Same quality as non-streaming responses

---

## 15. Performance Monitoring & Analytics

Monitor your CLI usage, response times, tool efficiency, and identify performance bottlenecks with comprehensive metrics tracking.

### What is Performance Monitoring?

WYN360 automatically tracks and analyzes session performance, providing insights into:
- **Response Times**: How fast the AI responds to your requests
- **Tool Usage**: Which tools you use most and their success rates
- **Error Tracking**: What errors occur and how frequently
- **Session Statistics**: Overall session duration and activity

### The /stats Command

View comprehensive performance metrics at any time during your session:

```
You: /stats

┏━━━━━━━━━━━━━━━━━━━━━━┓  ┏━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃   Token Usage        ┃  ┃   Performance Metrics   ┃
┣━━━━━━━━━━━━━━━━━━━━━━┫  ┣━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ Total Requests: 25   ┃  ┃ Session Duration: 15m   ┃
┃ Input Tokens: 45,230 ┃  ┃ Avg Response: 2.3s     ┃
┃ Output Tokens: 12,450┃  ┃ Min Response: 0.8s     ┃
┃ Total Cost: $0.32    ┃  ┃ Max Response: 5.2s     ┃
┗━━━━━━━━━━━━━━━━━━━━━━┛  ┃ Error Count: 0         ┃
                          ┗━━━━━━━━━━━━━━━━━━━━━━━━━┛

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃      Tool Usage            ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ Total Tool Calls: 47       ┃
┃ Successful Calls: 45       ┃
┃ Failed Calls: 2            ┃
┃ Success Rate: 95.7%        ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃      Most Used Tools          ┃
┣━━━━━━━━━━━┳━━━━━━━┳━━━━━━┳━━━━━┫
┃ Tool      ┃Success┃Failed┃Total┃
┣━━━━━━━━━━━╋━━━━━━━╋━━━━━━╋━━━━━┫
┃ read_file ┃  15   ┃  0   ┃ 15  ┃
┃write_file ┃  12   ┃  1   ┃ 13  ┃
┃execute_cmd┃   8   ┃  0   ┃  8  ┃
┃search_files┃  5   ┃  0   ┃  5  ┃
┃git_status ┃   5   ┃  1   ┃  6  ┃
┗━━━━━━━━━━━┻━━━━━━━┻━━━━━━┻━━━━━┛
```

### Use Case 1: Identifying Slow Operations

**Scenario:** You notice your session feels slow sometimes

```
You: /stats

WYN360: [Shows metrics]
- Avg Response: 4.5s
- Max Response: 15.2s  ← Outlier detected!

You: What took 15 seconds?

WYN360: Looking at your session history, the slowest
operation was "Generate comprehensive ML pipeline" which
generated 800+ lines of code. Consider breaking large
requests into smaller chunks for faster responses.
```

**Insight:** Large code generation requests take longer. Break them into smaller, focused tasks.

### Use Case 2: Tool Success Rate Analysis

**Scenario:** Want to see which operations are failing

```
You: /stats

WYN360: [Shows tool usage]
Tool Success Rates:
- read_file: 100% (15/15)
- write_file: 92.3% (12/13)  ← 1 failure
- execute_command: 100% (8/8)
- git_status: 83.3% (5/6)    ← 1 failure

You: Why did write_file fail once?

WYN360: The write_file failure was due to attempting
to write without overwrite=True when the file already
existed. This was corrected in the retry.
```

**Insight:** Understand which operations need error handling or user confirmation.

### Use Case 3: Session Cost Monitoring

**Scenario:** Track spending during a long coding session

```
You: I've been working for 2 hours. How much have I spent?

You: /stats

WYN360: [Shows combined token + performance metrics]
Session Duration: 2h 15m
Total Requests: 47
Total Cost: $1.23
Average Cost per Request: $0.026

Most expensive operations:
1. Multi-file refactoring: $0.15
2. Test generation: $0.12
3. Documentation creation: $0.09
```

**Insight:** Monitor costs in real-time, identify expensive operations, optimize usage.

### Use Case 4: Error Tracking & Debugging

**Scenario:** Encountering errors and want to understand patterns

```
You: /stats

WYN360: [Shows error summary]
Error Count: 3
Error Types:
- FileNotFoundError: 2
- ValueError: 1

Recent errors:
1. FileNotFoundError: "config.yaml not found" (2x)
2. ValueError: "Invalid JSON format"

You: Create config.yaml with default settings

WYN360: ✓ Created config.yaml
Now future runs won't encounter FileNotFoundError
```

**Insight:** Identify recurring errors and fix root causes.

### Use Case 5: Performance Benchmarking

**Scenario:** Compare different models or approaches

```
# Session 1 with Haiku (fast model)
You: /stats
Avg Response: 1.2s
Total Cost: $0.15

# Session 2 with Sonnet (balanced model)
You: /stats
Avg Response: 2.3s
Total Cost: $0.42

# Session 3 with Opus (powerful model)
You: /stats
Avg Response: 4.1s
Total Cost: $1.25
```

**Insight:** Choose the right model for your use case - speed vs. capability vs. cost.

### Features

**Automatic Tracking:**
- ✅ Response times tracked for every request
- ✅ Tool calls logged with success/failure status
- ✅ Errors captured with type and message
- ✅ Session duration calculated automatically

**Persistent Metrics:**
- ✅ Metrics saved with /save command
- ✅ Loaded with /load command
- ✅ Track performance across multiple sessions

**Zero Configuration:**
- ✅ Works automatically - no setup required
- ✅ Non-intrusive - runs in background
- ✅ No performance overhead
- ✅ Compatible with all existing features

### Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `/stats` | Show comprehensive performance metrics | `You: /stats` |
| `/tokens` | Show only token usage (legacy) | `You: /tokens` |
| `/clear` | Reset all metrics and history | `You: /clear` |

### Tips for Optimization

**1. Monitor Long-Running Sessions**
```bash
# Check metrics periodically during long sessions
You: /stats
# If avg response time > 5s, consider:
# - Breaking large requests into smaller ones
# - Switching to faster model (haiku)
# - Clearing conversation history
```

**2. Track Tool Efficiency**
```bash
# If tool success rate < 90%, investigate:
# - Are file paths correct?
# - Do required files exist?
# - Are permissions set properly?
```

**3. Cost Management**
```bash
# Set personal budget limits
# Check /stats before expensive operations
# Use haiku for simple tasks, sonnet for complex
```

**4. Identify Bottlenecks**
```bash
# Look at "Most Used Tools"
# If one tool dominates, consider:
# - Batch operations
# - Cache results
# - Optimize workflow
```

### Real-World Workflow Example

**Scenario:** Building a web scraper project

```
# Start session
You: Create a web scraper for news articles

# After 30 minutes of work
You: /stats

WYN360:
Session Duration: 32m
Total Requests: 18
Avg Response: 2.1s
Total Cost: $0.45

Most Used Tools:
- write_file: 8 times (100% success)
- read_file: 6 times (100% success)
- execute_command: 4 times (75% success)  ← Attention needed

You: Why did execute_command fail?

WYN360: One pip install failed due to network timeout.
Retried successfully. No action needed.

# Continue working...

# End of session
You: /stats

WYN360:
Final Session Stats:
Duration: 1h 15m
Requests: 35
Cost: $0.87
Success Rate: 97.1%

You: /save scraper_session.json
WYN360: ✓ Session saved (including performance metrics)
```

**Result:** Complete project visibility, cost tracking, and session replay capability.

### Technical Details

**What's Tracked:**
- Request timestamps and durations
- Tool invocation counts (success/failure)
- Error occurrences with stack traces
- Token usage per request
- Model information

**Storage:**
- In-memory during session
- Persisted to JSON with /save
- Loaded from JSON with /load
- Zero database dependencies

**Performance:**
- Negligible overhead (< 0.1ms per operation)
- Asynchronous tracking
- Memory efficient
- No blocking operations

---

## 16. Web Search - Real-Time Information Access

**Phase:** 11.1
**Version:** 0.3.21, Enhanced in 0.3.23
**Feature:** Real-time web search using Claude's native web_search_20250305 tool

### Overview

WYN360 now has access to real-time web search capabilities! This feature enables the AI assistant to fetch current information from the internet, including weather data, website content, latest documentation, and **finding GitHub repositories and libraries** (enhanced in v0.3.23). The web search tool is integrated via pydantic-ai's `WebSearchTool` builtin and is configured with cost controls (5 searches per session max, $10 per 1,000 searches).

**v0.3.23 Enhancements:**
- ⬆️ Upgraded from pydantic-ai 0.0.19 to 1.13.0 for improved stability
- 🔧 Fixed web search tool integration with proper `builtin_tools` configuration
- 📝 Enhanced system prompt with explicit examples for finding resources
- ✅ Now properly recognizes queries like "find a popular GitHub repo for X"

### Key Features

- 🌤️ **Weather Queries** - Get current weather for any location
- 🌐 **Website Reading** - Fetch and summarize web content
- 📚 **Current Information** - Access latest docs, news, and trends
- 🔍 **Resource Finding** - Find GitHub repos, libraries, and tutorials **(NEW in v0.3.23)**
- 💰 **Cost Controlled** - Limited to 5 searches per session by default
- 🔗 **Proper Citations** - All results include source URLs
- 🤖 **Automatic Invocation** - Claude decides when web search is needed

### Use Case 16.1: Weather Queries

Get real-time weather information for any location.

**User Interaction:**
```
You: What's the weather in San Francisco?

WYN360: [Searches web for current San Francisco weather]

Current Weather in San Francisco, CA:
- Temperature: 62°F (17°C)
- Conditions: Partly Cloudy
- Humidity: 71%
- Wind: 10 mph NW
- Last Updated: 2025-01-10 14:30 PST

Source: [Weather.com](https://weather.com/weather/today/l/San+Francisco+CA)
```

**If Location Not Provided:**
```
You: What's the weather?

WYN360: I'd be happy to check the weather for you! Could you please tell me which location you'd like to know about?

You: Boston

WYN360: [Searches web for Boston weather]

Current Weather in Boston, MA:
- Temperature: 28°F (-2°C)
- Conditions: Light Snow
- Humidity: 85%
- Wind: 15 mph NE
- Last Updated: 2025-01-10 14:30 EST

Source: [Weather.com](https://weather.com/weather/today/l/Boston+MA)
```

**How It Works:**
1. User asks for weather information
2. If location is missing, WYN360 asks for it
3. Web search tool fetches current weather data
4. Results displayed with source citation
5. Information includes temperature, conditions, and more

**Cost:**
- 1 search per query ($0.01)
- Plus token costs for input/output (~$0.001-0.003)
- Total: ~$0.011-0.013 per weather query

### Use Case 16.2: Website Reading & Summarization

Fetch and summarize content from any publicly accessible URL.

**User Interaction:**
```
You: Read this article: https://python.org/downloads/release/python-3130/

WYN360: [Fetches content from python.org]

**Python 3.13.0 Release Summary:**

**Key Highlights:**
1. **Performance Improvements:**
   - Free-threaded CPython (no GIL) - experimental
   - JIT compiler - experimental
   - 5-10% performance boost in most workloads

2. **New Features:**
   - Enhanced error messages with better tracebacks
   - Improved type hinting capabilities
   - New syntax for generic type parameters
   - Enhanced asyncio performance

3. **Standard Library Updates:**
   - New modules: `dbm.sqlite3`
   - Improved `pathlib` functionality
   - Enhanced `argparse` features

4. **Deprecations & Removals:**
   - Removed various deprecated features from 3.10
   - Updated minimum supported platforms

**Release Date:** October 2024
**Status:** Stable Release

**Important Notes:**
- Free-threading and JIT are experimental and opt-in
- Recommended for production use after thorough testing
- Migration guide available for deprecated features

Source: [Python.org](https://python.org/downloads/release/python-3130/)
(Last updated: 2024-10-07)
```

**Another Example:**
```
You: What does this page say? https://fastapi.tiangolo.com/

WYN360: [Fetches FastAPI homepage]

**FastAPI Framework Overview:**

FastAPI is a modern, high-performance web framework for building APIs with Python 3.8+ based on standard Python type hints.

**Key Features:**
- **Fast:** Very high performance, on par with NodeJS and Go
- **Fast to code:** Increase development speed by 200-300%
- **Fewer bugs:** Reduce about 40% of human errors
- **Intuitive:** Great editor support with auto-completion
- **Easy:** Designed to be easy to use and learn
- **Short:** Minimize code duplication
- **Robust:** Production-ready code with automatic docs
- **Standards-based:** Based on OpenAPI and JSON Schema

**Core Technologies:**
- Starlette for web parts
- Pydantic for data validation
- Python type hints for everything

**Use Cases:**
- RESTful APIs
- GraphQL APIs
- WebSockets
- Background tasks
- Dependency injection

Source: [FastAPI Documentation](https://fastapi.tiangolo.com/)
```

**How It Works:**
1. User provides a URL to read
2. Web search tool fetches the page content
3. WYN360 analyzes and summarizes key information
4. Results presented with proper structure and citations
5. Source URL and last updated date included

**Cost:**
- 1 search per URL ($0.01)
- Token costs vary by page size (typically $0.003-0.010)
- Total: ~$0.013-0.020 per URL

### Use Case 16.3: Current Information & Latest Updates

Access the latest documentation, package versions, news, and trends.

**Example 1: Latest Package Information**
```
You: What's new in React 19?

WYN360: [Searches for React 19 release information]

**React 19 - Major Updates:**

**Release Date:** December 2024 (Beta available)

**Key New Features:**

1. **React Compiler:**
   - Automatic optimization of React code
   - No need for manual memoization in most cases
   - Significant performance improvements

2. **Actions:**
   - New API for handling form submissions
   - Built-in pending states
   - Optimistic updates support
   - Example: `useActionState()`, `useFormStatus()`

3. **Document Metadata:**
   - Built-in support for `<title>`, `<meta>` tags
   - No need for react-helmet or next/head
   - Simplified SEO management

4. **Asset Loading:**
   - New APIs: `preload()`, `preinit()`
   - Better control over resource loading
   - Improved performance

5. **Web Components:**
   - Full support for Web Components
   - Better interoperability

**Breaking Changes:**
- Removed deprecated APIs (componentWillMount, etc.)
- StrictMode changes
- Updated TypeScript types

**Migration Guide:**
Available at react.dev with automated codemod tools

Sources:
- [React Blog - React 19 Beta](https://react.dev/blog/2024/12/05/react-19)
- [React Docs - What's New](https://react.dev/learn/whats-new)
```

**Example 2: Security Information**
```
You: What are the latest security vulnerabilities in Node.js?

WYN360: [Searches for recent Node.js security advisories]

**Node.js Security Updates (January 2025):**

**Critical Vulnerabilities:**

1. **CVE-2025-XXXX - HTTP Request Smuggling**
   - Severity: High (7.5 CVSS)
   - Affected: Node.js 18.x, 20.x, 21.x
   - Fixed in: 18.19.1, 20.11.1, 21.6.2
   - Impact: Allows attackers to bypass security controls
   - Recommendation: Update immediately

2. **CVE-2025-YYYY - OpenSSL Vulnerability**
   - Severity: Medium (5.9 CVSS)
   - Affected: All versions using OpenSSL 3.x
   - Fixed in: Latest versions
   - Impact: Potential denial of service
   - Recommendation: Update to patched versions

**Recommended Actions:**
1. Update to latest LTS versions (18.19.1+ or 20.11.1+)
2. Review security best practices
3. Enable security audit in CI/CD
4. Run `npm audit` to check dependencies

Sources:
- [Node.js Security Releases](https://nodejs.org/en/blog/vulnerability/)
- [GitHub Security Advisories](https://github.com/nodejs/node/security/advisories)
```

**Example 3: Best Practices Research**
```
You: What are current best practices for FastAPI deployment?

WYN360: [Searches for FastAPI deployment best practices]

**FastAPI Deployment Best Practices (2025):**

**Production Server:**
- **Recommended:** Uvicorn with Gunicorn workers
- **Configuration:**
  ```bash
  gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
  ```

**Docker Deployment:**
- Use official Python slim images
- Multi-stage builds for smaller images
- Non-root user for security
- Example: tiangolo/uvicorn-gunicorn-fastapi image

**Key Recommendations:**

1. **Performance:**
   - Enable HTTP/2 support
   - Use async database drivers (asyncpg, motor)
   - Implement caching (Redis, Memcached)
   - Enable GZIP compression

2. **Security:**
   - HTTPS only (Let's Encrypt for free certs)
   - CORS configuration
   - Rate limiting (slowapi library)
   - Input validation with Pydantic
   - Security headers (fastapi-security)

3. **Monitoring:**
   - Prometheus for metrics
   - Sentry for error tracking
   - Structured logging
   - Health check endpoints

4. **Scaling:**
   - Horizontal scaling with load balancer
   - Kubernetes for orchestration
   - Cloud platforms: AWS ECS, Google Cloud Run, Azure Container Apps

5. **Database:**
   - Use connection pooling
   - Implement database migrations (Alembic)
   - Read replicas for scaling reads

**Cloud Platforms:**
- AWS: ECS, Lambda (Mangum adapter), Elastic Beanstalk
- Google Cloud: Cloud Run, App Engine
- Azure: Container Apps, App Service
- Heroku: Simple deployment with Procfile

Sources:
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
- [Uvicorn Deployment](https://www.uvicorn.org/deployment/)
- [Best Practices Blog Posts - 2024/2025]
```

**How It Works:**
1. User asks about current information or latest updates
2. Web search fetches recent articles, documentation, or news
3. WYN360 synthesizes information from multiple sources
4. Results presented with structure, citations, and dates
5. Recommendations and best practices highlighted

**Cost:**
- 1-2 searches per query ($0.01-0.02)
- Token costs for synthesis (~$0.005-0.015)
- Total: ~$0.015-0.035 per information query

### Use Case 16.4: Finding Resources & GitHub Repositories **(NEW in v0.3.23)**

Find popular GitHub repositories, libraries, tools, and learning resources based on specific topics or technologies.

**User Interaction:**
```
You: Find a popular GitHub repo for machine learning

WYN360: [Searches web for popular ML repositories]

Here are some of the most popular GitHub repositories for machine learning:

1. **tensorflow/tensorflow** ⭐ 185,000+ stars
   https://github.com/tensorflow/tensorflow
   - End-to-end open source machine learning platform
   - Developed and maintained by Google
   - Comprehensive ecosystem for model development and deployment
   - Supports neural networks, deep learning, and production ML

2. **pytorch/pytorch** ⭐ 82,000+ stars
   https://github.com/pytorch/pytorch
   - Deep learning framework by Meta AI (Facebook)
   - Dynamic computational graphs (imperative programming)
   - Popular in research and academic communities
   - Excellent for prototyping and experimentation

3. **scikit-learn/scikit-learn** ⭐ 59,000+ stars
   https://github.com/scikit-learn/scikit-learn
   - Classic machine learning library for Python
   - Built on NumPy, SciPy, and matplotlib
   - Great for traditional ML algorithms (not deep learning)
   - Excellent documentation and beginner-friendly

4. **keras-team/keras** ⭐ 61,000+ stars
   https://github.com/keras-team/keras
   - High-level neural networks API
   - Runs on top of TensorFlow
   - User-friendly and modular
   - Perfect for quick prototyping

**Recommendation for Beginners:** Start with scikit-learn for traditional ML, then move to TensorFlow or PyTorch for deep learning.

Sources:
- [GitHub Search Results - Most Stars in ML category]
- [GitHub Trending - Machine Learning]
(Last updated: December 2025)
```

**Finding Libraries by Language:**
```
You: What are good Python libraries for data visualization?

WYN360: [Searches for Python data viz libraries]

Top Python libraries for data visualization:

1. **Matplotlib** ⭐ 19,500+ stars
   - Standard plotting library, similar to MATLAB
   - Highly customizable, extensive documentation
   - Best for: Static plots, scientific visualizations

2. **Plotly** ⭐ 16,000+ stars
   - Interactive web-based visualizations
   - Dash framework for dashboards
   - Best for: Interactive charts, web apps, dashboards

3. **Seaborn** ⭐ 12,000+ stars
   - Built on matplotlib, statistical focus
   - Beautiful default styles
   - Best for: Statistical analysis, heatmaps, distributions

4. **Bokeh** ⭐ 19,000+ stars
   - Interactive visualizations for web browsers
   - Real-time streaming and big data
   - Best for: Interactive web apps, large datasets

Sources: GitHub, Python Package Index, Stack Overflow trends
```

**Finding Tutorials:**
```
You: Find tutorials for FastAPI

WYN360: [Searches for FastAPI tutorials]

Top FastAPI Learning Resources:

**Official Documentation:**
- FastAPI Tutorial - https://fastapi.tiangolo.com/tutorial/
  Comprehensive, step-by-step guide by the creator

**GitHub Repositories:**
- awesome-fastapi/awesome-fastapi ⭐ 7,500+ stars
  Curated list of FastAPI resources, projects, and tutorials

**Tutorial Series:**
- "FastAPI - The Complete Course" (GitHub: codingforentrepreneurs)
- Real-world examples with authentication, databases, testing

**Video Tutorials:**
- FreeCodeCamp FastAPI full course (YouTube)
- Traversy Media FastAPI crash course

Sources: GitHub, FastAPI documentation, YouTube, Dev.to
```

**How It Works:**
1. User asks to find repositories, libraries, or learning resources
2. Web search queries GitHub, package registries, and tech communities
3. Results ranked by popularity (stars, downloads, community activity)
4. Provides URLs, descriptions, star counts, and recommendations
5. Includes comparisons and use case suggestions

**What You Can Find:**
- ✅ GitHub repositories by topic ("find repos for X")
- ✅ Python/JS/Go libraries ("best libraries for Y")
- ✅ Learning resources ("tutorials for Z")
- ✅ Tools and frameworks ("tools for web scraping")
- ✅ Code examples ("example projects using A")

**Cost:**
- 1-2 searches per query ($0.01-0.02)
- Token costs for formatting (~$0.005-0.010)
- Total: ~$0.015-0.030 per resource search

### When Web Search is Used

**WILL Use Web Search:**
- ✅ Weather queries ("What's the weather in NYC?")
- ✅ Reading URLs ("Read https://example.com")
- ✅ **Finding resources** ("Find a popular GitHub repo for machine learning") **(NEW v0.3.23)**
- ✅ **Library recommendations** ("What are good Python data viz libraries?") **(NEW v0.3.23)**
- ✅ **Tutorial finding** ("Find tutorials for FastAPI") **(NEW v0.3.23)**
- ✅ Current information ("What's new in Python 3.13?")
- ✅ Latest versions ("Latest React features")
- ✅ Recent news ("Recent security vulnerabilities")
- ✅ Real-time data ("Current stock price of...")
- ✅ Best practices research ("Current FastAPI deployment practices")

**WILL NOT Use Web Search:**
- ❌ Code generation ("Write a FastAPI app")
- ❌ File operations ("Show me app.py")
- ❌ Local project queries ("List files in this project")
- ❌ Git operations ("Show git status")
- ❌ General programming concepts ("What is async/await?")
- ❌ Existing knowledge ("How to use Python decorators?")

### Cost Analysis

**Pricing:**
- **Web Search Cost:** $10.00 per 1,000 searches
- **Token Costs:** Standard model pricing ($3/$15 per M tokens for Sonnet)
- **Session Limit:** 5 searches per session (configurable)

**Example Costs:**

| Query Type | Searches | Token Cost | Total Cost |
|-----------|----------|------------|------------|
| Weather | 1 | $0.001-0.003 | $0.011-0.013 |
| URL Reading | 1 | $0.003-0.010 | $0.013-0.020 |
| Latest Info | 1-2 | $0.005-0.015 | $0.015-0.035 |

**Session Example:**
```
- 2 weather queries: $0.026
- 1 URL read: $0.015
- 2 info searches: $0.050
Total: ~$0.091 per session
```

**Monthly Estimate (heavy use):**
- 10 sessions/day × 30 days = 300 sessions
- Average 3 searches per session = 900 searches
- Cost: (900 × $0.01) + token costs ≈ $9-15/month

### Configuration

**Default Settings:**
```python
# In agent.py
builtin_tools=[
    WebSearchTool(max_uses=5)  # Limit searches per session
]
```

**Adjustable Parameters:**
- `max_uses`: Maximum searches per session (default: 5)
- `search_context_size`: How much context to include
- `user_location`: Default location for queries
- `blocked_domains`: Sites to exclude
- `allowed_domains`: Sites to include only

### Technical Implementation

**Integration Method:**
```python
from pydantic_ai import Agent, WebSearchTool

agent = Agent(
    model="claude-sonnet-4",
    builtin_tools=[WebSearchTool(max_uses=5)]
)
```

**Key Points:**
- Uses Claude's native `web_search_20250305` tool
- Integrated via pydantic-ai framework
- Separate from custom @tool decorated functions
- Works alongside 19 existing custom tools
- No conflicts with file operations or git tools

### Best Practices

**For Users:**
1. **Be Specific:** Provide clear locations for weather ("San Francisco" not just "weather")
2. **Full URLs:** Provide complete URLs for reading ("https://..." not just "python.org")
3. **Recent Focus:** Use for current info, not general knowledge
4. **Cost Aware:** Remember search limits (5 per session by default)

**For Developers:**
1. **Adjust Limits:** Increase `max_uses` for high-volume use cases
2. **Filter Domains:** Use `allowed_domains` for trusted sources only
3. **Monitor Costs:** Track search usage with `/stats` command
4. **Combine Tools:** Use with `read_file` for comparing local vs online docs

### Troubleshooting

**Issue: Search limit reached**
```
Error: Maximum web searches (5) reached for this session
```
**Solution:** Start a new session or adjust `max_uses` in code

**Issue: No results found**
```
No relevant results found for query: [your query]
```
**Solution:** Rephrase query with more specific terms

**Issue: URL not accessible**
```
Error: Could not fetch content from URL
```
**Solution:** Check URL is publicly accessible, not behind authentication

### Performance

**Response Times:**
- Weather query: 1-3 seconds
- URL reading: 2-5 seconds (depends on page size)
- Information search: 1-4 seconds

**Accuracy:**
- Real-time data: 100% current (as of search time)
- Source citations: Always included
- Confidence: Based on source reliability

**Limitations:**
- Cannot access authenticated sites
- Cannot bypass paywalls
- Limited to publicly available content
- Session limit prevents excessive searches

---

## 17. GitHub Integration - Complete Git Workflow Management

**Phase:** 8.1
**Version:** 0.3.23
**Feature:** Complete GitHub integration with commit, PR creation, and branch management

### Overview

WYN360 now provides seamless GitHub integration directly from the CLI! This feature enables complete git workflow management including committing changes, creating pull requests, managing branches, and merging code. All operations use the GitHub CLI (gh) for reliable interactions with GitHub's API, with built-in authentication and user confirmation for safety.

### Key Features

- 🔐 **GitHub Authentication** - Token-based authentication with GH_TOKEN/GITHUB_TOKEN
- 💾 **Commit & Push** - Stage, commit, and push changes directly from CLI
- 🔀 **Pull Requests** - Create PRs with title, body, and base branch
- 🌿 **Branch Management** - Create, checkout, and list branches
- 🔄 **Branch Merging** - Merge branches with conflict detection
- 🔒 **User Confirmation** - All git operations require y/N approval
- ✅ **Auto-Authentication** - Automatically uses environment token if found
- 🎯 **Session Persistence** - Token stored in environment across session

### Use Case 17.1: Commit and Push Changes

Commit your changes to the current repository and push to GitHub with a single command.

**User Interaction:**
```
You: Commit these changes

WYN360: [Checks GitHub authentication]

Let me check your GitHub authentication first...

✓ Authenticated with GitHub as 'yiqiao-yin'

I'll now commit your changes. Let me check what's been modified:

[Runs git status]
Changes to be committed:
  modified:   agent.py
  modified:   USE_CASES.md
  new file:   tests/test_github.py

[Runs git add -A to stage all changes]

======================================================================
⚠️  COMMAND EXECUTION CONFIRMATION
======================================================================
Command: git commit -m "Add GitHub integration tools"
Directory: /home/workbench/wyn360-cli/wyn360-cli
Permissions: Full user permissions
======================================================================

>>> WAITING FOR YOUR RESPONSE <<<

Execute this command? (y/N): y

✅ Command executed successfully (exit code 0)

Commit created: a1b2c3d
Author: Yiqiao Yin <yiqiao.yin@wyn-associates.com>
Message: Add GitHub integration tools

Now pushing to remote...

======================================================================
⚠️  COMMAND EXECUTION CONFIRMATION
======================================================================
Command: git push origin main
Directory: /home/workbench/wyn360-cli/wyn360-cli
Permissions: Full user permissions
======================================================================

>>> WAITING FOR YOUR RESPONSE <<<

Execute this command? (y/N): y

✅ Command executed successfully (exit code 0)

✓ Successfully committed and pushed changes to GitHub!
```

**If Not Authenticated:**
```
You: Commit to github

WYN360: [Checks authentication]

Not authenticated with GitHub. To use GitHub features, I need your access token.

To get a GitHub token:
1. Visit: https://github.com/settings/tokens/new
2. Generate a Personal Access Token with 'repo' and 'workflow' scopes
3. Copy the token (format: ghp_... or github_pat_...)

Please provide your GitHub token (it will be stored in GH_TOKEN environment variable):

You: ghp_abc123xyz789...

WYN360: [Authenticates]

======================================================================
⚠️  COMMAND EXECUTION CONFIRMATION
======================================================================
Command: echo 'ghp_abc123xyz789...' | gh auth login --with-token
Directory: /home/workbench/wyn360-cli/wyn360-cli
Permissions: Full user permissions
======================================================================

>>> WAITING FOR YOUR RESPONSE <<<

Execute this command? (y/N): y

✅ Command executed successfully (exit code 0)

✓ Authenticated with GitHub (auto-authenticated using provided token)

Now let me commit your changes...

[Proceeds with commit workflow as shown above]
```

**How It Works:**
1. User requests to commit changes
2. Agent checks GitHub authentication status (one time per session)
3. If not authenticated, asks for token and authenticates
4. Stages all changes with git add -A
5. Commits with user-provided or generated message
6. Optionally pushes to remote (default: yes)
7. Shows commit SHA and confirmation

**Cost:**
- Authentication check: ~$0.001-0.003
- Commit workflow: ~$0.005-0.010
- Total: ~$0.006-0.013 per commit operation

### Use Case 17.2: Create Pull Request

Open a pull request from your current branch to the main branch with a single command.

**User Interaction:**
```
You: Create a pull request for my feature

WYN360: [Checks authentication - already authenticated this session]

✓ Authenticated with GitHub as 'yiqiao-yin'

Let me gather information about your branch...

[Runs git branch --show-current]
Current branch: feature/github-integration

[Runs git diff main...feature/github-integration]
Changes include:
- agent.py: +150 lines (7 new tools)
- SYSTEM.md: +75 lines (architecture updates)
- USE_CASES.md: +200 lines (documentation)

I'll create a pull request with the following details:

**Title:** Add GitHub Integration Tools (Phase 8.1)

**Body:**
This PR implements Phase 8.1 - GitHub Integration with 7 new tools:

## Changes
- ✅ GitHub authentication (check_gh_authentication, authenticate_gh)
- ✅ Commit and push (gh_commit_changes)
- ✅ Create PRs (gh_create_pr)
- ✅ Branch management (gh_create_branch, gh_checkout_branch)
- ✅ Branch merging (gh_merge_branch)

## Documentation
- Updated SYSTEM.md with GitHub integration layer
- Added Section 17 to USE_CASES.md
- Updated system prompt with GitHub workflow

## Testing
- Unit tests to be added in next commit

**Base branch:** main

======================================================================
⚠️  COMMAND EXECUTION CONFIRMATION
======================================================================
Command: gh pr create --title "Add GitHub Integration Tools (Phase 8.1)" \
         --base main --body "..."
Directory: /home/workbench/wyn360-cli/wyn360-cli
Permissions: Full user permissions
======================================================================

>>> WAITING FOR YOUR RESPONSE <<<

Execute this command? (y/N): y

✅ Command executed successfully (exit code 0)

✓ Successfully created pull request!

PR URL: https://github.com/yiqiao-yin/wyn360-cli/pull/42
Title: Add GitHub Integration Tools (Phase 8.1)
Base: main ← feature/github-integration
Status: Open

View or merge at: https://github.com/yiqiao-yin/wyn360-cli/pull/42
```

**Custom PR with User Input:**
```
You: Create PR titled "Fix authentication bug" with body "Fixes #123"

WYN360: [Authentication already verified]

Current branch: bugfix/auth-loop
Target branch: main (default)

======================================================================
⚠️  COMMAND EXECUTION CONFIRMATION
======================================================================
Command: gh pr create --title "Fix authentication bug" \
         --base main --body "Fixes #123"
Directory: /home/workbench/wyn360-cli/wyn360-cli
Permissions: Full user permissions
======================================================================

>>> WAITING FOR YOUR RESPONSE <<<

Execute this command? (y/N): y

✅ Command executed successfully (exit code 0)

✓ Successfully created pull request!

PR URL: https://github.com/yiqiao-yin/wyn360-cli/pull/43
Title: Fix authentication bug
Base: main ← bugfix/auth-loop
Status: Open
```

**How It Works:**
1. User requests PR creation
2. Agent checks current branch (must not be main/master)
3. Optionally analyzes changes with git diff
4. Generates or uses user-provided title and body
5. Creates PR using gh pr create command
6. Returns PR URL for immediate access

**Cost:**
- PR creation workflow: ~$0.010-0.020
- With change analysis: ~$0.015-0.030
- Total: ~$0.010-0.030 per PR

### Use Case 17.3: Branch Management (Create & Checkout)

Create new branches and switch between them seamlessly.

**Create New Branch:**
```
You: Create a new branch called feature/auth

WYN360: I'll create a new branch 'feature/auth' and check it out.

======================================================================
⚠️  COMMAND EXECUTION CONFIRMATION
======================================================================
Command: git checkout -b feature/auth
Directory: /home/workbench/wyn360-cli/wyn360-cli
Permissions: Full user permissions
======================================================================

>>> WAITING FOR YOUR RESPONSE <<<

Execute this command? (y/N): y

✅ Command executed successfully (exit code 0)

✓ Successfully created and checked out branch 'feature/auth'

Current branch: feature/auth
Base commit: a1b2c3d (from main)

You can now make changes on this branch. When ready:
- Commit: "commit these changes"
- Push: "push to github"
- PR: "create pull request"
```

**Create Without Checkout:**
```
You: Create branch bugfix/typo but don't switch to it

WYN360: I'll create the branch 'bugfix/typo' without checking it out.

======================================================================
⚠️  COMMAND EXECUTION CONFIRMATION
======================================================================
Command: git branch bugfix/typo
Directory: /home/workbench/wyn360-cli/wyn360-cli
Permissions: Full user permissions
======================================================================

>>> WAITING FOR YOUR RESPONSE <<<

Execute this command? (y/N): y

✅ Command executed successfully (exit code 0)

✓ Successfully created branch 'bugfix/typo'

Current branch: main (unchanged)
New branch: bugfix/typo (created but not checked out)

To switch to it later: "checkout bugfix/typo"
```

**Checkout Existing Branch:**
```
You: Switch to the develop branch

WYN360: I'll check out the 'develop' branch.

[First checks if branch exists with git branch]
Branch 'develop' exists.

======================================================================
⚠️  COMMAND EXECUTION CONFIRMATION
======================================================================
Command: git checkout develop
Directory: /home/workbench/wyn360-cli/wyn360-cli
Permissions: Full user permissions
======================================================================

>>> WAITING FOR YOUR RESPONSE <<<

Execute this command? (y/N): y

✅ Command executed successfully (exit code 0)

✓ Successfully checked out branch 'develop'

Previous branch: main
Current branch: develop
Last commit: x9y8z7 "Update documentation"
```

**Branch Doesn't Exist:**
```
You: Checkout feature/new-api

WYN360: [Checks for branch]

Branch 'feature/new-api' doesn't exist.

Would you like me to:
1. Create the branch and check it out? (create + checkout)
2. List all available branches?

You: Create and checkout

WYN360: [Proceeds with create + checkout workflow as shown above]
```

**How It Works:**
1. **Create Branch:**
   - Validates branch name format
   - Uses git checkout -b (create + checkout) or git branch (create only)
   - Confirms creation with current base commit

2. **Checkout Branch:**
   - Checks if branch exists first
   - If exists: switches with git checkout
   - If not: offers to create it
   - Shows previous and current branch

**Cost:**
- Branch creation: ~$0.003-0.008
- Branch checkout: ~$0.003-0.008
- Total: ~$0.003-0.008 per operation

### Use Case 17.4: Merge Branches

Merge feature branches into target branches with conflict detection.

**Successful Merge:**
```
You: Merge feature/auth into main

WYN360: I'll merge 'feature/auth' into 'main'.

[Checks current branch]
Current branch: main ✓

[Checks if source branch exists]
Source branch 'feature/auth' exists ✓

[Checks for uncommitted changes]
Working directory clean ✓

======================================================================
⚠️  COMMAND EXECUTION CONFIRMATION
======================================================================
Command: git merge feature/auth
Directory: /home/workbench/wyn360-cli/wyn360-cli
Permissions: Full user permissions
======================================================================

>>> WAITING FOR YOUR RESPONSE <<<

Execute this command? (y/N): y

✅ Command executed successfully (exit code 0)

✓ Successfully merged 'feature/auth' into 'main'

Merge type: Fast-forward
Files changed: 5
Insertions: +230 lines
Deletions: -15 lines

Changes:
  modified: agent.py (+150, -10)
  modified: SYSTEM.md (+45, -0)
  modified: USE_CASES.md (+30, -5)
  new file: tests/test_auth.py (+5, -0)

Next steps:
- Push to remote: "push to github"
- Create PR: "create pull request"
```

**Merge with Conflicts:**
```
You: Merge feature/conflicting into main

WYN360: I'll merge 'feature/conflicting' into 'main'.

[Pre-checks all pass]

======================================================================
⚠️  COMMAND EXECUTION CONFIRMATION
======================================================================
Command: git merge feature/conflicting
Directory: /home/workbench/wyn360-cli/wyn360-cli
Permissions: Full user permissions
======================================================================

>>> WAITING FOR YOUR RESPONSE <<<

Execute this command? (y/N): y

❌ Command failed (exit code 1)

⚠️ Merge conflict detected!

Conflicting files:
- agent.py (both modified)
- config.py (both modified)

The merge has been started but not completed. You need to:

1. Resolve conflicts in the files listed above
2. Stage resolved files: git add <file>
3. Complete the merge: git commit

Or abort the merge: git merge --abort

Would you like me to:
1. Show the conflicting sections?
2. Abort the merge?
3. Guide you through manual resolution?

You: Show conflicts

WYN360: [Reads conflicting files and shows conflict markers]

In agent.py (lines 150-160):
<<<<<<< HEAD
def authenticate_gh(self, token: str) -> str:
    # Current implementation
    return "authenticated"
=======
def authenticate_gh(self, token: str, force: bool = False) -> str:
    # New feature with force parameter
    return "force authenticated" if force else "authenticated"
>>>>>>> feature/conflicting

In config.py (lines 25-30):
<<<<<<< HEAD
GH_TOKEN_ENV = "GH_TOKEN"
=======
GH_TOKEN_ENV = "GITHUB_TOKEN"
>>>>>>> feature/conflicting

Recommendation:
- Keep both changes in agent.py (add force parameter)
- Choose one token env name in config.py (suggest: GH_TOKEN)

[User resolves manually, then:]

You: Stage agent.py and config.py

WYN360: [Runs git add agent.py config.py]
✓ Files staged

You: Complete the merge

WYN360: [Runs git commit with merge message]
✓ Merge completed successfully
```

**Wrong Branch Error:**
```
You: Merge main into feature/auth

WYN360: [Checks current branch]

Current branch: main

Error: You're trying to merge 'main' into 'feature/auth', but you're currently on 'main'.

To merge main into feature/auth:
1. First checkout feature/auth: "checkout feature/auth"
2. Then merge: "merge main into feature/auth"

Or did you mean to merge feature/auth into main?
```

**How It Works:**
1. Validates source and target branches exist
2. Ensures user is on the target branch
3. Checks for uncommitted changes (warns if found)
4. Executes git merge with confirmation
5. Detects conflicts and provides guidance
6. Shows merge summary (files changed, lines added/removed)

**Cost:**
- Merge workflow: ~$0.010-0.020
- With conflict resolution: ~$0.020-0.040
- Total: ~$0.010-0.040 per merge

### When GitHub Tools are Used

**WILL Use GitHub Tools:**
- ✅ "Commit to github" / "Commit these changes"
- ✅ "Create pull request" / "Open PR"
- ✅ "Create branch feature/name"
- ✅ "Switch to develop branch"
- ✅ "Merge feature/auth into main"
- ✅ "Push changes to github"
- ✅ "Check github authentication"

**WILL NOT Use GitHub Tools:**
- ❌ File operations ("Write app.py")
- ❌ Code generation ("Create a FastAPI app")
- ❌ Local git commands without pushing ("Show git status")
- ❌ General questions ("What is git?")

### Cost Analysis

**Pricing:**
- **GitHub CLI Commands:** Free (uses GitHub API)
- **Token Costs:** Standard model pricing ($3/$15 per M tokens for Sonnet)
- **No Extra Fees:** No additional GitHub API costs

**Example Costs:**

| Operation | Token Cost | Total Cost |
|-----------|-----------|------------|
| Commit + Push | $0.005-0.010 | $0.005-0.010 |
| Create PR | $0.010-0.020 | $0.010-0.020 |
| Branch Create | $0.003-0.008 | $0.003-0.008 |
| Branch Checkout | $0.003-0.008 | $0.003-0.008 |
| Merge (no conflict) | $0.010-0.020 | $0.010-0.020 |
| Merge (with conflict) | $0.020-0.040 | $0.020-0.040 |

**Session Example:**
```
- 1 authentication check: $0.003
- 2 commits with push: $0.020
- 1 PR creation: $0.015
- 2 branch operations: $0.012
Total: ~$0.050 per session
```

**Monthly Estimate (active developer):**
- 20 working days
- 5 commits per day = 100 commits/month
- 10 PRs per month
- 20 branch operations per month
- Cost: (100 × $0.008) + (10 × $0.015) + (20 × $0.006) ≈ $1.07/month

### Configuration

**Environment Variables:**
```bash
# Set GitHub token for automatic authentication
export GH_TOKEN="ghp_your_token_here"

# Or use GITHUB_TOKEN (both work)
export GITHUB_TOKEN="ghp_your_token_here"
```

**Token Requirements:**
- Format: `ghp_*` or `github_pat_*`
- Required scopes: `repo`, `workflow`
- Generate at: https://github.com/settings/tokens/new

**.env File (Recommended):**
```bash
# .env file in your project root
ANTHROPIC_API_KEY=your_anthropic_key
GH_TOKEN=ghp_your_github_token
```

**Project-Specific Config (.wyn360.yaml):**
```yaml
context: |
  This project follows GitHub Flow:
  - main branch is always deployable
  - feature branches for new work
  - PRs required for all changes

commands:
  commit: "commit to github"
  pr: "create pull request"
  deploy: "merge to main and push"
```

### Technical Implementation

**Integration Method:**
```python
# In agent.py

@agent.tool
async def check_gh_authentication(ctx: RunContext[None]) -> str:
    """Check if user is authenticated with GitHub."""
    gh_token = os.getenv('GH_TOKEN') or os.getenv('GITHUB_TOKEN')
    success, output, _ = execute_command_safe("gh auth status", timeout=10)

    if success and "logged in" in output.lower():
        return f"✓ Authenticated with GitHub as '{username}'"
    elif gh_token:
        # Auto-authenticate with token
        return "✓ Authenticated (auto-authenticated using GH_TOKEN)"
    else:
        return "Not authenticated. Please provide GitHub token..."

@agent.tool
async def gh_commit_changes(
    ctx: RunContext[None],
    message: str,
    push: bool = True
) -> str:
    """Commit changes and optionally push to GitHub."""
    # Stage all changes
    execute_command_safe("git add -A", timeout=10)

    # Commit
    execute_command_safe(f"git commit -m \"{message}\"", timeout=30)

    # Push if requested
    if push:
        execute_command_safe(f"git push origin {branch}", timeout=60)

    return "✓ Successfully committed and pushed changes"
```

**Key Points:**
- Uses GitHub CLI (gh) for all GitHub operations
- All operations use execute_command_safe with confirmation
- Token validation (ghp_* or github_pat_*)
- Environment variables: GH_TOKEN or GITHUB_TOKEN
- Auto-authentication from environment

### Best Practices

**For Users:**

1. **Set Up Token Once:**
   ```bash
   echo "GH_TOKEN=ghp_your_token" >> .env
   ```

2. **Descriptive Commit Messages:**
   ```
   Good: "commit with message 'Add GitHub tools (Phase 8.1)'"
   Bad: "commit changes"
   ```

3. **Feature Branch Workflow:**
   ```
   1. Create branch: "create branch feature/auth"
   2. Make changes: [code generation]
   3. Commit: "commit these changes"
   4. PR: "create pull request"
   ```

4. **Review Before Confirming:**
   - Always check the command in confirmation prompt
   - Verify branch names before merging
   - Review files being committed

**For Teams:**

1. **Shared Configuration:**
   ```yaml
   # .wyn360.yaml (committed to repo)
   context: |
     Follow team conventions:
     - Branch naming: feature/, bugfix/, hotfix/
     - PR requires 2 approvals
     - All tests must pass before merge
   ```

2. **Protected Branches:**
   - Configure on GitHub to prevent direct pushes to main
   - Require PRs for all changes
   - Use branch protection rules

3. **CI/CD Integration:**
   - Use WYN360 for local commits
   - Let CI/CD handle builds and deployments
   - Review test results before merging

### Troubleshooting

**Issue: Not authenticated**
```
Error: Not authenticated with GitHub
```
**Solution:**
1. Set GH_TOKEN or GITHUB_TOKEN environment variable
2. Or run `gh auth login` manually first
3. Verify token format (ghp_* or github_pat_*)

**Issue: Permission denied**
```
Error: Permission denied (publickey)
```
**Solution:**
1. Check SSH keys: `ssh -T git@github.com`
2. Or use HTTPS instead of SSH
3. Verify token has correct scopes

**Issue: Branch already exists**
```
Error: Branch 'feature/auth' already exists
```
**Solution:**
1. Checkout existing branch: "checkout feature/auth"
2. Or delete and recreate: "delete branch feature/auth"
3. Or use different branch name

**Issue: Merge conflict**
```
Error: Merge conflict in agent.py
```
**Solution:**
1. Ask WYN360 to show conflicts
2. Resolve manually in editor
3. Stage resolved files: "stage agent.py"
4. Complete merge: "complete the merge"

**Issue: Nothing to commit**
```
Error: nothing to commit, working tree clean
```
**Solution:**
1. Make changes first before committing
2. Or check if changes were already committed

### Performance

**Response Times:**
- Authentication check: 0.5-1.5 seconds
- Commit + push: 2-5 seconds (depends on changes)
- Create PR: 1-3 seconds
- Branch operations: 0.5-1 second
- Merge: 1-3 seconds (no conflicts)

**Reliability:**
- Uses GitHub CLI (gh) for robust API interactions
- All operations have error handling
- Confirmation prompts prevent accidents
- Session-based authentication (check once per session)

**Limitations:**
- Requires GitHub CLI (gh) installed
- Requires git repository
- Cannot resolve merge conflicts automatically
- Limited to repositories user has access to
- Session limit: Authentication valid for session duration only

### Example Workflow: Complete Feature Development

**Scenario:** Building a new authentication feature

```
# 1. Create feature branch
You: Create a new branch called feature/auth

WYN360: [Creates and checks out branch]
✓ Branch 'feature/auth' created and checked out

# 2. Generate code
You: Create an authentication module with JWT support

WYN360: [Generates auth.py with JWT implementation]
✓ Created auth.py

# 3. Write tests
You: Generate tests for the authentication module

WYN360: [Generates tests/test_auth.py]
✓ Created tests/test_auth.py

# 4. Commit changes
You: Commit these changes with message "Add JWT authentication"

WYN360: [Authentication already verified]
[Stages all changes]
[Commits with message]
[Pushes to origin]
✓ Successfully committed and pushed changes

# 5. Create PR
You: Create a pull request titled "Add JWT Authentication Feature"

WYN360: [Analyzes changes]
[Generates PR description]
[Creates PR on GitHub]
✓ PR created: https://github.com/username/repo/pull/42

# 6. After review, merge to main
You: Checkout main

WYN360: [Switches to main branch]
✓ Checked out main

You: Merge feature/auth into main

WYN360: [Merges branch]
[No conflicts]
✓ Successfully merged feature/auth into main

You: Push to github

WYN360: [Pushes main branch]
✓ Pushed to origin/main

✅ Complete workflow: Branch → Code → Commit → PR → Merge → Deploy
```

**Time Saved:**
- Manual workflow: 10-15 minutes
- With WYN360: 2-3 minutes
- **Efficiency gain: 70-80%**

---

**Version:** 0.3.23
**Last Updated:** December 10, 2025
**Maintained by:** Yiqiao Yin (yiqiao.yin@wyn-associates.com)

## 📝 Changelog

### v0.3.21 (Latest)
- 🌐 **NEW FEATURE:** Phase 11.1 - Real-Time Web Search
- ✅ **BUILTIN TOOL:** WebSearchTool integrated via pydantic-ai framework
- 🌤️ **WEATHER QUERIES:** Ask for weather in any location with automatic search
- 📖 **WEBSITE READING:** Fetch and summarize content from any public URL
- 📚 **CURRENT INFO:** Access latest docs, package updates, news, and trends
- 💰 **COST CONTROLLED:** Limited to 5 searches per session ($10 per 1K searches)
- 🔗 **PROPER CITATIONS:** All results include source URLs and dates
- 📊 **USE CASES:** Added Section 16 to USE_CASES.md with 3 detailed examples
- 🎯 **SMART INVOCATION:** Claude automatically decides when web search is needed
- ⚡ **INTEGRATION:** Works alongside 19 existing custom tools without conflicts
- 📚 **DOCUMENTATION:** Updated SYSTEM.md, COST.md, README.md, agent.py system prompt
- 🧪 **NO BREAKING CHANGES:** Purely additive feature

### v0.3.20
- 🎨 **UX IMPROVEMENT:** Enhanced CLI help output with comprehensive documentation
- ✅ **NEW FLAG:** Added `-h` shorthand for `--help`
- 📚 **DOCUMENTATION:** Help now shows all slash commands, available tools, examples
- 💡 **QUICK REFERENCE:** Users can run `wyn360 -h` to see complete command reference
- 🔧 **ORGANIZED:** Help structured into sections: Quick Start, Slash Commands, Available Tools, Examples, Documentation

### v0.3.19
- 🚀 **NEW FEATURE:** Phase 10.2 - Performance Metrics & Analytics
- ✅ **CLASS:** PerformanceMetrics - Comprehensive session metrics tracking
- 📊 **TRACKING:** Response times (avg, min, max), tool usage, error frequency
- 💻 **COMMAND:** /stats - Display comprehensive performance dashboard
- 📈 **ANALYTICS:** Most used tools, success rates, session duration
- 🔄 **PERSISTENCE:** Metrics saved/loaded with sessions
- 🧪 **TESTS:** Added 11 comprehensive unit tests (169 total tests)
- 📚 **DOCUMENTATION:** Added USE_CASES.md section 15 - Performance Monitoring
- ⚡ **INTEGRATION:** Automatic tracking in read_file, write_file, execute_command, git_status, search_files, list_files
- 🎯 **NON-INTRUSIVE:** Runs transparently in background with zero configuration

### v0.3.18
- 🚀 **NEW FEATURE:** Phase 7.2 - Automatic Test Generation
- ✅ **TOOL:** generate_tests - Automatically generate pytest test stubs for Python files
- 🧪 **AST PARSING:** Safe code analysis without execution
- 📝 **TEMPLATES:** Generates test scaffolding with TODO markers for easy completion
- 🧪 **TESTS:** Added 6 new unit tests for test generation (158 total tests)
- 📚 **DOCUMENTATION:** Updated system prompt with test generation workflow
- 💡 **PRODUCTIVITY:** Saves time by auto-generating test structure
- ⚡ **WORKFLOW:** "generate tests for calculator.py" → instant pytest template

### v0.3.17
- 🚀 **NEW FEATURE:** HuggingFace integration Phase 2 - Full Deployment
- ✅ **TOOL:** create_hf_space - Create HuggingFace Space repository via CLI
- ✅ **TOOL:** push_to_hf_space - Upload files to HuggingFace Space automatically
- 🤖 **AUTOMATION:** Complete end-to-end deployment to HuggingFace Spaces
- 🧪 **TESTS:** Added 6 new unit tests for Phase 2 tools (152 total tests)
- 📚 **DOCUMENTATION:** Updated ROADMAP.md with Phase 6 complete
- 💡 **SYSTEM PROMPT:** Updated workflow with automatic deployment instructions
- 🔧 **BUG FIX:** Fixed authentication loop when HF_TOKEN is set in environment
- ⚡ **WORKFLOW:** Users can now deploy apps with one command: "push to huggingface"

### v0.3.16
- 🚀 **NEW FEATURE:** HuggingFace integration Phase 1
- ✅ **TOOL:** check_hf_authentication - Check HuggingFace CLI authentication status
- ✅ **TOOL:** authenticate_hf - Authenticate with HuggingFace using access token
- ✅ **TOOL:** create_hf_readme - Generate README.md with Space configuration
- 📦 **DEPENDENCY:** Added huggingface-hub>=0.20.0
- 🧪 **TESTS:** Added 12 new unit tests for HuggingFace tools (7 in test_agent.py, 5 in test_utils.py)
- 📚 **DOCUMENTATION:** Updated ROADMAP.md with Phase 6 HuggingFace Integration
- 🛠️ **UTILS:** Added extract_username_from_hf_whoami() helper function
- 💡 **SYSTEM PROMPT:** Added HuggingFace workflow instructions

### v0.3.15
- 📚 **DOCUMENTATION:** Created comprehensive SYSTEM.md with updated architecture
- 📊 **DOCUMENTATION:** Updated mermaid diagram to include all Phase 1-5 features
- 📝 **DOCUMENTATION:** Updated COST.md with Phase 2 tools (13 tools total)
- 🏗️ **DOCUMENTATION:** Cleaned up README.md, moved architecture to SYSTEM.md
- 🔧 **FIX:** Fixed mermaid syntax error for GitHub rendering

### v0.3.14
- 🎨 **UX IMPROVEMENT:** Added confirmation feedback after command execution prompt
- ✓ When pressing 'y': Shows "✓ Confirmed. Executing command..." before spinner
- ✗ When pressing 'N': Shows "✗ Cancelled (pressed 'N')." with clear feedback
- 📺 User now sees immediate visual confirmation that their keypress was registered
- 🔧 Added sys.stdout.flush() to ensure messages appear immediately

### v0.3.13
- 🐛 **CRITICAL FIX:** Removed streaming API entirely to fix persistent duplication
- ✅ Now uses agent.run() to get complete response (not run_stream())
- 🎨 Simulates streaming by splitting response by spaces and printing word-by-word
- ⚡ Small 0.01s delay between words creates smooth streaming effect
- 🔧 Tools execute reliably with non-streaming approach
- 📺 Visual streaming effect maintained without API complexity
- 🎯 Simple, reliable solution: get complete response → split → print word-by-word

### v0.3.12
- 🐛 **CRITICAL FIX:** Eliminated streaming text duplication
- ⚡ Fixed: Agent now yields deltas (new text only), not accumulated text
- 🎯 Simplified CLI: Direct delta display without complex extraction logic
- ✅ Cleaner, more efficient streaming implementation
- 🔧 Updated tests to expect delta chunks instead of accumulated chunks
- 📺 True real-time streaming with correct tool execution

### v0.3.11
- ⚡ **CRITICAL FIX:** Restored REAL streaming using run_stream()
- 🔧 Fixed: Was using run() and waiting for full response, then simulating chunks
- 🎯 Now uses pydantic-ai's run_stream() for true token-by-token streaming
- 📺 Immediate visual feedback - see text appear as model generates it
- ✅ Tools still execute properly with streaming enabled
- 💡 No more long waits - responses appear instantly as they're generated

### v0.3.10
- 🐛 **FIX:** Console width detection causing narrow text wrapping
- 📐 Set minimum console width of 80 characters
- 🎨 Maximum width of 200 for readability
- 💻 Uses shutil.get_terminal_size() with fallback to 120
- ✅ Prevents text from wrapping every 10-15 characters in some environments

### v0.3.9
- 🐛 **FIX:** Stricter early size validation (100KB limit, down from 1MB)
- 🔍 Enhanced type checking with automatic string conversion attempts
- 📏 More explicit ML script guidance: ONE model, NO extensive hyperparameter tuning
- 📊 Better error messages with content preview when size exceeded
- ⚠️ Clear warning: "Your code is too long! Reduce to under 1000 lines"

### v0.3.8
- 🐛 **CRITICAL FIX:** Removed type hints from write_file to bypass pydantic validation
- 📏 Added 50KB size guidance - model now generates concise code
- 🎯 Updated system prompt: "Keep code under 500-800 lines"
- 💡 EDA scripts now include only essential visualizations (3-5 plots)
- ✅ Prevents framework-level validation errors that caused "exceeded max retries"

### v0.3.7
- 🐛 **CRITICAL FIX:** Set retries=0 to completely disable retries
- 📊 Added comprehensive debug logging to write_file tool
- 🔍 Input validation with detailed type checking
- 📝 Full error tracebacks for debugging issues
- 💡 Clear error messages showing exactly what went wrong

### v0.3.6
- 🐛 **FIX:** Reduced retry count from 3 to 1 to prevent "exceeded max retries" errors
- 🔧 Added file size validation (1MB limit) to write_file tool
- 📝 Improved error messages with clearer guidance for tool failures
- 💡 Updated system prompt to clarify retry behavior
- ✅ Better handling of tool validation errors

### v0.3.5
- ✨ **NEW:** Added back "thinking" spinner while agent processes
- 🎨 Better UX - shows "WYN360 is thinking..." with animated dots
- ⏳ Spinner appears before first response chunk is ready
- 🔧 Improved visual feedback during processing time

### v0.3.4
- 🐛 **CRITICAL FIX:** Tool execution bug - tools weren't being called in streaming mode
- 🔧 Switched to non-streaming backend with simulated chunking for reliability
- ✅ All tools now work correctly (list_files, write_file, read_file, etc.)
- 📝 Updated tests to reflect new implementation
- 💡 Better user experience - tools execute properly with streaming-like display

### v0.3.3
- 🐛 **FIX:** Streaming duplication bug - fixed text appearing multiple times
- 🔧 Implemented delta tracking to show only new text portions
- ✅ All 133 tests passing with streaming fix

### v0.3.2
- ✨ **NEW:** Streaming Responses - token-by-token real-time output
- ✨ **NEW:** `chat_stream()` method for streaming responses
- ⚡ Immediate feedback - see responses as they're generated
- 🎯 Better perceived performance - feels 2-3x faster
- 📺 Real-time progress visibility like ChatGPT
- 🧪 Added 3 new unit tests for streaming (133 total tests)
- 💡 No configuration needed - streaming is automatic
- 📚 Comprehensive streaming documentation with comparisons

### v0.3.1
- ✨ **NEW:** Configuration & Personalization - user and project-specific settings
- ✨ **NEW:** User config file (`~/.wyn360/config.yaml`) for personal preferences
- ✨ **NEW:** Project config file (`.wyn360.yaml`) for project-specific context
- ✨ **NEW:** `/config` slash command to view current configuration
- 🔧 Custom instructions automatically added to system prompt
- 🔧 Project context helps AI understand your codebase
- 🔧 Configuration merging with precedence (project > user > defaults)
- 🧪 Added 27 new unit tests for configuration system (130 total tests)
- 📦 Added PyYAML dependency for configuration file parsing
- 📚 Comprehensive configuration documentation and examples
- 💡 Support for aliases, workspaces, dependencies, and commands

### v0.3.0
- ✨ **NEW:** Model selection and switching - choose Haiku, Sonnet, or Opus
- ✨ **NEW:** `/model` slash command to view and switch models mid-session
- ✨ **NEW:** Real-time model information with pricing and descriptions
- 💰 Cost optimization - use cheaper models for simple tasks
- 🔧 Conversation history preserved when switching models
- 🧪 Added 10 new unit tests for model switching (103 total tests)
- 📊 Model comparison guide with cost analysis
- 💡 Three cost optimization strategies documented
- 📚 Updated documentation with comprehensive model examples

### v0.2.9
- ✨ **NEW:** Git operation tools - status, diff, log, branch
- ✨ **NEW:** Code search across files with pattern matching
- ✨ **NEW:** File management tools - delete, move/rename, create directories
- 🔧 Added 8 new tools for enhanced project management
- 🧪 Added 17 new unit tests for Phase 2 tools (93 total tests)
- 📊 Git integration for version control operations
- 🔍 Search capabilities with regex support and file type filtering
- 📁 Complete file system operations with safety features
- 📚 Updated documentation with comprehensive Phase 2 examples

### v0.2.8
- ✨ **NEW:** Conversation history management - context persists across multiple interactions
- ✨ **NEW:** Token usage tracking and cost estimation
- ✨ **NEW:** Slash commands for quick access to context management features
  - `/clear` - Clear conversation history and reset token counters
  - `/history` - Display conversation history in a formatted table
  - `/save <file>` - Save current session to JSON file
  - `/load <file>` - Load session from JSON file
  - `/tokens` - Show detailed token usage statistics and costs
  - `/help` - Display help message with all commands
- ✨ **NEW:** Session save/load functionality - preserve conversations for later
- 🧪 Added 31 new unit tests for history management and slash commands (76 total tests)
- 📊 Real-time cost tracking: input tokens ($3/M), output tokens ($15/M)
- 💾 JSON session export with full conversation state and token statistics
- 📚 Updated documentation with slash command examples and usage patterns

### v0.2.7
- 🐛 **BUGFIX:** Ensured command execution status always displayed
- 🔧 Added CRITICAL instruction to agent: preserve "✅ Command executed successfully" indicator
- 🔧 Agent now required to start responses with status indicator
- 📚 User reported not always seeing success message - now guaranteed
- 💡 Consistent feedback for all command executions

### v0.2.6
- 🎨 **UX IMPROVEMENT:** Enhanced command execution confirmation prompt
- 🔧 Made confirmation much more visible with banner and clear messaging
- 🔧 Added "WAITING FOR YOUR RESPONSE" indicator
- 🔧 Shows command, directory, and permissions clearly
- 🔧 Added sys.stdout.flush() to ensure prompt appears immediately
- 📚 Updated documentation to explain spinner behavior during confirmation
- 💡 Improves user experience - no more confusion about whether to wait or respond

### v0.2.5
- 🐛 **BUGFIX:** Fixed "write_file exceeded max retries" error for script generation
- 🔧 Enhanced intent recognition for "write/generate script" patterns
- 🔧 Added automatic retry with overwrite=True if file exists
- 🔧 Clear instructions: Don't read_file for NEW file creation
- 📚 Better handling of data analysis script generation workflows

### v0.2.4
- 🐛 **BUGFIX:** Fixed key binding error - Changed to Ctrl+Enter for newlines
- 🔧 Updated key bindings: Enter submits, Ctrl+Enter adds newline
- 🔧 Fixed ValueError: Invalid key 's-enter' issue from v0.2.3

### v0.2.3
- 🐛 **BUGFIX:** Fixed multi-line input behavior - Enter now properly submits
- 🔧 Corrected key bindings: Enter submits, Shift+Enter adds newline
- 🔧 Changed from `multiline=True` to custom key binding approach

### v0.2.2
- ✨ **NEW:** Command execution capability - run Python scripts, UV commands, shell scripts, any CLI tool
- ✨ **NEW:** Multi-line input support with Shift+Enter for newline
- ✨ **NEW:** User confirmation prompts before executing commands
- ✨ **NEW:** Timeout protection for long-running commands (5 min default)
- ✨ **NEW:** Comprehensive stdout/stderr capture with exit codes
- 🔧 Added prompt-toolkit dependency for advanced input handling
- 🧪 Added 8 new unit tests for command execution (45 total tests)
- 📚 Updated documentation with command execution examples

### v0.2.1
- ✨ **NEW:** Intelligent file operation handling with intent recognition
- ✨ **NEW:** Context-aware updates (reads before modifying)
- ✨ **NEW:** Self-correcting behavior with smart retry mechanism (3 retries)
- 🔧 Improved error messages for better agent understanding
- 🔧 Enhanced system prompt with file operation guidelines

### v0.2.0
- ✨ Added progress indicator with animated spinner
- 🐛 Fixed duplicate output in CLI display
- 🔧 Improved user experience during long operations

### v0.1.3
- 🐛 Fixed result attribute compatibility across pydantic-ai versions
- 🔧 Support for both .data and .output attributes

### v0.1.2
- 🎨 Fixed ASCII banner to correctly display "WYN360"
- 📧 Updated email to yiqiao.yin@wyn-associates.com

### v0.1.1
- 🐛 Fixed AnthropicModel initialization error
- 🔧 Updated to use environment variables for API key

### v0.1.0
- 🎉 Initial release
