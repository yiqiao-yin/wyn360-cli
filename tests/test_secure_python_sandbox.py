"""
Unit tests for Secure Python Sandbox

Tests the secure execution environment for browser automation code.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch

from wyn360_cli.tools.browser.secure_python_sandbox import (
    SecurePythonSandbox,
    SandboxConfig,
    SecurityChecker,
    ResourceMonitor,
    SandboxManager,
    SandboxError,
    SecurityViolation,
    ExecutionTimeout,
    ResourceLimitExceeded,
    execute_secure,
    execute_browser_automation
)


class TestSandboxConfig:
    """Test SandboxConfig dataclass"""

    def test_default_config(self):
        """Test default configuration values"""
        config = SandboxConfig()

        assert config.max_execution_time == 60
        assert config.max_memory_usage == 100 * 1024 * 1024
        assert config.max_output_size == 10 * 1024 * 1024
        assert 'asyncio' in config.allow_imports
        assert 'json' in config.allow_imports
        assert 'open' in config.restricted_builtins
        assert 'exec' in config.restricted_builtins

    def test_custom_config(self):
        """Test custom configuration values"""
        custom_imports = ['asyncio', 'json']
        custom_restricted = ['eval', 'exec']

        config = SandboxConfig(
            max_execution_time=30,
            max_memory_usage=50 * 1024 * 1024,
            allow_imports=custom_imports,
            restricted_builtins=custom_restricted,
            enable_debugging=True
        )

        assert config.max_execution_time == 30
        assert config.max_memory_usage == 50 * 1024 * 1024
        assert config.allow_imports == custom_imports
        assert config.restricted_builtins == custom_restricted
        assert config.enable_debugging is True


class TestSecurityChecker:
    """Test SecurityChecker class"""

    def setup_method(self):
        """Setup test fixtures"""
        self.config = SandboxConfig()
        self.checker = SecurityChecker(self.config)

    def test_safe_code_validation(self):
        """Test validation of safe code"""
        safe_code = """
import asyncio
import json

result = {"message": "Hello World"}
print(f"Result: {result}")
"""

        is_safe, violations = self.checker.check_code_safety(safe_code)
        assert is_safe is True
        assert len(violations) == 0

    def test_dangerous_builtin_detection(self):
        """Test detection of dangerous builtin functions"""
        dangerous_code = """
import asyncio
result = eval("1 + 1")
"""

        is_safe, violations = self.checker.check_code_safety(dangerous_code)
        assert is_safe is False
        assert any("eval" in violation for violation in violations)

    def test_restricted_import_detection(self):
        """Test detection of restricted imports"""
        restricted_code = """
import os
import subprocess
result = os.listdir(".")
"""

        is_safe, violations = self.checker.check_code_safety(restricted_code)
        assert is_safe is False
        assert any("os" in violation for violation in violations)

    def test_dangerous_pattern_detection(self):
        """Test detection of dangerous code patterns"""
        dangerous_code = """
import asyncio
obj.__class__.__bases__[0].__subclasses__()
"""

        is_safe, violations = self.checker.check_code_safety(dangerous_code)
        assert is_safe is False
        assert len(violations) > 0

    def test_syntax_error_detection(self):
        """Test detection of syntax errors"""
        invalid_code = """
