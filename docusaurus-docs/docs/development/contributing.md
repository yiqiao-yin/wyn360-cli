# Contributing

Contributions to WYN360 CLI are welcome! This guide will help you get started.

## Development Setup

### Prerequisites

- Python >= 3.10
- Poetry (package manager)
- Git

### Setup Steps

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/your-username/wyn360-cli.git
   cd wyn360-cli
   ```

2. **Install Poetry** (if not already installed):
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

3. **Install dependencies:**
   ```bash
   poetry install
   ```

4. **Set up pre-commit hooks (recommended):**
   ```bash
   poetry run pre-commit install
   ```

## Development Workflow

### Making Changes

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes and test:**
   ```bash
   # Run tests
   WYN360_SKIP_CONFIRM=1 poetry run pytest tests/ -v

   # Test your changes manually
   poetry run wyn360
   ```

3. **Update documentation if needed:**
   ```bash
   # Update version in pyproject.toml, __init__.py
   # Update docs/ if adding new features
   ```

### Testing

**Run all tests:**
```bash
WYN360_SKIP_CONFIRM=1 poetry run pytest tests/ -v
```

**Run specific test file:**
```bash
poetry run pytest tests/test_agent.py -v
```

**Run with coverage:**
```bash
poetry run pytest tests/ --cov=wyn360_cli --cov-report=html
```

### Code Style

We follow Python best practices:

- **PEP 8** style guidelines
- **Type hints** for function parameters and return values
- **Docstrings** for public functions and classes
- **Black** for code formatting
- **isort** for import sorting

## Submitting Changes

### Pull Request Process

1. **Ensure tests pass:**
   ```bash
   WYN360_SKIP_CONFIRM=1 poetry run pytest tests/ -v
   ```

2. **Update documentation:**
   - Add/update docstrings
   - Update relevant `.md` files
   - Update version numbers if needed

3. **Commit your changes:**
   ```bash
   git add .
   git commit -m "feat: your feature description"
   ```

4. **Push and create PR:**
   ```bash
   git push origin feature/your-feature-name
   # Create pull request on GitHub
   ```

### Commit Message Format

Use conventional commits:

- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `test:` - Adding/updating tests
- `refactor:` - Code refactoring
- `style:` - Code style changes

Examples:
```
feat: Add Google Gemini integration
fix: Handle timeout errors in web search
docs: Update installation instructions
test: Add tests for document processing
```

## Areas for Contribution

### High Priority
- **Bug fixes** - Check GitHub issues
- **Documentation improvements** - Always welcome
- **Test coverage** - Increase test coverage
- **Performance optimizations** - Speed and efficiency

### Feature Development
- **New AI providers** - Additional LLM integrations
- **Tool integrations** - New development tools
- **UI improvements** - Better terminal experience
- **Platform support** - Windows/macOS specific features

### Documentation
- **Usage examples** - Real-world workflows
- **Tutorial content** - Step-by-step guides
- **API documentation** - Code documentation
- **Video tutorials** - Screen recordings

## Getting Help

### Resources
- **GitHub Issues** - Bug reports and feature requests
- **Discussions** - General questions and ideas
- **Discord** - Real-time chat (if available)

### Code Review Process
- All changes require review
- Maintain backward compatibility
- Include tests for new features
- Update documentation

## Release Process

### Version Management

Update version in:
- `pyproject.toml` - `version = "X.Y.Z"`
- `wyn360_cli/__init__.py` - `__version__ = "X.Y.Z"`
- Documentation files as needed

### Building and Publishing

```bash
# Build package
poetry build

# Test locally
pip install dist/wyn360_cli-X.Y.Z-py3-none-any.whl

# Publish to PyPI (maintainers only)
poetry publish
```

## Code of Conduct

- Be respectful and inclusive
- Help others learn and grow
- Focus on constructive feedback
- Maintain professional communication

Thank you for contributing to WYN360 CLI!