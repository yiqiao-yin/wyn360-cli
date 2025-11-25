"""
Secure Python Sandbox for Browser Automation

This module implements a secure Python execution environment for running
generated automation code safely without requiring Docker or external services.
"""

import ast
import asyncio
import sys
import io
import contextlib
import traceback
import threading
import time
import gc
from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum
import builtins
import json
import re


class SandboxError(Exception):
    """Exception raised by sandbox execution"""
    pass


class SecurityViolation(SandboxError):
    """Exception raised when code violates security restrictions"""
    pass


class ExecutionTimeout(SandboxError):
    """Exception raised when execution exceeds time limit"""
    pass


class ResourceLimitExceeded(SandboxError):
    """Exception raised when resource limits are exceeded"""
    pass


@dataclass
class SandboxConfig:
    """Configuration for the secure Python sandbox"""
    max_execution_time: int = 60  # seconds
    max_memory_usage: int = 100 * 1024 * 1024  # 100MB
    max_output_size: int = 10 * 1024 * 1024  # 10MB
    allow_imports: List[str] = None
    restricted_builtins: List[str] = None
    enable_debugging: bool = False

    def __post_init__(self):
        if self.allow_imports is None:
            self.allow_imports = [
                'asyncio', 'json', 're', 'time', 'datetime',
                'math', 'random', 'urllib.parse', 'base64'
            ]
        if self.restricted_builtins is None:
            self.restricted_builtins = [
                'open', 'input', 'raw_input', 'file', 'execfile',
                'reload', 'compile', 'eval', 'exec',
                'vars', 'locals', 'globals', 'dir', 'getattr',
                'setattr', 'delattr', 'hasattr', 'callable'
            ]


class SecurityChecker:
    """Checks code for security violations before execution"""

    def __init__(self, config: SandboxConfig):
        self.config = config
        self._dangerous_patterns = [
            r'__.*__',  # Double underscore methods
            r'\.im_.*',  # Internal method access
            r'\.func_.*',  # Function internals
            r'\.gi_.*',  # Generator internals
            r'subprocess',  # Process execution
            r'os\.',  # Operating system access
            r'sys\.',  # System access (except allowed)
            r'importlib',  # Dynamic imports
            r'builtins',  # Builtin manipulation
            r'globals\(',  # Global scope access
            r'locals\(',  # Local scope access
            r'exec\(',  # Dynamic execution
            r'eval\(',  # Dynamic evaluation
        ]

    def check_code_safety(self, code: str) -> Tuple[bool, List[str]]:
        """Check if code is safe to execute"""
        violations = []

        try:
            # Parse AST to check for dangerous constructs
            tree = ast.parse(code)
            violations.extend(self._check_ast_safety(tree))

            # Check for dangerous patterns in raw code
            violations.extend(self._check_pattern_safety(code))

            # Check imports
            violations.extend(self._check_imports(tree))

        except SyntaxError as e:
            violations.append(f"Syntax error: {e}")

        return len(violations) == 0, violations

    def _check_ast_safety(self, tree: ast.AST) -> List[str]:
        """Check AST nodes for security violations"""
        violations = []

        for node in ast.walk(tree):
            # Check for dangerous function calls
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in self.config.restricted_builtins:
                        violations.append(f"Restricted builtin: {node.func.id}")

            # Check for attribute access that might be dangerous
            elif isinstance(node, ast.Attribute):
                attr_name = node.attr
                # Allow some common safe attributes like 'sleep' for time module
                if attr_name.startswith('_') and attr_name not in ['__name__', '__doc__']:
                    violations.append(f"Private attribute access: {attr_name}")

            # Check for imports
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                pass  # Handled separately in _check_imports

        return violations

    def _check_pattern_safety(self, code: str) -> List[str]:
        """Check code patterns for security violations"""
        violations = []

        for pattern in self._dangerous_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                violations.append(f"Dangerous pattern detected: {pattern}")

        return violations

    def _check_imports(self, tree: ast.AST) -> List[str]:
        """Check if imports are allowed"""
        violations = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name not in self.config.allow_imports:
                        violations.append(f"Restricted import: {alias.name}")

            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module not in self.config.allow_imports:
                    violations.append(f"Restricted import: {node.module}")

        return violations


