"""
Browser Task Executor for autonomous browser automation.

This module orchestrates autonomous browser tasks using vision-based decision making.
Coordinates BrowserController (automation) + VisionDecisionEngine (AI).
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from pydantic_ai import Agent

from .browser_controller import BrowserController, BrowserControllerError
from .vision_engine import VisionDecisionEngine, VisionDecisionError

logger = logging.getLogger(__name__)


class BrowserTaskExecutorError(Exception):
    """Base exception for BrowserTaskExecutor errors."""
    pass


class BrowserTaskExecutor:
    """
    Orchestrates autonomous browser tasks using vision-based decision making.

    Coordinates:
    - BrowserController: Pure browser automation (Playwright)
    - VisionDecisionEngine: AI-powered decision making (Claude Vision)

    Responsible for:
    - Main execution loop (screenshot → analyze → decide → act → repeat)
    - Task state management (goal, progress, history)
    - Step limiting (prevent infinite loops)
    - Success detection (task completion criteria)
    - Stuck detection (repeated failed actions)
    - Progress reporting to user
    - Execution metrics tracking
    """

    def __init__(self, agent: Agent):
        """
        Initialize with WYN360Agent (pydantic-ai).

        Args:
            agent: pydantic-ai Agent instance (must support vision)
        """
        self.agent = agent
        self.controller = BrowserController()
        self.vision_engine = VisionDecisionEngine(agent)

    async def execute_task(
        self,
        task: str,
        url: str,
        max_steps: int = 20,
        headless: bool = False
    ) -> Dict[str, Any]:
        """
        Execute multi-step browser task autonomously.

        Args:
            task: Natural language task description
            url: Starting URL
            max_steps: Maximum browser actions (default: 20)
            headless: Run browser in headless mode (default: False for user visibility)

        Returns:
            Result dictionary:
            {
                'status': 'success' | 'partial' | 'failed',
                'result': {...},  # Extracted data
                'steps_taken': int,
                'history': [...],  # Action history
                'reasoning': str,  # Final summary
                'metrics': {...},  # Performance metrics
            }

        Raises:
            BrowserTaskExecutorError: If critical error occurs
        """
        logger.info(f"Starting task execution: {task}")
        logger.info(f"Starting URL: {url}")
        logger.info(f"Max steps: {max_steps}, Headless: {headless}")

        # Initialize metrics
        metrics = {
            'start_time': asyncio.get_event_loop().time(),
            'screenshots_taken': 0,
            'actions_executed': 0,
            'vision_api_calls': 0,
            'errors_encountered': 0
        }

        # Initialize state
        history = []
        stuck_count = 0
        last_action = None

        try:
            # Initialize browser
            logger.info("Initializing browser...")
            await self.controller.initialize(headless=headless)

            # Navigate to starting URL
            logger.info(f"Navigating to {url}...")
            await self.controller.navigate(url)

            # Main execution loop
            for step in range(max_steps):
                logger.info(f"=== Step {step + 1}/{max_steps} ===")

                try:
                    # 1. Capture current state
                    logger.debug("Taking screenshot...")
                    screenshot = await self.controller.take_screenshot()
                    metrics['screenshots_taken'] += 1

                    page_state = await self.controller.get_page_state()
                    logger.info(f"Current page: {page_state.get('url', 'unknown')}")

                    # 2. Analyze and decide (ALL AI via pydantic-ai + Anthropic Vision)
                    logger.debug("Analyzing screenshot with vision engine...")
                    decision = await self.vision_engine.analyze_and_decide(
                        screenshot=screenshot,
                        goal=task,
                        history=history,
                        page_state=page_state
                    )
                    metrics['vision_api_calls'] += 1

                    logger.info(f"Decision: {decision['status']}")
                    logger.info(f"Action: {decision['action'].get('type', 'none')}")
                    logger.info(f"Confidence: {decision.get('confidence', 0)}%")
                    logger.debug(f"Reasoning: {decision.get('reasoning', 'N/A')[:100]}...")

                    # 3. Check if task complete
                    if decision['status'] == 'complete':
                        logger.info("✅ Task completed successfully!")

                        metrics['end_time'] = asyncio.get_event_loop().time()
                        metrics['total_duration'] = metrics['end_time'] - metrics['start_time']

                        return {
                            'status': 'success',
                            'result': decision.get('extracted_data', {}),
                            'steps_taken': step + 1,
                            'history': history,
                            'reasoning': decision.get('reasoning', 'Task completed'),
                            'metrics': metrics
                        }

                    # 4. Check if stuck (repeated failures or same action)
                    if decision['status'] == 'stuck':
                        stuck_count += 1
                        logger.warning(f"Agent reported stuck (count: {stuck_count})")
                    elif decision['action'] == last_action:
                        stuck_count += 1
                        logger.warning(f"Repeating same action (count: {stuck_count})")
                    else:
                        stuck_count = 0  # Reset on different action

                    if stuck_count >= 3:
                        logger.error("❌ Agent stuck after 3 attempts")
                        return self._handle_stuck_state(task, history, step + 1, metrics)

                    # 5. Execute action
                    logger.info(f"Executing action: {decision['action']}")
                    action_result = await self.controller.execute_action(decision['action'])
                    metrics['actions_executed'] += 1

                    if not action_result.get('success', False):
                        logger.warning(f"Action failed: {action_result.get('error', 'unknown')}")
                        metrics['errors_encountered'] += 1

                    # 6. Record history
                    history.append({
                        'step': step + 1,
                        'action': decision['action'],
                        'reasoning': decision.get('reasoning', ''),
                        'confidence': decision.get('confidence', 0),
                        'result': action_result,
                        'page_url': page_state.get('url', '')
                    })

                    last_action = decision['action']

                    # 7. Small delay for page updates
                    logger.debug("Waiting for page to update...")
                    await asyncio.sleep(1)

                except VisionDecisionError as e:
                    logger.error(f"Vision decision error: {e}")
                    metrics['errors_encountered'] += 1

                    # Continue with fallback action (wait)
                    history.append({
                        'step': step + 1,
                        'action': {'type': 'wait', 'seconds': 2},
                        'reasoning': f'Vision error: {str(e)}',
                        'confidence': 0,
                        'result': {'success': False, 'error': str(e)},
                        'page_url': page_state.get('url', '') if 'page_state' in locals() else ''
                    })

                except BrowserControllerError as e:
                    logger.error(f"Browser controller error: {e}")
                    metrics['errors_encountered'] += 1

                    history.append({
                        'step': step + 1,
                        'action': {'type': 'error'},
                        'reasoning': f'Browser error: {str(e)}',
                        'confidence': 0,
                        'result': {'success': False, 'error': str(e)},
                        'page_url': ''
                    })

                except Exception as e:
                    logger.error(f"Unexpected error in step {step + 1}: {e}")
                    metrics['errors_encountered'] += 1

                    # Try to continue
                    continue

        finally:
            # Always cleanup browser
            logger.info("Cleaning up browser...")
            await self.controller.cleanup()

        # Max steps reached
        logger.warning(f"⚠️ Reached maximum steps ({max_steps}) without completion")

        metrics['end_time'] = asyncio.get_event_loop().time()
        metrics['total_duration'] = metrics['end_time'] - metrics['start_time']

        return {
            'status': 'partial',
            'result': None,
            'steps_taken': max_steps,
            'history': history,
            'reasoning': f"Reached maximum steps ({max_steps}) without completion",
            'metrics': metrics
        }

    def _handle_stuck_state(
        self,
        task: str,
        history: List[Dict],
        steps_taken: int,
        metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle case where agent is stuck/repeating actions.

        Args:
            task: Original task
            history: Action history
            steps_taken: Number of steps taken
            metrics: Execution metrics

        Returns:
            Failed result dictionary
        """
        logger.error("Handling stuck state...")

        # Analyze why stuck (last few actions)
        recent_actions = history[-3:] if len(history) >= 3 else history
        action_types = [a['action'].get('type', 'unknown') for a in recent_actions]

        metrics['end_time'] = asyncio.get_event_loop().time()
        metrics['total_duration'] = metrics['end_time'] - metrics['start_time']

        return {
            'status': 'failed',
            'result': None,
            'steps_taken': steps_taken,
            'history': history,
            'reasoning': (
                f"Agent appears stuck. "
                f"Last 3 actions: {', '.join(action_types)}. "
                f"Unable to make progress toward goal: {task}"
            ),
            'metrics': metrics
        }

    def get_summary(self, result: Dict[str, Any]) -> str:
        """
        Generate human-readable summary of execution.

        Args:
            result: Execution result dictionary

        Returns:
            Formatted summary string
        """
        status_emoji = {
            'success': '✅',
            'partial': '⚠️',
            'failed': '❌'
        }

        emoji = status_emoji.get(result['status'], '❓')

        summary = f"{emoji} **Task {result['status'].upper()}**\n\n"
        summary += f"**Steps Taken:** {result['steps_taken']}\n"

        if result.get('metrics'):
            metrics = result['metrics']
            summary += f"**Duration:** {metrics.get('total_duration', 0):.1f}s\n"
            summary += f"**Screenshots:** {metrics.get('screenshots_taken', 0)}\n"
            summary += f"**Actions:** {metrics.get('actions_executed', 0)}\n"
            summary += f"**Errors:** {metrics.get('errors_encountered', 0)}\n"

        summary += f"\n**Reasoning:**\n{result.get('reasoning', 'N/A')}\n"

        if result['status'] == 'success' and result.get('result'):
            summary += f"\n**Extracted Data:**\n{self._format_data(result['result'])}\n"

        return summary

    def _format_data(self, data: Any, indent: int = 0) -> str:
        """Format extracted data for display."""
        if isinstance(data, dict):
            lines = []
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    lines.append(f"{'  ' * indent}- {key}:")
                    lines.append(self._format_data(value, indent + 1))
                else:
                    lines.append(f"{'  ' * indent}- {key}: {value}")
            return '\n'.join(lines)
        elif isinstance(data, list):
            lines = []
            for item in data:
                if isinstance(item, (dict, list)):
                    lines.append(self._format_data(item, indent))
                else:
                    lines.append(f"{'  ' * indent}- {item}")
            return '\n'.join(lines)
        else:
            return f"{'  ' * indent}{data}"

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        # Ensure browser is cleaned up
        if self.controller:
            await self.controller.cleanup()
