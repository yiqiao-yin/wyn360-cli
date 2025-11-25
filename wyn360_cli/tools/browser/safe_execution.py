"""
Safe Execution Wrapper for Browser Automation

This module provides a high-level wrapper for safely executing
browser automation code using the secure Python sandbox.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict

from .secure_python_sandbox import (
    SecurePythonSandbox,
    SandboxConfig,
    SandboxError,
    SecurityViolation,
    ExecutionTimeout,
    ResourceLimitExceeded
)
from .enhanced_code_generator import EnhancedCodeGenerator, CodeGenerationContext


@dataclass
class ExecutionConfig:
    """Configuration for safe execution"""
    max_execution_time: int = 60
    max_memory_usage: int = 100 * 1024 * 1024  # 100MB
    enable_debugging: bool = False
    allow_browser_interaction: bool = True
    allow_network_access: bool = True
    sandbox_mode: str = "strict"  # strict, permissive, custom


@dataclass
class ExecutionResult:
    """Result of safe code execution"""
    success: bool
    result: Any = None
    output: str = ""
    errors: str = ""
    execution_time: float = 0.0
    approach_used: str = "sandbox"
    security_violations: List[str] = None
    resource_usage: Dict[str, Any] = None

    def __post_init__(self):
        if self.security_violations is None:
            self.security_violations = []
        if self.resource_usage is None:
            self.resource_usage = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary"""
        return asdict(self)


