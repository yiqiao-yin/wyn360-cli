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

**Version:** 0.3.2
**Last Updated:** January 2025
**Maintained by:** Yiqiao Yin (yiqiao.yin@wyn-associates.com)

## 📝 Changelog

### v0.3.2 (Latest)
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
