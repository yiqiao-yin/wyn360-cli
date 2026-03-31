"""
WYN360 Hook System - Pre/post response hooks for validation and custom processing.

Hooks are callables that run at specific points in the request/response lifecycle:
  - pre_query: Before sending a message to the model
  - post_response: After receiving a response from the model
  - pre_tool: Before a tool is executed
  - post_tool: After a tool is executed
  - on_error: When an error occurs

Hooks can be registered programmatically or loaded from config.
"""

import time
import logging
from enum import Enum
from typing import List, Dict, Optional, Any, Callable, Awaitable, Union
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class HookPoint(Enum):
    PRE_QUERY = "pre_query"
    POST_RESPONSE = "post_response"
    PRE_TOOL = "pre_tool"
    POST_TOOL = "post_tool"
    ON_ERROR = "on_error"


@dataclass
class HookContext:
    """Context passed to hook functions."""
    hook_point: HookPoint
    message: str = ""
    response: str = ""
    tool_name: str = ""
    tool_args: Dict[str, Any] = field(default_factory=dict)
    tool_result: str = ""
    error: Optional[Exception] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HookResult:
    """Result returned by a hook."""
    # If True, stop processing further hooks at this point
    stop_chain: bool = False
    # Modified message (for pre_query hooks)
    modified_message: Optional[str] = None
    # Modified response (for post_response hooks)
    modified_response: Optional[str] = None
    # Additional messages to inject
    extra_messages: List[str] = field(default_factory=list)
    # Whether to block the action (for pre_tool hooks)
    block_action: bool = False
    block_reason: str = ""


# Hook function type: can be sync or async
HookFn = Callable[[HookContext], Union[HookResult, Awaitable[HookResult]]]


@dataclass
class RegisteredHook:
    """A registered hook with metadata."""
    name: str
    hook_point: HookPoint
    fn: HookFn
    priority: int = 0  # Lower runs first
    enabled: bool = True


class HookManager:
    """Manages registration and execution of hooks."""

    def __init__(self):
        self._hooks: Dict[HookPoint, List[RegisteredHook]] = {
            point: [] for point in HookPoint
        }
        self.execution_count: Dict[str, int] = {}
        self.total_execution_time: float = 0.0

    def register(self, name: str, hook_point: HookPoint, fn: HookFn,
                 priority: int = 0) -> RegisteredHook:
        """Register a new hook."""
        hook = RegisteredHook(
            name=name,
            hook_point=hook_point,
            fn=fn,
            priority=priority,
        )
        self._hooks[hook_point].append(hook)
        # Keep sorted by priority
        self._hooks[hook_point].sort(key=lambda h: h.priority)
        return hook

    def unregister(self, name: str, hook_point: Optional[HookPoint] = None):
        """Remove a hook by name, optionally from a specific point."""
        points = [hook_point] if hook_point else list(HookPoint)
        for point in points:
            self._hooks[point] = [h for h in self._hooks[point] if h.name != name]

    def enable(self, name: str, enabled: bool = True):
        """Enable or disable a hook by name."""
        for hooks in self._hooks.values():
            for hook in hooks:
                if hook.name == name:
                    hook.enabled = enabled

    async def execute(self, hook_point: HookPoint, context: HookContext) -> HookResult:
        """
        Execute all hooks registered for a given point.

        Returns the combined result of all hooks.
        """
        import asyncio
        import inspect

        combined = HookResult()
        hooks = [h for h in self._hooks[hook_point] if h.enabled]

        for hook in hooks:
            start = time.time()
            try:
                if inspect.iscoroutinefunction(hook.fn):
                    result = await hook.fn(context)
                else:
                    result = hook.fn(context)

                if result is None:
                    continue

                # Merge results
                if result.modified_message is not None:
                    combined.modified_message = result.modified_message
                    context.message = result.modified_message

                if result.modified_response is not None:
                    combined.modified_response = result.modified_response
                    context.response = result.modified_response

                combined.extra_messages.extend(result.extra_messages)

                if result.block_action:
                    combined.block_action = True
                    combined.block_reason = result.block_reason

                if result.stop_chain:
                    combined.stop_chain = True
                    break

            except Exception as e:
                logger.warning(f"Hook '{hook.name}' at {hook_point.value} failed: {e}")

            elapsed = time.time() - start
            self.total_execution_time += elapsed
            self.execution_count[hook.name] = self.execution_count.get(hook.name, 0) + 1

        return combined

    def list_hooks(self, hook_point: Optional[HookPoint] = None) -> List[RegisteredHook]:
        """List all registered hooks, optionally filtered by point."""
        if hook_point:
            return list(self._hooks[hook_point])
        all_hooks = []
        for hooks in self._hooks.values():
            all_hooks.extend(hooks)
        return all_hooks

    def get_stats(self) -> Dict[str, Any]:
        """Get hook execution statistics."""
        total_hooks = sum(len(hooks) for hooks in self._hooks.values())
        return {
            "total_registered": total_hooks,
            "execution_counts": dict(self.execution_count),
            "total_execution_time_ms": round(self.total_execution_time * 1000, 2),
        }

    def register_builtin_hooks(self):
        """Register default built-in hooks."""

        # Safety hook: warn about destructive file operations
        def safety_check(ctx: HookContext) -> HookResult:
            dangerous_patterns = ["rm -rf", "DROP TABLE", "DELETE FROM", "format c:"]
            for pattern in dangerous_patterns:
                if pattern.lower() in ctx.message.lower():
                    return HookResult(
                        extra_messages=[
                            f"Warning: Detected potentially destructive pattern '{pattern}' in the request."
                        ]
                    )
            return HookResult()

        self.register("builtin_safety_check", HookPoint.PRE_QUERY, safety_check, priority=-100)

        # Response length tracking hook
        def track_response_length(ctx: HookContext) -> HookResult:
            length = len(ctx.response) if ctx.response else 0
            if length > 50000:
                logger.info(f"Long response detected: {length} chars")
            return HookResult()

        self.register("builtin_response_tracker", HookPoint.POST_RESPONSE, track_response_length, priority=100)