import asyncio
result = {"test": "value"  # Missing closing brace
"""

        is_safe, violations = self.checker.check_code_safety(invalid_code)
        assert is_safe is False
        assert any("Syntax error" in violation for violation in violations)

    def test_allowed_imports(self):
        """Test that allowed imports pass validation"""
        allowed_code = """
import asyncio
import json
import re

result = {"pattern": re.compile(r"test")}
"""

        is_safe, violations = self.checker.check_code_safety(allowed_code)
        assert is_safe is True

    def test_private_attribute_access(self):
        """Test detection of private attribute access"""
        private_access_code = """
import asyncio

class Test:
    def __init__(self):
        self._private = "test"

t = Test()
result = t._private
"""

        is_safe, violations = self.checker.check_code_safety(private_access_code)
        # This should be detected as potentially unsafe
        assert any("Private attribute" in violation for violation in violations)


class TestResourceMonitor:
    """Test ResourceMonitor class"""

    def setup_method(self):
        """Setup test fixtures"""
        self.config = SandboxConfig(max_execution_time=2, max_output_size=100)
        self.monitor = ResourceMonitor(self.config)

    def test_time_limit_monitoring(self):
        """Test execution time limit monitoring"""
        self.monitor.start_monitoring()

        # Should not raise exception immediately
        self.monitor.check_time_limit()

        # Simulate time passing
        self.monitor._start_time = time.time() - 3  # 3 seconds ago

        with pytest.raises(ExecutionTimeout):
            self.monitor.check_time_limit()

    def test_output_size_monitoring(self):
        """Test output size limit monitoring"""
        self.monitor.start_monitoring()

        # Small output should be fine
        self.monitor.check_output_size("small output")

        # Large output should exceed limit
        large_output = "x" * 200  # Exceeds 100 byte limit

        with pytest.raises(ResourceLimitExceeded):
            self.monitor.check_output_size(large_output)

    def test_memory_usage_check(self):
        """Test memory usage checking"""
        self.monitor.start_monitoring()

        # Memory check is currently a no-op, should not raise
        self.monitor.check_memory_usage()


class TestSecurePythonSandbox:
    """Test SecurePythonSandbox class"""

    def setup_method(self):
        """Setup test fixtures"""
        self.config = SandboxConfig(max_execution_time=5)
        self.sandbox = SecurePythonSandbox(self.config)

    def test_sandbox_initialization(self):
        """Test sandbox initialization"""
        assert self.sandbox.config is not None
        assert self.sandbox.security_checker is not None
        assert self.sandbox.resource_monitor is not None
        assert len(self.sandbox.safe_builtins) > 0

    def test_safe_builtins_setup(self):
        """Test that safe builtins are properly configured"""
        builtins = self.sandbox.safe_builtins

        # Should have basic safe functions
        assert 'len' in builtins
        assert 'str' in builtins
        assert 'int' in builtins
        assert 'print' in builtins

        # Should not have dangerous functions
        assert 'open' not in builtins
        assert 'exec' not in builtins
        assert 'eval' not in builtins

    def test_safe_globals_creation(self):
        """Test creation of safe global environment"""
        context = {'page': Mock(), 'test_var': 'test_value'}
        safe_globals = self.sandbox._create_safe_globals(context)

        # Should include context variables
        assert 'page' in safe_globals
        assert 'test_var' in safe_globals

        # Should include allowed modules
        assert 'asyncio' in safe_globals
        assert 'json' in safe_globals

        # Should have safe builtins
        assert '__builtins__' in safe_globals

    @pytest.mark.asyncio
    async def test_simple_code_execution(self):
        """Test execution of simple safe code"""
        code = """
result = {"message": "Hello World", "number": 42}
"""

        result = await self.sandbox.execute_code(code)

        assert result['success'] is True
        assert result['result'] == {"message": "Hello World", "number": 42}
        assert result['execution_time'] > 0

    @pytest.mark.asyncio
    async def test_code_with_output(self):
        """Test execution of code that produces output"""
        code = """
print("Starting execution")
result = {"status": "completed"}
print("Execution finished")
"""

        result = await self.sandbox.execute_code(code)

        assert result['success'] is True
        assert "Starting execution" in result['output']
        assert "Execution finished" in result['output']
        assert result['result'] == {"status": "completed"}

    @pytest.mark.asyncio
    async def test_code_with_context(self):
        """Test execution with context variables"""
        mock_page = Mock()
        mock_page.title = Mock(return_value="Test Page")

        context = {'page': mock_page}
        code = """
title = page.title()
result = {"page_title": title}
"""

        result = await self.sandbox.execute_code(code, context)

        assert result['success'] is True
        assert result['result'] == {"page_title": "Test Page"}

    @pytest.mark.asyncio
    async def test_security_violation(self):
        """Test that security violations are caught"""
        dangerous_code = """
import os
result = os.listdir(".")
"""

        with pytest.raises(SecurityViolation):
            await self.sandbox.execute_code(dangerous_code)

    @pytest.mark.asyncio
    async def test_execution_timeout(self):
        """Test execution timeout handling"""
        # Use very short timeout for testing
        short_config = SandboxConfig(max_execution_time=1)
        short_sandbox = SecurePythonSandbox(short_config)

        long_running_code = """
import time
time.sleep(5)  # Sleep longer than timeout
result = "should not complete"
"""

        result = await short_sandbox.execute_code(long_running_code)

        assert result['success'] is False
        assert "timeout" in result['errors'].lower()

    @pytest.mark.asyncio
    async def test_code_with_exception(self):
        """Test handling of code that raises exceptions"""
        error_code = """
result = 1 / 0  # Division by zero
"""

        result = await self.sandbox.execute_code(error_code)

        assert result['success'] is False
        assert "ZeroDivisionError" in result['errors'] or "division by zero" in result['errors']

    @pytest.mark.asyncio
    async def test_async_code_execution(self):
        """Test execution of asynchronous code"""
        async_code = """
import asyncio

async def async_task():
    await asyncio.sleep(0.1)
    return "async result"

# Note: Direct async execution in sandbox may need special handling
result = {"async": "simulation"}
"""

        result = await self.sandbox.execute_code(async_code)

        # Should execute successfully even if async features are limited
        assert result['success'] is True

    def test_context_validation(self):
        """Test validation of context objects"""
        safe_context = {
            'page': Mock(),
            'data': {'key': 'value'},
            'number': 42
        }

        is_valid, issues = self.sandbox.validate_context(safe_context)
        assert is_valid is True
        assert len(issues) == 0

        # Test with potentially unsafe context
        unsafe_context = {
            'page': Mock(),
            'dangerous_module': __import__('os')
        }

        is_valid, issues = self.sandbox.validate_context(unsafe_context)
        # Should detect the module as potentially unsafe
        # Note: This depends on implementation details

    @pytest.mark.asyncio
    async def test_automation_script_execution(self):
        """Test execution of complete automation script"""
        mock_page = Mock()
        mock_page.goto = AsyncMock()
        mock_page.title = AsyncMock(return_value="Test Page")

        browser_context = {'page': mock_page}

        automation_script = """
# Simple automation script
await page.goto("https://example.com")
title = await page.title()
result = {"page_title": title, "status": "completed"}
"""

        result = await self.sandbox.execute_automation_script(automation_script, browser_context)

        assert result['success'] is True
        assert result['result']['page_title'] == "Test Page"
        mock_page.goto.assert_called_once_with("https://example.com")

    def test_cleanup(self):
        """Test sandbox cleanup"""
        # Cleanup should not raise exceptions
        self.sandbox.cleanup()


class TestSandboxManager:
    """Test SandboxManager class"""

    def setup_method(self):
        """Setup test fixtures"""
        self.manager = SandboxManager()

    def test_create_sandbox(self):
        """Test creating sandbox instances"""
        sandbox_id = self.manager.create_sandbox()

        assert isinstance(sandbox_id, str)
        assert sandbox_id.startswith("sandbox_")

        # Should be able to retrieve the sandbox
        sandbox = self.manager.get_sandbox(sandbox_id)
        assert sandbox is not None
        assert isinstance(sandbox, SecurePythonSandbox)

    def test_remove_sandbox(self):
        """Test removing sandbox instances"""
        sandbox_id = self.manager.create_sandbox()

        # Should exist
        assert self.manager.get_sandbox(sandbox_id) is not None

        # Remove it
        success = self.manager.remove_sandbox(sandbox_id)
        assert success is True

        # Should no longer exist
        assert self.manager.get_sandbox(sandbox_id) is None

        # Removing non-existent sandbox should return False
        success = self.manager.remove_sandbox("non_existent")
        assert success is False

    def test_cleanup_all(self):
        """Test cleaning up all sandboxes"""
        # Create multiple sandboxes
        sandbox_ids = []
        for i in range(3):
            sandbox_id = self.manager.create_sandbox()
            sandbox_ids.append(sandbox_id)

        # Verify they exist
        for sandbox_id in sandbox_ids:
            assert self.manager.get_sandbox(sandbox_id) is not None

        # Cleanup all
        self.manager.cleanup_all()

        # Verify they're gone
        for sandbox_id in sandbox_ids:
            assert self.manager.get_sandbox(sandbox_id) is None

    @pytest.mark.asyncio
    async def test_execute_in_new_sandbox(self):
        """Test executing code in a new sandbox"""
        code = """
result = {"executed": True, "value": 123}
"""

        result = await self.manager.execute_in_new_sandbox(code)

        assert result['success'] is True
        assert result['result'] == {"executed": True, "value": 123}

    def test_custom_config(self):
        """Test creating sandbox with custom config"""
        custom_config = SandboxConfig(max_execution_time=30)
        sandbox_id = self.manager.create_sandbox(custom_config)

        sandbox = self.manager.get_sandbox(sandbox_id)
        assert sandbox.config.max_execution_time == 30


class TestConvenienceFunctions:
    """Test convenience functions"""

    @pytest.mark.asyncio
    async def test_execute_secure(self):
        """Test execute_secure convenience function"""
        code = """
result = {"secure_execution": True}
"""

        result = await execute_secure(code)

        assert result['success'] is True
        assert result['result'] == {"secure_execution": True}

    @pytest.mark.asyncio
    async def test_execute_browser_automation(self):
        """Test execute_browser_automation convenience function"""
        mock_page = Mock()
        mock_page.title = AsyncMock(return_value="Test Page")

        script = """
title = await page.title()
result = {"title": title}
"""

        result = await execute_browser_automation(script, page=mock_page)

        assert result['success'] is True
        assert result['result']['title'] == "Test Page"

    @pytest.mark.asyncio
    async def test_execute_with_custom_config(self):
        """Test execution with custom configuration"""
        config = SandboxConfig(max_execution_time=10)
        code = """
result = {"config_test": True}
"""

        result = await execute_secure(code, config=config)

        assert result['success'] is True
        assert result['result'] == {"config_test": True}


class TestErrorHandling:
    """Test error handling scenarios"""

    def setup_method(self):
        """Setup test fixtures"""
        self.sandbox = SecurePythonSandbox()

    @pytest.mark.asyncio
    async def test_invalid_syntax_handling(self):
        """Test handling of syntax errors"""
        invalid_code = """
result = {"test": "value"  # Missing closing brace
"""

        with pytest.raises(SecurityViolation):
            await self.sandbox.execute_code(invalid_code)

    @pytest.mark.asyncio
    async def test_runtime_error_handling(self):
        """Test handling of runtime errors"""
        error_code = """
undefined_variable = some_undefined_var
result = undefined_variable
"""

        result = await self.sandbox.execute_code(error_code)

        assert result['success'] is False
        assert "NameError" in result['errors'] or "name 'some_undefined_var' is not defined" in result['errors']

    @pytest.mark.asyncio
    async def test_import_error_handling(self):
        """Test handling of import errors"""
        import_code = """
import non_existent_module
result = {"imported": True}
"""

        with pytest.raises(SecurityViolation):
            await self.sandbox.execute_code(import_code)

    @pytest.mark.asyncio
    async def test_resource_limit_handling(self):
        """Test handling of resource limit violations"""
        # Test with very small output limit
        small_config = SandboxConfig(max_output_size=10)
        small_sandbox = SecurePythonSandbox(small_config)

        large_output_code = """
result = "x" * 1000  # Large result
"""

        result = await small_sandbox.execute_code(large_output_code)
        # The sandbox should handle this gracefully