class ResourceMonitor:
    """Monitors resource usage during code execution"""

    def __init__(self, config: SandboxConfig):
        self.config = config
        self._start_time = None
        self._output_size = 0

    def start_monitoring(self):
        """Start monitoring resource usage"""
        self._start_time = time.time()
        self._output_size = 0

    def check_time_limit(self):
        """Check if execution time limit is exceeded"""
        if self._start_time is None:
            return

        elapsed = time.time() - self._start_time
        if elapsed > self.config.max_execution_time:
            raise ExecutionTimeout(f"Execution exceeded {self.config.max_execution_time} seconds")

    def check_memory_usage(self):
        """Check memory usage (basic implementation)"""
        # Note: This is a simplified memory check
        # In a production environment, you might want to use psutil
        pass

    def check_output_size(self, output: str):
        """Check if output size limit is exceeded"""
        self._output_size += len(output.encode('utf-8'))
        if self._output_size > self.config.max_output_size:
            raise ResourceLimitExceeded(f"Output exceeded {self.config.max_output_size} bytes")


class SecurePythonSandbox:
    """
    Secure Python sandbox for executing browser automation code
    """

    def __init__(self, config: Optional[SandboxConfig] = None):
        self.config = config or SandboxConfig()
        self.security_checker = SecurityChecker(self.config)
        self.resource_monitor = ResourceMonitor(self.config)
        self._setup_restricted_environment()

    def _setup_restricted_environment(self):
        """Setup restricted execution environment"""
        # Create safe builtins
        self.safe_builtins = {}

        # Allow basic safe builtins
        safe_builtin_names = [
            'abs', 'all', 'any', 'bool', 'chr', 'dict', 'enumerate',
            'float', 'int', 'len', 'list', 'max', 'min', 'ord',
            'range', 'reversed', 'round', 'set', 'sorted', 'str',
            'sum', 'tuple', 'type', 'zip', 'isinstance', 'issubclass',
            'print', 'format'
        ]

        for name in safe_builtin_names:
            if hasattr(builtins, name):
                self.safe_builtins[name] = getattr(builtins, name)

        # Add safe versions of potentially dangerous functions
        # We need __import__ for modules to work, but in a controlled way
        self.safe_builtins['__import__'] = __import__
        self.safe_builtins['__builtins__'] = self.safe_builtins

    def _create_safe_globals(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create a safe global environment for code execution"""
        safe_globals = {
            '__builtins__': self.safe_builtins,
            '__name__': '__sandbox__',
            '__doc__': None,
        }

        # Add allowed modules
        for module_name in self.config.allow_imports:
            try:
                module = __import__(module_name)
                safe_globals[module_name] = module
            except ImportError:
                pass  # Module not available, skip

        # Add context variables (browser objects, etc.)
        safe_globals.update(context)

        return safe_globals

    async def execute_code(self,
                          code: str,
                          context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute code in secure sandbox environment

        Args:
            code: Python code to execute
            context: Context variables (page, browser, etc.)

        Returns:
            Execution result with output, errors, and return value
        """
        if context is None:
            context = {}

        # Check code safety first
        is_safe, violations = self.security_checker.check_code_safety(code)
        if not is_safe:
            raise SecurityViolation(f"Code safety violations: {violations}")

        # Setup execution environment
        safe_globals = self._create_safe_globals(context)
        local_vars = {}

        # Capture output
        output_buffer = io.StringIO()
        error_buffer = io.StringIO()

        # Start resource monitoring
        self.resource_monitor.start_monitoring()

        execution_result = {
            'success': False,
            'result': None,
            'output': '',
            'errors': '',
            'execution_time': 0,
            'resource_usage': {}
        }

        start_time = time.time()

        try:
            # Execute in thread to enable timeout control
            result = await self._execute_with_timeout(
                code, safe_globals, local_vars, output_buffer, error_buffer
            )

            execution_result.update({
                'success': True,
                'result': result,
                'output': output_buffer.getvalue(),
                'errors': error_buffer.getvalue(),
                'execution_time': time.time() - start_time
            })

        except ExecutionTimeout:
            execution_result.update({
                'success': False,
                'errors': f"Execution timeout after {self.config.max_execution_time} seconds"
            })

        except SecurityViolation as e:
            execution_result.update({
                'success': False,
                'errors': f"Security violation: {e}"
            })

        except Exception as e:
            execution_result.update({
                'success': False,
                'errors': f"Execution error: {e}",
                'output': output_buffer.getvalue()
            })

        finally:
            execution_result['execution_time'] = time.time() - start_time

        return execution_result

    async def _execute_with_timeout(self,
                                   code: str,
                                   safe_globals: Dict[str, Any],
                                   local_vars: Dict[str, Any],
                                   output_buffer: io.StringIO,
                                   error_buffer: io.StringIO) -> Any:
        """Execute code with timeout control"""

        execution_complete = asyncio.Event()
        execution_result = {'value': None, 'exception': None}

        def execute_in_thread():
            try:
                # Redirect stdout and stderr
                with contextlib.redirect_stdout(output_buffer), \
                     contextlib.redirect_stderr(error_buffer):

                    # Check if code contains async/await - if so, wrap it
                    if 'await ' in code or 'async def' in code:
                        # For async code, we need to run it in the event loop
                        if 'async def' not in code:
                            # Wrap the code in an async function
                            indented_code = '\n'.join('    ' + line if line.strip() else line for line in code.split('\n'))
                            wrapped_code = f"""
import asyncio

_result_holder = None

async def _sandbox_async_executor():
    global _result_holder
{indented_code}
    try:
        _result_holder = result
    except NameError:
        _result_holder = None

asyncio.run(_sandbox_async_executor())
result = _result_holder
"""
                        else:
                            # Code already has async def, just execute it
                            wrapped_code = code

                        exec(wrapped_code, safe_globals, local_vars)
                    else:
                        # Execute the code normally
                        exec(code, safe_globals, local_vars)

                    # Get result if available
                    if 'result' in local_vars:
                        execution_result['value'] = local_vars['result']

            except Exception as e:
                execution_result['exception'] = e

            finally:
                execution_complete.set()

        # Start execution in thread
        thread = threading.Thread(target=execute_in_thread, daemon=True)
        thread.start()

        # Wait for completion or timeout
        try:
            await asyncio.wait_for(
                execution_complete.wait(),
                timeout=self.config.max_execution_time
            )
        except asyncio.TimeoutError:
            raise ExecutionTimeout(f"Code execution exceeded {self.config.max_execution_time} seconds")

        # Check for exceptions
        if execution_result['exception']:
            raise execution_result['exception']

        return execution_result['value']

    def validate_context(self, context: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate that context objects are safe to use"""
        issues = []

        for key, value in context.items():
            # Check for dangerous object types
            if hasattr(value, '__class__'):
                class_name = value.__class__.__name__
                if class_name in ['module', 'function', 'method']:
                    # Allow specific safe modules/functions
                    if key not in ['page', 'browser', 'context', 'asyncio', 'json', 're']:
                        issues.append(f"Potentially unsafe context object: {key} ({class_name})")

        return len(issues) == 0, issues

    async def execute_automation_script(self,
                                      script_code: str,
                                      browser_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a complete browser automation script

        Args:
            script_code: Complete automation script code
            browser_context: Browser objects (page, browser, etc.)

        Returns:
            Execution result with automation output
        """
        # Validate browser context
        is_valid, issues = self.validate_context(browser_context)
        if not is_valid:
            raise SecurityViolation(f"Unsafe browser context: {issues}")

        # Execute the automation script
        result = await self.execute_code(script_code, browser_context)

        # Post-process result
        if result['success'] and result['result'] is not None:
            # Ensure result is JSON serializable
            try:
                json.dumps(result['result'])
            except (TypeError, ValueError):
                # Convert non-serializable result to string
                result['result'] = str(result['result'])

        return result

    def cleanup(self):
        """Cleanup sandbox resources"""
        # Force garbage collection
        gc.collect()

        # Clear any cached modules
        # Note: In a production environment, you might want to
        # be more aggressive about cleanup


class SandboxManager:
    """
    Manager for multiple sandbox instances
    """

    def __init__(self, default_config: Optional[SandboxConfig] = None):
        self.default_config = default_config or SandboxConfig()
        self._sandboxes = {}
        self._sandbox_counter = 0

    def create_sandbox(self, config: Optional[SandboxConfig] = None) -> str:
        """Create a new sandbox instance and return its ID"""
        sandbox_id = f"sandbox_{self._sandbox_counter}"
        self._sandbox_counter += 1

        sandbox_config = config or self.default_config
        sandbox = SecurePythonSandbox(sandbox_config)

        self._sandboxes[sandbox_id] = sandbox
        return sandbox_id

    def get_sandbox(self, sandbox_id: str) -> Optional[SecurePythonSandbox]:
        """Get sandbox by ID"""
        return self._sandboxes.get(sandbox_id)

    def remove_sandbox(self, sandbox_id: str) -> bool:
        """Remove and cleanup sandbox"""
        if sandbox_id in self._sandboxes:
            sandbox = self._sandboxes[sandbox_id]
            sandbox.cleanup()
            del self._sandboxes[sandbox_id]
            return True
        return False

    def cleanup_all(self):
        """Cleanup all sandboxes"""
        for sandbox_id in list(self._sandboxes.keys()):
            self.remove_sandbox(sandbox_id)

    async def execute_in_new_sandbox(self,
                                    code: str,
                                    context: Optional[Dict[str, Any]] = None,
                                    config: Optional[SandboxConfig] = None) -> Dict[str, Any]:
        """Execute code in a new sandbox instance"""
        sandbox_id = self.create_sandbox(config)

        try:
            sandbox = self.get_sandbox(sandbox_id)
            result = await sandbox.execute_code(code, context)
            return result

        finally:
            self.remove_sandbox(sandbox_id)


# Global sandbox manager instance
sandbox_manager = SandboxManager()


# Convenience functions for easy use
async def execute_secure(code: str,
                        context: Optional[Dict[str, Any]] = None,
                        config: Optional[SandboxConfig] = None) -> Dict[str, Any]:
    """
    Execute code securely in an isolated sandbox

    Args:
        code: Python code to execute
        context: Context variables
        config: Sandbox configuration

    Returns:
        Execution result
    """
    return await sandbox_manager.execute_in_new_sandbox(code, context, config)


async def execute_browser_automation(script_code: str,
                                    page=None,
                                    browser=None,
                                    config: Optional[SandboxConfig] = None) -> Dict[str, Any]:
    """
    Execute browser automation script securely

    Args:
        script_code: Browser automation script
        page: Playwright page object
        browser: Playwright browser object
        config: Sandbox configuration

    Returns:
        Automation result
    """
    browser_context = {}
    if page is not None:
        browser_context['page'] = page
    if browser is not None:
        browser_context['browser'] = browser

    sandbox_id = sandbox_manager.create_sandbox(config)

    try:
        sandbox = sandbox_manager.get_sandbox(sandbox_id)
        result = await sandbox.execute_automation_script(script_code, browser_context)
        return result

    finally:
        sandbox_manager.remove_sandbox(sandbox_id)