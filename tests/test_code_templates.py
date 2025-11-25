"""
Unit tests for Code Templates

Tests the automation code templates and patterns.
"""

import pytest
from wyn360_cli.tools.browser.code_templates import (
    AutomationTemplates,
    TemplateCategory
)


class TestTemplateCategory:
    """Test TemplateCategory enum"""

    def test_template_categories(self):
        """Test that all expected categories exist"""
        expected_categories = [
            "navigation",
            "search",
            "forms",
            "data_extraction",
            "interaction",
            "error_handling"
        ]

        for category in expected_categories:
            assert hasattr(TemplateCategory, category.upper())
            assert TemplateCategory[category.upper()].value == category


class TestAutomationTemplates:
    """Test AutomationTemplates class"""

    def setup_method(self):
        """Setup test fixtures"""
        self.templates = AutomationTemplates()

    def test_initialization(self):
        """Test template initialization"""
        assert self.templates is not None
        assert hasattr(self.templates, '_templates')
        assert hasattr(self.templates, '_patterns')

    def test_templates_structure(self):
        """Test that all template categories are initialized"""
        expected_categories = [
            TemplateCategory.NAVIGATION.value,
            TemplateCategory.SEARCH.value,
            TemplateCategory.FORMS.value,
            TemplateCategory.DATA_EXTRACTION.value,
            TemplateCategory.INTERACTION.value,
            TemplateCategory.ERROR_HANDLING.value
        ]

        for category in expected_categories:
            assert category in self.templates._templates
            assert isinstance(self.templates._templates[category], dict)
            assert len(self.templates._templates[category]) > 0

    def test_navigation_templates(self):
        """Test navigation template category"""
        nav_templates = self.templates._templates[TemplateCategory.NAVIGATION.value]

        assert "basic_navigation" in nav_templates
        assert "navigation_with_retry" in nav_templates
        assert "conditional_navigation" in nav_templates

        # Test basic navigation template
        basic_nav = nav_templates["basic_navigation"]
        assert "await page.goto" in basic_nav
        assert "{url}" in basic_nav
        assert "wait_until" in basic_nav

        # Test retry navigation template
        retry_nav = nav_templates["navigation_with_retry"]
        assert "max_retries" in retry_nav
        assert "for attempt in range" in retry_nav

    def test_search_templates(self):
        """Test search template category"""
        search_templates = self.templates._templates[TemplateCategory.SEARCH.value]

        assert "robust_search" in search_templates
        assert "search_with_suggestions" in search_templates

        # Test robust search template
        robust_search = search_templates["robust_search"]
        assert "search_selectors" in robust_search
        assert "{search_term}" in robust_search
        assert "for selector in search_selectors" in robust_search
        assert "input[placeholder*=" in robust_search

    def test_forms_templates(self):
        """Test forms template category"""
        forms_templates = self.templates._templates[TemplateCategory.FORMS.value]

        assert "form_fill_robust" in forms_templates
        assert "login_form" in forms_templates

        # Test form fill template
        form_fill = forms_templates["form_fill_robust"]
        assert "{form_data}" in form_fill
        assert "field_selectors" in form_fill
        assert "field_type" in form_fill

        # Test login form template
        login_form = forms_templates["login_form"]
        assert "{username}" in login_form
        assert "{password}" in login_form
        assert "username_selectors" in login_form
        assert "password_selectors" in login_form

    def test_data_extraction_templates(self):
        """Test data extraction template category"""
        extraction_templates = self.templates._templates[TemplateCategory.DATA_EXTRACTION.value]

        assert "product_extraction" in extraction_templates
        assert "table_extraction" in extraction_templates

        # Test product extraction template
        product_extract = extraction_templates["product_extraction"]
        assert "product_selectors" in product_extract
        assert "name_selectors" in product_extract
        assert "price_selectors" in product_extract
        assert "rating_selectors" in product_extract

        # Test table extraction template
        table_extract = extraction_templates["table_extraction"]
        assert "table_selectors" in table_extract
        assert "header_rows" in table_extract
        assert "data_rows" in table_extract

    def test_interaction_templates(self):
        """Test interaction template category"""
        interaction_templates = self.templates._templates[TemplateCategory.INTERACTION.value]

        assert "filter_application" in interaction_templates
        assert "pagination_navigation" in interaction_templates

        # Test filter application template
        filter_app = interaction_templates["filter_application"]
        assert "{filters}" in filter_app
        assert "filter_applied" in filter_app

        # Test pagination template
        pagination = interaction_templates["pagination_navigation"]
        assert "{max_pages}" in pagination
        assert "next_page_selectors" in pagination

    def test_error_handling_templates(self):
        """Test error handling template category"""
        error_templates = self.templates._templates[TemplateCategory.ERROR_HANDLING.value]

        assert "retry_wrapper" in error_templates
        assert "graceful_degradation" in error_templates
        assert "error_recovery" in error_templates

        # Test retry wrapper template
        retry_wrapper = error_templates["retry_wrapper"]
        assert "async def retry_operation" in retry_wrapper
        assert "max_retries" in retry_wrapper
        assert "Exponential backoff" in retry_wrapper or "exponential backoff" in retry_wrapper

    def test_patterns_initialization(self):
        """Test that patterns are properly initialized"""
        patterns = self.templates._patterns

        expected_patterns = [
            "wait_for_element",
            "safe_fill",
            "extract_with_fallback"
        ]

        for pattern in expected_patterns:
            assert pattern in patterns
            assert "async def" in patterns[pattern]

    def test_get_template_valid(self):
        """Test getting a valid template"""
        template = self.templates.get_template(
            TemplateCategory.NAVIGATION.value,
            "basic_navigation"
        )

        assert template is not None
        assert "await page.goto" in template
        assert "{url}" in template

    def test_get_template_invalid_category(self):
        """Test getting template from invalid category"""
        template = self.templates.get_template("invalid_category", "basic_navigation")
        assert template is None

    def test_get_template_invalid_name(self):
        """Test getting invalid template name"""
        template = self.templates.get_template(
            TemplateCategory.NAVIGATION.value,
            "invalid_template"
        )
        assert template is None

    def test_get_category_templates(self):
        """Test getting all templates in a category"""
        nav_templates = self.templates.get_category_templates(TemplateCategory.NAVIGATION.value)

        assert isinstance(nav_templates, dict)
        assert "basic_navigation" in nav_templates
        assert "navigation_with_retry" in nav_templates
        assert len(nav_templates) >= 3

    def test_get_category_templates_invalid(self):
        """Test getting templates from invalid category"""
        templates = self.templates.get_category_templates("invalid_category")
        assert templates == {}

    def test_list_templates(self):
        """Test listing all templates"""
        all_templates = self.templates.list_templates()

        assert isinstance(all_templates, dict)
        assert TemplateCategory.NAVIGATION.value in all_templates
        assert TemplateCategory.SEARCH.value in all_templates

        # Check that each category has templates
        for category, template_names in all_templates.items():
            assert isinstance(template_names, list)
            assert len(template_names) > 0

    def test_get_pattern_valid(self):
        """Test getting a valid pattern"""
        pattern = self.templates.get_pattern("wait_for_element")

        assert pattern is not None
        assert "async def wait_for_element" in pattern
        assert "page.locator" in pattern

    def test_get_pattern_invalid(self):
        """Test getting invalid pattern"""
        pattern = self.templates.get_pattern("invalid_pattern")
        assert pattern is None

    def test_list_patterns(self):
        """Test listing all patterns"""
        patterns = self.templates.list_patterns()

        assert isinstance(patterns, list)
        assert "wait_for_element" in patterns
        assert "safe_fill" in patterns
        assert "extract_with_fallback" in patterns
        assert len(patterns) >= 3

    def test_search_templates_keyword(self):
        """Test searching templates by keyword"""
        results = self.templates.search_templates("navigation")

        assert isinstance(results, dict)
        assert TemplateCategory.NAVIGATION.value in results
        assert "basic_navigation" in results[TemplateCategory.NAVIGATION.value]

    def test_search_templates_code_content(self):
        """Test searching templates by code content"""
        results = self.templates.search_templates("page.goto")

        assert isinstance(results, dict)
        assert TemplateCategory.NAVIGATION.value in results

    def test_search_templates_no_results(self):
        """Test searching templates with no matches"""
        results = self.templates.search_templates("nonexistent_keyword_xyz123")
        assert results == {}

    def test_generate_custom_template(self):
        """Test adding custom template"""
        custom_code = "await page.click('.custom-button')"
        success = self.templates.generate_custom_template(
            "custom_click",
            custom_code,
            "custom"
        )

        assert success is True

        # Verify template was added
        custom_template = self.templates.get_template("custom", "custom_click")
        assert custom_template == custom_code

    def test_generate_custom_template_existing_category(self):
        """Test adding custom template to existing category"""
        custom_code = "# Custom navigation code"
        success = self.templates.generate_custom_template(
            "custom_nav",
            custom_code,
            TemplateCategory.NAVIGATION.value
        )

        assert success is True

        # Verify template was added
        nav_templates = self.templates.get_category_templates(TemplateCategory.NAVIGATION.value)
        assert "custom_nav" in nav_templates
        assert nav_templates["custom_nav"] == custom_code

    def test_template_placeholder_consistency(self):
        """Test that templates use consistent placeholders"""
        # Check navigation templates use {url}
        nav_templates = self.templates.get_category_templates(TemplateCategory.NAVIGATION.value)
        for name, template in nav_templates.items():
            if "goto" in template:
                assert "{url}" in template, f"Navigation template {name} should use {{url}} placeholder"

        # Check search templates use {search_term}
        search_templates = self.templates.get_category_templates(TemplateCategory.SEARCH.value)
        for name, template in search_templates.items():
            if "search_term" in template:
                assert "{search_term}" in template, f"Search template {name} should use {{search_term}} placeholder"

    def test_template_async_patterns(self):
        """Test that templates use proper async/await patterns"""
        all_templates = self.templates._templates

        for category, templates in all_templates.items():
            for name, template in templates.items():
                if "page." in template:
                    # Templates with page interactions should use await
                    # Some templates may use page.locator without await directly
                    if "page.locator" not in template or "await " in template:
                        assert "await page." in template or "await " in template, f"Template {category}/{name} should use await with page operations"

    def test_template_error_handling(self):
        """Test that templates include appropriate error handling"""
        # Navigation templates should have error handling
        nav_templates = self.templates.get_category_templates(TemplateCategory.NAVIGATION.value)
        basic_nav = nav_templates["basic_navigation"]
        assert "try:" in basic_nav and ("except:" in basic_nav or "except Exception" in basic_nav)

        # Robust search should have error handling
        search_templates = self.templates.get_category_templates(TemplateCategory.SEARCH.value)
        robust_search = search_templates["robust_search"]
        assert "try:" in robust_search and "except:" in robust_search

    def test_template_selector_strategies(self):
        """Test that templates use multiple selector strategies"""
        # Search template should have multiple selectors
        search_templates = self.templates.get_category_templates(TemplateCategory.SEARCH.value)
        robust_search = search_templates["robust_search"]
        assert "search_selectors = [" in robust_search
        assert len([line for line in robust_search.split('\n') if 'input[' in line]) >= 3

        # Form template should have multiple selectors
        form_templates = self.templates.get_category_templates(TemplateCategory.FORMS.value)
        robust_form = form_templates["form_fill_robust"]
        assert "field_selectors = [" in robust_form
        assert len([line for line in robust_form.split('\n') if 'input[' in line]) >= 3

    def test_data_extraction_robustness(self):
        """Test that data extraction templates are robust"""
        extraction_templates = self.templates.get_category_templates(TemplateCategory.DATA_EXTRACTION.value)

        # Product extraction should handle multiple product containers
        product_extract = extraction_templates["product_extraction"]
        assert "product_selectors = [" in product_extract
        assert ".product-item" in product_extract
        assert ".s-result-item" in product_extract

        # Should handle multiple name selectors
        assert "name_selectors = [" in product_extract
        assert ".title" in product_extract
        assert ".name" in product_extract

    def test_interaction_template_robustness(self):
        """Test that interaction templates handle edge cases"""
        interaction_templates = self.templates.get_category_templates(TemplateCategory.INTERACTION.value)

        # Filter application should handle different filter types
        filter_template = interaction_templates["filter_application"]
        assert "exact text match" in filter_template
        assert "input/select elements" in filter_template
        assert "checkbox" in filter_template and "radio" in filter_template

        # Pagination should handle different pagination patterns
        pagination_template = interaction_templates["pagination_navigation"]
        assert "next_page_selectors = [" in pagination_template
        assert '"Next"' in pagination_template
        assert ".pagination-next" in pagination_template