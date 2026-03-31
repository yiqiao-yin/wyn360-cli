# Features Overview

WYN360 CLI provides comprehensive AI-powered development assistance through a rich set of integrated features.

## Core AI Capabilities

### 🤖 Interactive AI Assistant
- **Natural Language Interface** - Describe what you want in plain English
- **Conversation Memory** - Maintains context across multiple interactions
- **Multi-Provider Support** - Anthropic Claude, Google Gemini, AWS Bedrock
- **Model Switching** - Change AI models mid-session based on task complexity

### 📝 Code Generation & Analysis
- **Production-Ready Code** - Generate complete applications, not just snippets
- **Smart File Operations** - Context-aware file creation, reading, and updates
- **Intent Recognition** - Understands "update existing" vs "create new" automatically
- **Self-Correcting** - Smart retry mechanism with error handling

## Agentic Features (v0.4.0)

### 🧠 [Memory & Skills](agentic-memory.md)
- **Persistent Memory** - Remember context across sessions (user preferences, project decisions, feedback)
- **Relevance Selection** - Automatically surfaces the most relevant memories per query
- **Custom Skills** - Define reusable slash commands via YAML files in `~/.wyn360/skills/`
- **Skill Aliases** - Multiple names for the same skill (e.g., `/review`, `/cr`)

### 📋 [Planning & Sub-Agents](planning-and-agents.md)
- **Plan Mode** - Structured step-by-step plans with approve/reject/skip workflow
- **Parallel Workers** - Spawn sub-agents for concurrent research and verification
- **Task Lifecycle** - Track worker status (pending, running, completed, failed, killed)
- **Result Synthesis** - AI combines parallel findings into coherent next steps

### 🔧 [Hooks & Token Budget](hooks-and-budget.md)
- **Hook System** - Pre/post hooks for validation, transformation, and custom processing
- **Safety Hooks** - Built-in detection of destructive commands (rm -rf, DROP TABLE)
- **Auto-Continue** - Automatically continues when responses are cut off by token limits
- **Diminishing Returns** - Detects when continuations produce little new content and stops

## Advanced Features

### 🌐 Web Integration
- **[Real-Time Web Search](web-search.md)** - Access current information and resources
- **[Direct Website Fetching](browser-use.md)** - Read specific URLs directly
- **[Autonomous Browsing](browser-use.md)** - AI navigates websites and extracts data
- **Smart Caching** - Efficient content caching with TTL management

### 📄 Document Processing
- **Multi-Format Support** - Excel, Word, PDF, and more
- **[Vision Mode](vision-mode.md)** - Process images, charts, and diagrams
- **Semantic Chunking** - Intelligent document segmentation
- **Embedding Search** - Find relevant content across large documents

### 🔧 Development Tools
- **[GitHub Integration](github.md)** - Commit, push, create PRs seamlessly
- **[HuggingFace Deployment](huggingface.md)** - Deploy to Spaces with one command
- **Automatic Test Generation** - Generate comprehensive pytest tests
- **Command Execution** - Run any CLI tool with safety confirmations

## Feature Comparison by Provider

| Feature | Anthropic Claude | Google Gemini | AWS Bedrock |
|---------|-----------------|---------------|-------------|
| **Code Generation** | ✅ Excellent | ✅ Very Good | ✅ Excellent |
| **Web Search** | ✅ Built-in | ⚠️ Custom tool | ✅ Built-in |
| **Document Processing** | ✅ Full support | ✅ Full support | ✅ Full support |
| **Vision Mode** | ✅ Advanced | ✅ Good | ✅ Advanced |
| **Browser Automation** | ✅ Supported | ✅ Supported | ✅ Supported |
| **Context Window** | 200K tokens | 2M tokens | 200K tokens |
| **Cost per M tokens** | $3.00/$15.00 | $0.075/$0.30 | $3.00/$15.00 |
| **Best for** | Complex reasoning | Cost efficiency | Enterprise use |

