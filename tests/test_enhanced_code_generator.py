"""
Unit tests for Enhanced Code Generator

Tests the smolagents-inspired code generation functionality.
"""

import pytest
import asyncio
import re
from unittest.mock import Mock, patch, AsyncMock

from wyn360_cli.tools.browser.enhanced_code_generator import (
    EnhancedCodeGenerator,
    CodeGenerationContext,
    TaskComplexity,
    CodeOptimizationLevel
)
from wyn360_cli.tools.browser.code_templates import AutomationTemplates


class TestCodeGenerationContext:
    """Test CodeGenerationContext dataclass"""

    def test_default_context_creation(self):
        """Test creating context with defaults"""
        context = CodeGenerationContext(
            task_description="Find wireless mouse",
            url="https://amazon.com"
        )

        assert context.task_description == "Find wireless mouse"
        assert context.url == "https://amazon.com"
        assert context.complexity == TaskComplexity.MODERATE
        assert context.optimization_level == CodeOptimizationLevel.STANDARD
        assert context.include_error_handling is True
        assert context.include_waits is True
        assert context.max_retries == 3

    def test_custom_context_creation(self):
        """Test creating context with custom values"""
        schema = {"name": str, "price": float}
        context = CodeGenerationContext(
            task_description="Complex task",
            url="https://example.com",
            expected_output_schema=schema,
            complexity=TaskComplexity.COMPLEX,
            optimization_level=CodeOptimizationLevel.ADVANCED,
            include_error_handling=False,
            max_retries=5
        )

        assert context.expected_output_schema == schema
        assert context.complexity == TaskComplexity.COMPLEX
        assert context.optimization_level == CodeOptimizationLevel.ADVANCED
        assert context.include_error_handling is False
        assert context.max_retries == 5


