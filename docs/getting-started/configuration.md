# Configuration

WYN360 CLI uses a hierarchical configuration system that allows you to customize behavior at multiple levels.

## Configuration Hierarchy

Configuration is loaded in this priority order (highest to lowest):

1. **Project Configuration** (`.wyn360.yaml`) - Highest priority
2. **User Configuration** (`~/.wyn360/config.yaml`)
3. **Default Values** - Lowest priority

## User Configuration

### Location
```
~/.wyn360/config.yaml
```

### Creating User Config

Create your user configuration directory and file:

```bash
mkdir -p ~/.wyn360
touch ~/.wyn360/config.yaml
```

### User Config Example

```yaml
# ~/.wyn360/config.yaml
model: "claude-sonnet-4-20250514"
max_tokens: 4096
temperature: 0.1

# Custom instructions added to every conversation
custom_instructions: |
  Please follow these coding standards:
  - Use type hints for all function parameters and return values
  - Add docstrings to all functions and classes
  - Follow PEP 8 style guidelines
  - Prefer pathlib over os.path for file operations
  - Use f-strings for string formatting

# Browser use settings
browser_use_cache_enabled: true
browser_use_cache_ttl: 1800  # 30 minutes
browser_use_truncate_strategy: "smart"  # smart, beginning, end, middle
browser_use_max_tokens: 10000

# User aliases and shortcuts
aliases:
  review: "Review this code for potential improvements, bugs, and style issues"
  test: "Generate comprehensive pytest tests for this code"
  doc: "Add comprehensive documentation and docstrings to this code"
```

## Project Configuration

### Location
```
.wyn360.yaml  # In your project root directory
```

### Project Config Example

```yaml
# .wyn360.yaml - Project-specific settings
model: "gemini-2.5-flash"  # Cost-effective for this project
max_tokens: 2048

# Project context helps AI understand your setup
project_context: |
  This is a FastAPI web application with:
  - PostgreSQL database using SQLAlchemy ORM
  - Redis for caching
  - Celery for background tasks
  - Docker for containerization
  - pytest for testing

  Code style preferences:
  - Use async/await for all database operations
  - Prefer Pydantic models for request/response validation
  - Store configuration in environment variables
  - Use dependency injection for database sessions

# Project-specific custom instructions
custom_instructions: |
  For this project:
  - Always use async/await patterns
  - Include proper error handling with custom exceptions
  - Add logging statements for important operations
  - Follow the established project structure in /app

# Browser settings for this project's needs
browser_use_cache_enabled: false  # Always fetch fresh data
browser_use_max_tokens: 15000     # Need more context for documentation
```

## Configuration Options Reference

### Core Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `model` | string | Auto-detect | AI model to use |
| `max_tokens` | integer | 4096 | Maximum output tokens |
| `temperature` | float | 0.1 | Model creativity (0.0-1.0) |
| `custom_instructions` | string | "" | Added to every conversation |
| `project_context` | string | "" | Project-specific context |

### Browser Use Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `browser_use_cache_enabled` | boolean | true | Enable website caching |
| `browser_use_cache_ttl` | integer | 1800 | Cache TTL in seconds |
| `browser_use_truncate_strategy` | string | "smart" | How to truncate long pages |
| `browser_use_max_tokens` | integer | 10000 | Max tokens for fetched content |

### Truncate Strategies

- `smart` - Preserves structure, removes less important content
- `beginning` - Keep first N tokens
- `end` - Keep last N tokens
- `middle` - Keep first and last, remove middle

## Environment Variables

Environment variables override all configuration files:

### Core Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `CHOOSE_CLIENT` | AI provider (1=Anthropic, 2=Bedrock, 3=Gemini, 0=auto) | `3` |
| `MAX_TOKEN` | Maximum output tokens | `4096` |
| `MAX_INTERNET_SEARCH_LIMIT` | Web searches per session | `5` |
| `WYN360_SKIP_CONFIRM` | Skip command confirmations | `1` |

### AI Provider Credentials

=== "Google Gemini"
    ```bash
    GEMINI_API_KEY=your_key_here
    GEMINI_MODEL=gemini-2.5-flash
    ```

=== "Anthropic Claude"
    ```bash
    ANTHROPIC_API_KEY=your_key_here
    ANTHROPIC_MODEL=claude-sonnet-4-20250514
    ```

=== "AWS Bedrock"
    ```bash
    AWS_ACCESS_KEY_ID=your_access_key
    AWS_SECRET_ACCESS_KEY=your_secret_key
    AWS_SESSION_TOKEN=your_session_token
    AWS_REGION=us-west-2
    ANTHROPIC_MODEL=us.anthropic.claude-sonnet-4-20250514-v1:0
    ```

