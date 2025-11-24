"""
Stagehand Code Generation System for WYN360 CLI

This module provides dynamic Stagehand code generation for complex browser automation
scenarios where DOM analysis confidence is medium but not sufficient for direct DOM manipulation.
"""

import os
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import json

try:
    import stagehand
    from stagehand import Stagehand, StagehandConfig, StagehandPage
    from stagehand import ActOptions, ExtractOptions, ObserveOptions
    from stagehand import ActResult, ExtractResult, ObserveResult
    HAS_STAGEHAND = True
except ImportError:
    HAS_STAGEHAND = False
    stagehand = None

logger = logging.getLogger(__name__)


class StagehandAvailability(Enum):
    """Stagehand availability status"""
    AVAILABLE = "available"
    NOT_INSTALLED = "not_installed"
    NOT_CONFIGURED = "not_configured"
    CONFIGURATION_ERROR = "configuration_error"


@dataclass
class StagehandPattern:
    """Represents a reusable Stagehand automation pattern"""
    pattern_id: str
    description: str
    stagehand_actions: List[Dict[str, Any]]
    success_count: int = 0
    failure_count: int = 0
    confidence_score: float = 0.0
    created_at: float = field(default_factory=lambda: asyncio.get_event_loop().time())
    last_used: Optional[float] = None

    @property
    def success_rate(self) -> float:
        """Calculate success rate for this pattern"""
        total = self.success_count + self.failure_count
        if total == 0:
            return 0.0
        return self.success_count / total


@dataclass
class StagehandExecutionResult:
    """Result from Stagehand code execution"""
    success: bool
    pattern_used: Optional[StagehandPattern]
    actions_performed: List[Dict[str, Any]]
    execution_time: float
    result_data: Dict[str, Any]
    error_message: Optional[str] = None
    token_usage: Optional[Dict[str, int]] = None