class TestEnhancedCodeGenerator:
    """Test EnhancedCodeGenerator class"""

    def setup_method(self):
        """Setup test fixtures"""
        self.generator = EnhancedCodeGenerator()

    def test_initialization(self):
        """Test generator initialization"""
        assert self.generator is not None
        assert hasattr(self.generator, 'templates')
        assert hasattr(self.generator, '_code_patterns')
        assert hasattr(self.generator, '_optimization_rules')

    def test_code_patterns_initialization(self):
        """Test code patterns are properly initialized"""
        patterns = self.generator._code_patterns

        assert 'navigation' in patterns
        assert 'search_action' in patterns
        assert 'data_extraction' in patterns
        assert 'form_interaction' in patterns

        # Check that patterns contain placeholder formatting
        assert '{url}' in patterns['navigation']
        assert '{search_term}' in patterns['search_action']

    def test_optimization_rules_initialization(self):
        """Test optimization rules are properly initialized"""
        rules = self.generator._optimization_rules

        assert 'waits' in rules
        assert 'selectors' in rules
        assert 'error_handling' in rules
        assert 'performance' in rules

        assert isinstance(rules['waits'], list)
        assert len(rules['waits']) > 0

    @pytest.mark.asyncio
    async def test_analyze_task_simple(self):
        """Test task analysis for simple tasks"""
        context = CodeGenerationContext(
            task_description="Click the login button",
            url="https://example.com"
        )

        analysis = await self.generator._analyze_task(context)

        assert isinstance(analysis, dict)
        assert 'complexity' in analysis
        assert 'involves_search' in analysis
        assert 'involves_interaction' in analysis

        # Simple click task should be low complexity
        assert analysis['complexity'] in [TaskComplexity.SIMPLE, TaskComplexity.MODERATE]

    @pytest.mark.asyncio
    async def test_analyze_task_complex(self):
        """Test task analysis for complex tasks"""
        context = CodeGenerationContext(
            task_description="Search for all wireless mice under $20, filter by rating, extract all product details",
            url="https://amazon.com"
        )

        analysis = await self.generator._analyze_task(context)

        assert analysis['involves_search'] is True
        assert analysis['involves_filtering'] is True
        assert analysis['involves_extraction'] is True
        assert analysis['requires_loops'] is True
        assert analysis['complexity'] == TaskComplexity.COMPLEX

    def test_extract_search_terms_quoted(self):
        """Test extracting quoted search terms"""
        terms = self.generator._extract_search_terms('Search for "wireless mouse" on the site')
        assert terms == ["wireless mouse"]

    def test_extract_search_terms_pattern(self):
        """Test extracting search terms from patterns"""
        terms = self.generator._extract_search_terms('Find wireless keyboard on Amazon')
        assert "wireless keyboard" in terms[0] or "keyboard" in terms

    def test_extract_search_terms_product(self):
        """Test extracting common product terms"""
        terms = self.generator._extract_search_terms('Browse for mouse products')
        assert "wireless mouse" in terms

    def test_extract_form_data_login(self):
        """Test extracting form data for login tasks"""
        form_data = self.generator._extract_form_data('Login to the website')

        assert 'email' in form_data or 'username' in form_data
        assert 'password' in form_data

    def test_extract_form_data_registration(self):
        """Test extracting form data for registration tasks"""
        form_data = self.generator._extract_form_data('Register a new account')

        assert 'name' in form_data
        assert 'email' in form_data
        assert 'password' in form_data

    def test_generate_header(self):
        """Test generating code header"""
        header = self.generator._generate_header()

        assert "import asyncio" in header
        assert "import json" in header
        assert "result = None" in header

    def test_generate_setup(self):
        """Test generating setup code"""
        context = CodeGenerationContext(
            task_description="Test task",
            url="https://test.com"
        )

        setup = self.generator._generate_setup(context)

        assert 'url = "https://test.com"' in setup
        assert 'task_description = "Test task"' in setup

    @pytest.mark.asyncio
    async def test_generate_filter_code_price(self):
        """Test generating price filter code"""
        filter_code = await self.generator._generate_filter_code("Find items under $25")

        assert "$25" in filter_code or "25" in filter_code
        assert "price_filter" in filter_code.lower()

    @pytest.mark.asyncio
    async def test_generate_filter_code_rating(self):
        """Test generating rating filter code"""
        filter_code = await self.generator._generate_filter_code("Find products with 4 star rating")

        assert "star" in filter_code.lower() or "rating" in filter_code.lower()
        assert "4" in filter_code

    def test_generate_schema_based_extraction(self):
        """Test generating extraction code from schema"""
        schema = {
            "name": str,
            "price": float,
            "available": bool
        }

        extraction_code = self.generator._generate_schema_based_extraction(schema)

        assert "name" in extraction_code
        assert "price" in extraction_code
        assert "available" in extraction_code
        assert "float(re.findall" in extraction_code  # Price parsing
        assert "available" in extraction_code and "in stock" in extraction_code  # Boolean logic

    def test_generate_task_based_extraction_products(self):
        """Test generating extraction code based on task description"""
        extraction_code = self.generator._generate_task_based_extraction("Find wireless mouse products")

        assert "product" in extraction_code.lower()
        assert "name" in extraction_code
        assert "price" in extraction_code
        assert "rating" in extraction_code

    def test_generate_result_processing(self):
        """Test generating result processing code"""
        context = CodeGenerationContext(
            task_description="Test",
            url="https://test.com"
        )

        processing_code = self.generator._generate_result_processing(context)

        assert "if result:" in processing_code
        assert "isinstance(result, dict)" in processing_code
        assert "isinstance(result, list)" in processing_code

    def test_wrap_with_error_handling(self):
        """Test wrapping code with error handling"""
        simple_code = "print('hello')"
        wrapped_code = self.generator._wrap_with_error_handling(simple_code)

        assert "async def execute_automation():" in wrapped_code
        assert "try:" in wrapped_code
        assert "except Exception as automation_error:" in wrapped_code
        assert "await execute_automation()" in wrapped_code

    def test_indent_code(self):
        """Test code indentation"""
        code = "line1\nline2\n    indented"
        indented = self.generator._indent_code(code, 4)

        lines = indented.split('\n')
        assert lines[0] == "    line1"
        assert lines[1] == "    line2"
        assert lines[2] == "        indented"

    @pytest.mark.asyncio
    async def test_optimize_code_advanced(self):
        """Test code optimization with advanced level"""
        context = CodeGenerationContext(
            task_description="Test",
            url="https://test.com",
            optimization_level=CodeOptimizationLevel.ADVANCED
        )

        original_code = "await page.goto('https://test.com')\npage.locator('.test')"
        optimized = await self.generator._optimize_code(original_code, context)

        # Should add waits and other optimizations
        assert "wait_for_load_state" in optimized

    def test_add_intelligent_waits(self):
        """Test adding intelligent waits to code"""
        code = "await page.goto('https://test.com')"
        enhanced = self.generator._add_intelligent_waits(code)

        assert "wait_for_load_state('networkidle')" in enhanced

    @pytest.mark.asyncio
    async def test_validate_generated_code_valid(self):
        """Test validation of valid code"""
        valid_code = """
import asyncio
try:
    result = {"test": "value"}
except:
    result = None
"""

        is_valid, issues = await self.generator.validate_generated_code(valid_code)

        if not is_valid:
            print(f"Validation issues: {issues}")

        assert is_valid is True
        assert len(issues) == 0

    @pytest.mark.asyncio
    async def test_validate_generated_code_invalid_syntax(self):
        """Test validation of code with syntax errors"""
        invalid_code = """
import asyncio
result = {"test": "value"  # Missing closing brace
"""

        is_valid, issues = await self.generator.validate_generated_code(invalid_code)

        assert is_valid is False
        assert len(issues) > 0
        assert "Syntax error" in issues[0]

    @pytest.mark.asyncio
    async def test_validate_generated_code_missing_imports(self):
        """Test validation catches missing imports"""
        code_without_imports = """
result = {"test": "value"}
"""

        is_valid, issues = await self.generator.validate_generated_code(code_without_imports)

        assert is_valid is False
        assert any("Missing asyncio import" in issue for issue in issues)

    @pytest.mark.asyncio
    async def test_estimate_execution_complexity_simple(self):
        """Test complexity estimation for simple tasks"""
        context = CodeGenerationContext(
            task_description="Click a button",
            url="https://test.com"
        )

        complexity = await self.generator.estimate_execution_complexity(context)

        assert isinstance(complexity, dict)
        assert 'complexity_score' in complexity
        assert 'estimated_execution_time' in complexity
        assert 'resource_intensity' in complexity
        assert complexity['complexity_score'] >= 0

    @pytest.mark.asyncio
    async def test_estimate_execution_complexity_complex(self):
        """Test complexity estimation for complex tasks"""
        context = CodeGenerationContext(
            task_description="Search for products, filter by price, extract all data from multiple pages",
            url="https://amazon.com"
        )

        complexity = await self.generator.estimate_execution_complexity(context)

        assert complexity['complexity_score'] > 3
        assert complexity['resource_intensity'] in ['medium', 'high']

    @pytest.mark.asyncio
    async def test_generate_automation_code_complete(self):
        """Test complete code generation process"""
        context = CodeGenerationContext(
            task_description="Search for wireless mouse under $20",
            url="https://amazon.com",
            expected_output_schema={"name": str, "price": float}
        )

        code = await self.generator.generate_automation_code(context)

        # Check that generated code contains expected elements
        assert "import asyncio" in code
        assert "amazon.com" in code
        assert "wireless mouse" in code or "mouse" in code
        assert "result" in code
        assert len(code) > 100  # Should be substantial code

        # Validate the generated code
        is_valid, issues = await self.generator.validate_generated_code(code)
        if not is_valid:
            print(f"Generated code issues: {issues}")
            print(f"Generated code:\n{code}")

        assert is_valid, f"Generated code should be valid. Issues: {issues}"

    @pytest.mark.asyncio
    async def test_generate_automation_code_without_error_handling(self):
        """Test code generation without error handling"""
        context = CodeGenerationContext(
            task_description="Simple task",
            url="https://test.com",
            include_error_handling=False
        )

        code = await self.generator.generate_automation_code(context)

        # Should still have execute_automation function but not comprehensive error handling
        assert "execute_automation" in code  # Basic wrapper is still present
        assert "Automation error occurred" not in code  # No complex error handling
        assert code.count("try:") <= 2  # Minimal try blocks

    @pytest.mark.asyncio
    async def test_generate_automation_code_basic_optimization(self):
        """Test code generation with basic optimization"""
        context = CodeGenerationContext(
            task_description="Test task",
            url="https://test.com",
            optimization_level=CodeOptimizationLevel.BASIC
        )

        code = await self.generator.generate_automation_code(context)

        # Should still be valid but with less optimization
        is_valid, issues = await self.generator.validate_generated_code(code)
        assert is_valid

    @pytest.mark.asyncio
    async def test_generate_main_logic_search_task(self):
        """Test main logic generation for search task"""
        context = CodeGenerationContext(
            task_description="Search for laptops",
            url="https://amazon.com"
        )

        task_analysis = await self.generator._analyze_task(context)
        main_logic = await self.generator._generate_main_logic(context, task_analysis)

        assert "search" in main_logic.lower()
        assert "laptop" in main_logic.lower()

    @pytest.mark.asyncio
    async def test_generate_main_logic_form_task(self):
        """Test main logic generation for form task"""
        context = CodeGenerationContext(
            task_description="Fill out the login form",
            url="https://test.com"
        )

        task_analysis = await self.generator._analyze_task(context)
        main_logic = await self.generator._generate_main_logic(context, task_analysis)

        assert "form" in main_logic.lower()
        assert "email" in main_logic.lower() or "username" in main_logic.lower()

    @pytest.mark.asyncio
    async def test_end_to_end_code_generation_and_validation(self):
        """Test complete end-to-end code generation and validation"""
        test_cases = [
            {
                "description": "Find cheapest wireless mouse under $30",
                "url": "https://amazon.com",
                "should_contain": ["wireless mouse", "30", "price"]
            },
            {
                "description": "Login to the website",
                "url": "https://example.com/login",
                "should_contain": ["email", "password", "login"]
            },
            {
                "description": "Extract product data from search results",
                "url": "https://shop.com",
                "should_contain": ["product", "extract", "result"]
            }
        ]

        for test_case in test_cases:
            context = CodeGenerationContext(
                task_description=test_case["description"],
                url=test_case["url"]
            )

            code = await self.generator.generate_automation_code(context)

            # Validate syntax
            is_valid, issues = await self.generator.validate_generated_code(code)
            assert is_valid, f"Code should be valid for '{test_case['description']}'. Issues: {issues}"

            # Check content
            code_lower = code.lower()
            for expected_content in test_case["should_contain"]:
                assert expected_content.lower() in code_lower, f"Code should contain '{expected_content}'"

    def test_multiple_selector_strategies(self):
        """Test that generated code includes multiple selector strategies"""
        # Test search action pattern
        search_pattern = self.generator._code_patterns['search_action']
        assert "search_selectors" in search_pattern
        assert "for selector in search_selectors" in search_pattern

        # Test form interaction pattern
        form_pattern = self.generator._code_patterns['form_interaction']
        assert "field_selectors" in form_pattern
        assert "for selector in field_selectors" in form_pattern


class TestCodeTemplatesIntegration:
    """Test integration with AutomationTemplates"""

    def setup_method(self):
        """Setup test fixtures"""
        self.generator = EnhancedCodeGenerator()

    def test_templates_integration(self):
        """Test that generator properly integrates with templates"""
        assert self.generator.templates is not None
        assert isinstance(self.generator.templates, AutomationTemplates)

    def test_code_patterns_use_templates(self):
        """Test that code patterns are consistent with templates"""
        patterns = self.generator._code_patterns

        # Test navigation pattern
        navigation_pattern = patterns['navigation']
        assert '{url}' in navigation_pattern
        assert 'goto' in navigation_pattern
        assert 'wait_for_load_state' in navigation_pattern