### Integration Tokens

```bash
GH_TOKEN=ghp_your_github_token              # GitHub features
GITHUB_TOKEN=ghp_your_github_token          # Alternative GitHub token var
HF_TOKEN=hf_your_huggingface_token          # HuggingFace features
HUGGINGFACE_TOKEN=hf_your_huggingface_token # Alternative HF token var
```

## Advanced Configuration

### Workspace-Specific Settings

Create different configurations for different types of projects:

```yaml
# ~/.wyn360/config.yaml
# Default settings
model: "gemini-2.5-flash"
max_tokens: 4096

# Workspace-specific overrides
workspaces:
  ml_projects:
    model: "claude-sonnet-4-20250514"  # Better for complex ML tasks
    max_tokens: 8192
    custom_instructions: |
      Focus on scientific computing best practices:
      - Use NumPy/SciPy for numerical operations
      - Follow scikit-learn patterns for ML models
      - Include proper data validation and preprocessing
      - Add visualization with matplotlib/seaborn

  web_development:
    model: "gemini-2.5-flash"  # Cost-effective for web dev
    max_tokens: 4096
    browser_use_cache_enabled: true
    custom_instructions: |
      Web development focus:
      - Use modern frameworks (FastAPI, React, etc.)
      - Include proper error handling and logging
      - Follow REST API best practices
      - Include basic security measures
```

### Aliases and Shortcuts

```yaml
# ~/.wyn360/config.yaml
aliases:
  # Code review shortcuts
  review: "Review this code for bugs, performance issues, and style problems"
  security: "Analyze this code for security vulnerabilities"
  optimize: "Suggest performance optimizations for this code"

  # Documentation shortcuts
  doc: "Add comprehensive docstrings and comments to this code"
  readme: "Create a README.md file for this project"

  # Testing shortcuts
  test: "Generate comprehensive pytest tests for this code"
  integration: "Create integration tests for this API endpoint"

  # Deployment shortcuts
  deploy: "Help me deploy this application to production"
  docker: "Create a Dockerfile for this application"
```

Usage:
```
You: @review main.py
# Expands to: "Review this code for bugs, performance issues, and style problems" + file content
```

## Configuration Commands

### View Current Configuration

```bash
# In WYN360 CLI session
/config

# Shows:
# 📋 Current Configuration
# Model: gemini-2.5-flash
# Max Tokens: 4096
# Custom Instructions: [First 100 chars...]
# Project Context: [First 100 chars...]
# Browser Cache: Enabled (TTL: 1800s)
```

### Validate Configuration

```bash
# Check config file syntax
poetry run python -c "
import yaml
with open('.wyn360.yaml') as f:
    config = yaml.safe_load(f)
    print('✅ Configuration is valid')
"
```

## Configuration Best Practices

### 1. Layer Your Settings

- **User config**: Personal preferences, API keys, general coding style
- **Project config**: Project-specific context, model selection, team standards
- **Environment variables**: Runtime overrides, CI/CD settings

### 2. Use Project Context Effectively

```yaml
project_context: |
  Tech Stack:
  - Backend: Django 4.2 with DRF
  - Database: PostgreSQL 14
  - Cache: Redis
  - Testing: pytest + factory_boy
  - Deployment: Docker + AWS ECS

  Project Structure:
  - /apps/core/ - Core business logic
  - /apps/api/ - REST API endpoints
  - /apps/users/ - User management
  - /config/ - Settings and configuration

  Coding Standards:
  - Follow Django best practices
  - Use class-based views for complex logic
  - Prefer function-based views for simple endpoints
  - All models must have proper __str__ methods
  - Use Django's built-in User model extensions
```

### 3. Cost Optimization

```yaml
# Cost-conscious configuration
model: "gemini-2.5-flash"  # 40x cheaper than Claude
max_tokens: 2048           # Reduce for simpler tasks
browser_use_cache_enabled: true  # Avoid re-fetching pages
browser_use_cache_ttl: 3600      # Cache for 1 hour
```

### 4. Team Consistency

Create a shared `.wyn360.yaml` in your project repository:

```yaml
# .wyn360.yaml - Team settings
model: "claude-sonnet-4-20250514"  # Consistent model for team
max_tokens: 4096
temperature: 0.1  # Consistent, less random responses

project_context: |
  Team coding standards and project setup...

custom_instructions: |
  Team-wide instructions that everyone should follow...

# Don't include API keys in project config!
# Use environment variables or user config instead
```

---

**Next:** [Features Overview →](../features/overview.md)