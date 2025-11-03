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

WYN360:
⚠️  About to execute command: python adult.py
⚠️  This will run with your full permissions in the current directory.
   Confirm execution? (y/N): y

✅ Command executed successfully (exit code 0)

Output:
Loading Adult dataset...
Preprocessing data...
Training model...
Accuracy: 0.85
Results saved to results.csv
```

**UV Workflow Example:**
```
You: Initialize a new UV project called my-app and add streamlit

WYN360:
I'll help you set up a UV project:

1. First, initializing the project...
⚠️  About to execute command: uv init my-app
   Confirm execution? (y/N): y
✅ Project initialized

2. Now adding Streamlit...
⚠️  About to execute command: uv add streamlit
   Confirm execution? (y/N): y
✅ Streamlit added to dependencies
```

**Bypass Confirmation (For Testing):**
Set environment variable `WYN360_SKIP_CONFIRM=1` to skip confirmation prompts.

---

### 7. Multi-line Input Support (NEW in v0.2.2)

Write complex, multi-line prompts with ease using keyboard shortcuts.

**How it works:**
- **Enter** → Submit your message
- **Shift+Enter** → Add a new line (continue typing)

**Example:**
```
You: [Shift+Enter for each line]
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

### 6. Use Clear Intent Language (NEW)
- Say "add feature" or "update" when modifying existing files
- Say "create new" or "make another" for new files
- Be explicit about what you want to change
- The agent understands natural language intent

**Examples:**
- ✅ "Add authentication to my app" (updates existing)
- ✅ "Create a new helper module" (creates new)
- ✅ "Improve error handling" (updates existing)
- ✅ "Build a separate API client" (creates new)

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

**Version:** 0.2.2
**Last Updated:** November 2025
**Maintained by:** Yiqiao Yin (yiqiao.yin@wyn-associates.com)

## 📝 Changelog

### v0.2.2 (Latest)
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