class StagehandCodeGenerator:
    """
    Generates and executes Stagehand automation code for browser tasks.

    This class serves as the middle layer between DOM analysis and vision fallback,
    providing AI-powered browser automation that's more reliable than brittle DOM
    selectors but more cost-effective than vision-based approaches.
    """

    def __init__(self):
        self.availability_status = self._check_availability()
        self.pattern_cache: Dict[str, StagehandPattern] = {}
        self.stagehand_instance: Optional[Stagehand] = None
        self.current_page: Optional[StagehandPage] = None
        self.is_configured = False

        if self.availability_status == StagehandAvailability.AVAILABLE:
            self._initialize_stagehand()

    def _check_availability(self) -> StagehandAvailability:
        """Check if Stagehand is available and properly configured"""
        if not HAS_STAGEHAND:
            logger.warning("Stagehand not available - stagehand-py package not installed")
            return StagehandAvailability.NOT_INSTALLED

        # Check for required environment variables (make them optional for now)
        required_vars = ['STAGEHAND_API_URL', 'BROWSERBASE_API_KEY']
        missing_vars = [var for var in required_vars if not os.getenv(var)]

        if missing_vars:
            logger.info(f"Stagehand not configured - missing environment variables: {missing_vars}")
            logger.info("Stagehand fallback will be disabled. To enable, set required environment variables.")
            return StagehandAvailability.NOT_CONFIGURED

        return StagehandAvailability.AVAILABLE

    def _initialize_stagehand(self) -> None:
        """Initialize Stagehand instance if available"""
        if self.availability_status != StagehandAvailability.AVAILABLE:
            return

        try:
            # Create basic configuration - can be expanded later
            config = StagehandConfig()

            # Initialize Stagehand instance (this would typically require API keys)
            # For now, we'll create a placeholder that tracks what would be done
            logger.info("Stagehand configuration initialized (placeholder mode)")
            self.is_configured = True

        except Exception as e:
            logger.error(f"Failed to initialize Stagehand: {e}")
            self.availability_status = StagehandAvailability.CONFIGURATION_ERROR

    def is_available(self) -> bool:
        """Check if Stagehand is available for use"""
        return self.availability_status == StagehandAvailability.AVAILABLE and self.is_configured

    def get_status_info(self) -> Dict[str, Any]:
        """Get detailed status information about Stagehand availability"""
        return {
            "status": self.availability_status.value,
            "is_configured": self.is_configured,
            "has_package": HAS_STAGEHAND,
            "pattern_cache_size": len(self.pattern_cache),
            "required_env_vars": {
                "STAGEHAND_API_URL": bool(os.getenv("STAGEHAND_API_URL")),
                "BROWSERBASE_API_KEY": bool(os.getenv("BROWSERBASE_API_KEY")),
                "MODEL_API_KEY": bool(os.getenv("MODEL_API_KEY", os.getenv("ANTHROPIC_API_KEY"))),
            }
        }

    async def generate_stagehand_code(
        self,
        url: str,
        task_description: str,
        dom_context: str,
        target_description: str,
        action_type: str,
        action_data: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Union[List[Dict[str, Any]], str]]:
        """
        Generate Stagehand automation code for the given task.

        Args:
            url: Target URL
            task_description: High-level description of what to accomplish
            dom_context: DOM analysis context from previous analysis
            target_description: Description of element to interact with
            action_type: Type of action (click, type, select, etc.)
            action_data: Additional data for the action

        Returns:
            Tuple of (success, actions_or_error_message)
        """
        if not self.is_available():
            return False, f"Stagehand not available: {self.availability_status.value}"

        try:
            # Check pattern cache first
            pattern_key = self._generate_pattern_key(task_description, action_type, target_description)
            if pattern_key in self.pattern_cache:
                pattern = self.pattern_cache[pattern_key]
                logger.info(f"Using cached Stagehand pattern: {pattern.pattern_id}")
                pattern.last_used = asyncio.get_event_loop().time()
                return True, pattern.stagehand_actions

            # Generate new Stagehand actions based on the task
            actions = await self._generate_new_actions(
                url, task_description, dom_context, target_description, action_type, action_data
            )

            # Cache the pattern for future use
            pattern = StagehandPattern(
                pattern_id=pattern_key,
                description=f"{action_type} on {target_description}",
                stagehand_actions=actions
            )
            self.pattern_cache[pattern_key] = pattern

            logger.info(f"Generated new Stagehand pattern: {pattern_key}")
            return True, actions

        except Exception as e:
            logger.error(f"Error generating Stagehand code: {e}")
            return False, str(e)

    async def _generate_new_actions(
        self,
        url: str,
        task_description: str,
        dom_context: str,
        target_description: str,
        action_type: str,
        action_data: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate new Stagehand actions for the task"""

        # For now, create a simulated Stagehand action sequence
        # In a real implementation, this would use the Stagehand API to generate actions
        actions = [
            {
                "type": "observe",
                "description": f"Observe page elements for: {target_description}",
                "options": {
                    "instruction": f"Find elements related to: {target_description}",
                    "useVision": False
                }
            }
        ]

        # Add the main action based on the action type
        if action_type.lower() == "click":
            actions.append({
                "type": "act",
                "description": f"Click on {target_description}",
                "options": {
                    "action": f"click on the {target_description}",
                    "useVision": False
                }
            })
        elif action_type.lower() == "type":
            text_to_type = action_data.get("text", "") if action_data else ""
            actions.append({
                "type": "act",
                "description": f"Type '{text_to_type}' into {target_description}",
                "options": {
                    "action": f"type '{text_to_type}' into the {target_description}",
                    "useVision": False
                }
            })
        elif action_type.lower() == "extract":
            actions.append({
                "type": "extract",
                "description": f"Extract data from {target_description}",
                "options": {
                    "instruction": f"extract relevant information from {target_description}",
                    "schema": action_data.get("schema") if action_data else {}
                }
            })
        else:
            actions.append({
                "type": "act",
                "description": f"Perform {action_type} on {target_description}",
                "options": {
                    "action": f"{action_type} the {target_description}",
                    "useVision": False
                }
            })

        # Add final observation to verify action completion
        actions.append({
            "type": "observe",
            "description": "Verify action completion",
            "options": {
                "instruction": f"Confirm that the {action_type} action on {target_description} was successful",
                "useVision": False
            }
        })

        return actions

    async def execute_stagehand_actions(
        self,
        url: str,
        actions: List[Dict[str, Any]],
        show_browser: bool = False
    ) -> StagehandExecutionResult:
        """
        Execute a sequence of Stagehand actions.

        Args:
            url: URL to navigate to
            actions: List of Stagehand actions to execute
            show_browser: Whether to show the browser window

        Returns:
            StagehandExecutionResult with execution details
        """
        if not self.is_available():
            return StagehandExecutionResult(
                success=False,
                pattern_used=None,
                actions_performed=[],
                execution_time=0.0,
                result_data={},
                error_message=f"Stagehand not available: {self.availability_status.value}"
            )

        start_time = asyncio.get_event_loop().time()

        try:
            # For now, simulate Stagehand execution
            # In a real implementation, this would use the actual Stagehand API

            logger.info(f"Simulating Stagehand execution for {len(actions)} actions at {url}")

            # Simulate some processing time
            await asyncio.sleep(0.1)

            # Simulate successful execution
            result_data = {
                "status": "completed",
                "url": url,
                "actions_count": len(actions),
                "simulated": True,
                "message": "Stagehand execution simulated - actual implementation requires API configuration"
            }

            execution_time = asyncio.get_event_loop().time() - start_time

            return StagehandExecutionResult(
                success=True,
                pattern_used=None,
                actions_performed=actions,
                execution_time=execution_time,
                result_data=result_data,
                error_message=None
            )

        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            logger.error(f"Error executing Stagehand actions: {e}")

            return StagehandExecutionResult(
                success=False,
                pattern_used=None,
                actions_performed=[],
                execution_time=execution_time,
                result_data={},
                error_message=str(e)
            )

    def _generate_pattern_key(
        self,
        task_description: str,
        action_type: str,
        target_description: str
    ) -> str:
        """Generate a unique key for caching patterns"""
        # Create a simple hash-like key from the task components
        import hashlib
        key_components = f"{task_description}|{action_type}|{target_description}".lower()
        return hashlib.md5(key_components.encode()).hexdigest()[:16]

    def update_pattern_success(self, pattern_key: str, success: bool) -> None:
        """Update success/failure statistics for a pattern"""
        if pattern_key in self.pattern_cache:
            pattern = self.pattern_cache[pattern_key]
            if success:
                pattern.success_count += 1
            else:
                pattern.failure_count += 1

            # Update confidence score based on success rate
            pattern.confidence_score = pattern.success_rate
            logger.info(f"Updated pattern {pattern_key}: success_rate={pattern.success_rate:.2f}")

    def get_pattern_statistics(self) -> Dict[str, Any]:
        """Get statistics about cached patterns"""
        if not self.pattern_cache:
            return {"total_patterns": 0, "patterns": []}

        pattern_stats = []
        for pattern in self.pattern_cache.values():
            pattern_stats.append({
                "pattern_id": pattern.pattern_id,
                "description": pattern.description,
                "success_count": pattern.success_count,
                "failure_count": pattern.failure_count,
                "success_rate": pattern.success_rate,
                "confidence_score": pattern.confidence_score
            })

        return {
            "total_patterns": len(self.pattern_cache),
            "patterns": sorted(pattern_stats, key=lambda x: x["success_rate"], reverse=True)
        }

    def clear_pattern_cache(self) -> int:
        """Clear the pattern cache and return number of patterns removed"""
        count = len(self.pattern_cache)
        self.pattern_cache.clear()
        logger.info(f"Cleared {count} patterns from cache")
        return count

    async def close(self) -> None:
        """Clean up Stagehand resources"""
        try:
            if self.current_page:
                # In real implementation, close the page
                self.current_page = None

            if self.stagehand_instance:
                # In real implementation, close the Stagehand instance
                self.stagehand_instance = None

            logger.info("Stagehand resources cleaned up")

        except Exception as e:
            logger.warning(f"Error cleaning up Stagehand resources: {e}")


# Global Stagehand generator instance
stagehand_generator = StagehandCodeGenerator()