## Development Workflow Features

### 📊 Session Management
- **Conversation History** - Review past interactions
- **Token Tracking** - Monitor API usage and costs in real-time
- **Session Save/Load** - Preserve important conversations
- **Model Information** - View current model, pricing, and capabilities

### ⚙️ Configuration & Customization
- **Hierarchical Config** - Project, user, and default settings
- **Custom Instructions** - Add personal coding standards to every conversation
- **Project Context** - Help AI understand your tech stack
- **Environment Variables** - Runtime configuration overrides

### 🎯 User Experience
- **Multi-line Input** - Shift+Enter for newlines, Enter to submit
- **Streaming Responses** - See results as they're generated
- **Rich Terminal UI** - Beautiful formatting with syntax highlighting
- **Slash Commands** - Quick access to features and settings

## Security & Privacy

### 🔒 Credential Management
- **AES-256 Encryption** - Secure storage of API keys and tokens
- **Per-User Keys** - Isolated encryption for multi-user systems
- **Audit Logging** - Track authentication attempts without exposing secrets
- **Session Management** - Secure cookie storage for web authentication

### 🛡️ Safety Features
- **Command Confirmation** - User approval required for system commands
- **Timeout Protection** - Prevents infinite loops and runaway processes
- **File Permissions** - Respects system security boundaries
- **Error Isolation** - Failed operations don't crash the session

## Performance & Optimization

### ⚡ Speed Features
- **Streaming Responses** - Start reading while AI is generating
- **Smart Caching** - Website and document content caching
- **Parallel Processing** - Multiple operations can run concurrently
- **Token Optimization** - Intelligent context management

### 💰 Cost Management
- **Multiple Models** - Choose based on task complexity and budget
- **Token Limits** - Configurable limits to control costs
- **Usage Tracking** - Real-time monitoring of API consumption
- **Cost Transparency** - Separate tracking for different API types

## Integration Ecosystem

### 🔗 Platform Integrations
- **GitHub** - Repository management, PRs, issues
- **HuggingFace** - Space deployment, model hosting
- **AWS** - Bedrock integration for enterprise users
- **Docker** - Container management and deployment

### 🛠️ Developer Tools
- **Poetry** - Python dependency management
- **Pytest** - Automated testing framework
- **Playwright** - Browser automation
- **Git** - Version control operations

## Feature Roadmap

### Current Focus (v0.4.x)
- ✅ Persistent memory system
- ✅ Sub-agent parallel workers
- ✅ Structured plan mode
- ✅ Token budget auto-continue
- ✅ Extensible skills system
- ✅ Hook-based pipeline

### Previous (v0.3.x)
- ✅ Multi-provider AI support
- ✅ Autonomous browsing capabilities
- ✅ Document processing with vision
- ✅ Google Gemini integration

### Upcoming Features
- **Claude Computer Use** - Direct computer interaction capabilities
- **Enhanced Vision** - Advanced image and diagram processing
- **Team Collaboration** - Shared sessions and project contexts

---

## Get Started with Specific Features

- **[Memory & Skills →](agentic-memory.md)** - Persistent memory and custom slash commands *(v0.4.0)*
- **[Planning & Sub-Agents →](planning-and-agents.md)** - Structured plans and parallel workers *(v0.4.0)*
- **[Hooks & Token Budget →](hooks-and-budget.md)** - Pipeline hooks and auto-continue *(v0.4.0)*
- **[Web Search →](web-search.md)** - Find current information and resources
- **[Browser Use →](browser-use.md)** - Autonomous web navigation and data extraction
- **[Vision Mode →](vision-mode.md)** - Process images and visual content
- **[GitHub Integration →](github.md)** - Seamless repository management
- **[HuggingFace →](huggingface.md)** - Deploy and share your projects

---

**Next:** Explore specific features or check out [Usage Examples →](../usage/use-cases.md)