class SafeExecutionWrapper:
    """
    High-level wrapper for safe browser automation execution
    """

    def __init__(self, config: Optional[ExecutionConfig] = None):
        self.config = config or ExecutionConfig()
        self.code_generator = EnhancedCodeGenerator()
        self.logger = logging.getLogger(__name__)

        # Setup sandbox configuration
        self.sandbox_config = self._create_sandbox_config()

    def _create_sandbox_config(self) -> SandboxConfig:
        """Create sandbox configuration from execution config"""
        allow_imports = [
            'asyncio', 'json', 're', 'time', 'datetime',
            'math', 'random', 'urllib.parse', 'base64'
        ]

        if self.config.allow_network_access:
            allow_imports.extend(['urllib', 'requests', 'aiohttp'])

        return SandboxConfig(
            max_execution_time=self.config.max_execution_time,
            max_memory_usage=self.config.max_memory_usage,
            enable_debugging=self.config.enable_debugging,
            allow_imports=allow_imports
        )

    async def execute_generated_code(self,
                                   context: CodeGenerationContext,
                                   browser_context: Dict[str, Any]) -> ExecutionResult:
        """
        Generate and execute automation code safely

        Args:
            context: Code generation context
            browser_context: Browser objects (page, browser, etc.)

        Returns:
            Execution result
        """
        try:
            # Generate automation code
            self.logger.info(f"Generating code for task: {context.task_description}")
            automation_code = await self.code_generator.generate_automation_code(context)

            # Execute the generated code
            return await self.execute_code_safely(automation_code, browser_context)

        except Exception as e:
            self.logger.error(f"Code generation failed: {e}")
            return ExecutionResult(
                success=False,
                errors=f"Code generation failed: {e}",
                approach_used="generation_failed"
            )

    async def execute_code_safely(self,
                                code: str,
                                browser_context: Dict[str, Any]) -> ExecutionResult:
        """
        Execute automation code in secure sandbox

        Args:
            code: Python automation code
            browser_context: Browser objects

        Returns:
            Execution result
        """
        sandbox = None
        execution_start = asyncio.get_event_loop().time()

        try:
            # Create sandbox with configuration
            sandbox = SecurePythonSandbox(self.sandbox_config)

            self.logger.info("Executing automation code in secure sandbox")

            # Execute the code
            sandbox_result = await sandbox.execute_automation_script(code, browser_context)

            execution_time = asyncio.get_event_loop().time() - execution_start

            # Convert sandbox result to execution result
            return ExecutionResult(
                success=sandbox_result['success'],
                result=sandbox_result.get('result'),
                output=sandbox_result.get('output', ''),
                errors=sandbox_result.get('errors', ''),
                execution_time=execution_time,
                approach_used="secure_sandbox",
                resource_usage=sandbox_result.get('resource_usage', {})
            )

        except SecurityViolation as e:
            self.logger.warning(f"Security violation during execution: {e}")
            return ExecutionResult(
                success=False,
                errors=f"Security violation: {e}",
                execution_time=asyncio.get_event_loop().time() - execution_start,
                approach_used="security_blocked",
                security_violations=[str(e)]
            )

        except ExecutionTimeout as e:
            self.logger.warning(f"Execution timeout: {e}")
            return ExecutionResult(
                success=False,
                errors=f"Execution timeout: {e}",
                execution_time=self.config.max_execution_time,
                approach_used="timeout"
            )

        except ResourceLimitExceeded as e:
            self.logger.warning(f"Resource limit exceeded: {e}")
            return ExecutionResult(
                success=False,
                errors=f"Resource limit exceeded: {e}",
                execution_time=asyncio.get_event_loop().time() - execution_start,
                approach_used="resource_limited"
            )

        except Exception as e:
            self.logger.error(f"Unexpected execution error: {e}")
            return ExecutionResult(
                success=False,
                errors=f"Execution error: {e}",
                execution_time=asyncio.get_event_loop().time() - execution_start,
                approach_used="error"
            )

        finally:
            # Cleanup sandbox resources
            if sandbox:
                sandbox.cleanup()

    async def execute_with_fallback(self,
                                  context: CodeGenerationContext,
                                  browser_context: Dict[str, Any],
                                  fallback_strategies: Optional[List[str]] = None) -> ExecutionResult:
        """
        Execute automation with fallback strategies

        Args:
            context: Code generation context
            browser_context: Browser objects
            fallback_strategies: List of fallback approaches to try

        Returns:
            Execution result from successful approach or last failure
        """
        if fallback_strategies is None:
            fallback_strategies = ['secure_sandbox', 'direct_execution']

        last_result = None

        for strategy in fallback_strategies:
            try:
                if strategy == 'secure_sandbox':
                    result = await self.execute_generated_code(context, browser_context)

                elif strategy == 'direct_execution':
                    result = await self._execute_direct(context, browser_context)

                else:
                    self.logger.warning(f"Unknown fallback strategy: {strategy}")
                    continue

                if result.success:
                    self.logger.info(f"Execution successful with strategy: {strategy}")
                    return result

                last_result = result
                self.logger.warning(f"Strategy {strategy} failed: {result.errors}")

            except Exception as e:
                self.logger.error(f"Strategy {strategy} raised exception: {e}")
                last_result = ExecutionResult(
                    success=False,
                    errors=f"Strategy {strategy} failed: {e}",
                    approach_used=f"{strategy}_exception"
                )

        # If all strategies failed, return the last result
        return last_result or ExecutionResult(
            success=False,
            errors="All fallback strategies failed",
            approach_used="all_failed"
        )

    async def _execute_direct(self,
                            context: CodeGenerationContext,
                            browser_context: Dict[str, Any]) -> ExecutionResult:
        """
        Direct execution fallback (less secure but more compatible)

        This method executes code directly without sandboxing.
        Use only as a fallback when sandbox execution fails.
        """
        execution_start = asyncio.get_event_loop().time()

        try:
            self.logger.warning("Using direct execution fallback - reduced security")

            # Generate code
            automation_code = await self.code_generator.generate_automation_code(context)

            # Setup execution environment
            execution_globals = {
                '__builtins__': __builtins__,
                'asyncio': asyncio,
                'json': __import__('json'),
                're': __import__('re'),
                **browser_context
            }

            local_vars = {}

            # Execute code directly
            exec(automation_code, execution_globals, local_vars)

            execution_time = asyncio.get_event_loop().time() - execution_start

            # Get result
            result_value = local_vars.get('result')

            return ExecutionResult(
                success=True,
                result=result_value,
                execution_time=execution_time,
                approach_used="direct_execution"
            )

        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - execution_start
            self.logger.error(f"Direct execution failed: {e}")

            return ExecutionResult(
                success=False,
                errors=f"Direct execution failed: {e}",
                execution_time=execution_time,
                approach_used="direct_execution_failed"
            )

    def validate_browser_context(self, browser_context: Dict[str, Any]) -> List[str]:
        """
        Validate browser context for security

        Args:
            browser_context: Browser objects to validate

        Returns:
            List of validation issues (empty if valid)
        """
        issues = []

        required_keys = []
        if self.config.allow_browser_interaction:
            required_keys = ['page']

        # Check required keys
        for key in required_keys:
            if key not in browser_context:
                issues.append(f"Missing required browser context: {key}")

        # Check for dangerous objects
        dangerous_types = ['module', 'function', 'method']
        for key, value in browser_context.items():
            if hasattr(value, '__class__'):
                class_name = value.__class__.__name__
                if class_name in dangerous_types:
                    # Allow specific safe objects
                    if key not in ['page', 'browser', 'context']:
                        issues.append(f"Potentially unsafe object in context: {key} ({class_name})")

        return issues

    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics"""
        # This would typically track statistics across multiple executions
        # For now, return basic configuration info
        return {
            'config': asdict(self.config),
            'sandbox_config': {
                'max_execution_time': self.sandbox_config.max_execution_time,
                'max_memory_usage': self.sandbox_config.max_memory_usage,
                'allowed_imports': len(self.sandbox_config.allow_imports)
            }
        }


# Convenience functions
async def execute_automation_safely(
    task_description: str,
    url: str,
    browser_context: Dict[str, Any],
    config: Optional[ExecutionConfig] = None
) -> ExecutionResult:
    """
    Convenience function to execute automation safely

    Args:
        task_description: Description of automation task
        url: Target URL
        browser_context: Browser objects
        config: Execution configuration

    Returns:
        Execution result
    """
    executor = SafeExecutionWrapper(config)

    # Create code generation context
    generation_context = CodeGenerationContext(
        task_description=task_description,
        url=url
    )

    # Execute with fallback strategies
    return await executor.execute_with_fallback(generation_context, browser_context)


async def execute_code_with_sandbox(
    code: str,
    browser_context: Dict[str, Any],
    config: Optional[ExecutionConfig] = None
) -> ExecutionResult:
    """
    Execute pre-written code in sandbox

    Args:
        code: Python automation code
        browser_context: Browser objects
        config: Execution configuration

    Returns:
        Execution result
    """
    executor = SafeExecutionWrapper(config)
    return await executor.execute_code_safely(code, browser_context)