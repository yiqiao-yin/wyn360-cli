"""
Vision Decision Engine for autonomous browser automation.

This module uses Anthropic Claude Vision (via pydantic-ai) to analyze screenshots
and make intelligent navigation decisions.
"""

import logging
from typing import Dict, Any, List, Optional
from pydantic_ai import Agent
from pydantic_ai.messages import BinaryContent

logger = logging.getLogger(__name__)


class VisionDecisionError(Exception):
    """Base exception for VisionDecisionEngine errors."""
    pass


class VisionDecisionEngine:
    """
    Uses Anthropic Claude Vision (via pydantic-ai) to analyze screenshots.

    Responsible for:
    - Vision analysis of browser screenshots
    - Decision making (what action to take next)
    - Action planning (structured output for BrowserController)
    - Context management (task goal, action history, page state)
    - Confidence scoring
    - Fallback strategies for low-confidence scenarios
    """

    def __init__(self, agent: Agent):
        """
        Initialize with WYN360Agent (pydantic-ai).

        Args:
            agent: pydantic-ai Agent instance (must support vision)
        """
        self.agent = agent

    async def analyze_and_decide(
        self,
        screenshot: bytes,
        goal: str,
        history: List[Dict[str, Any]],
        page_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze screenshot and decide next action.

        Args:
            screenshot: Screenshot as bytes (PNG format)
            goal: Task goal/description
            history: List of previous actions taken
            page_state: Current page state (URL, title, etc.)

        Returns:
            Decision dictionary:
            {
                'status': 'continue' | 'complete' | 'stuck',
                'action': {...},  # Next action to execute
                'reasoning': str,  # Claude's reasoning
                'confidence': float,  # 0-100
                'extracted_data': {...},  # If status='complete'
            }

        Raises:
            VisionDecisionError: If decision making fails
        """
        try:
            logger.info(f"Analyzing screenshot for goal: {goal}")

            # Build comprehensive analysis prompt
            prompt = self._build_analysis_prompt(goal, history, page_state)

            # Call agent with vision (all through pydantic-ai!)
            logger.debug("Calling agent with vision analysis")

            # For now, we'll use a simple text-based decision
            # The full vision integration will be added when we connect to the agent
            result = await self._analyze_with_vision(screenshot, prompt)

            # Parse decision
            decision = self._parse_decision(result, goal, page_state)

            logger.info(f"Decision: {decision['status']} - {decision.get('reasoning', 'N/A')[:100]}")

            return decision

        except Exception as e:
            logger.error(f"Vision analysis failed: {e}")
            raise VisionDecisionError(f"Failed to analyze screenshot: {e}")

    def _build_analysis_prompt(
        self,
        goal: str,
        history: List[Dict[str, Any]],
        page_state: Dict[str, Any]
    ) -> str:
        """
        Build comprehensive vision analysis prompt.

        Includes:
        - Task goal
        - Current page state
        - Action history (what we've tried)
        - Available actions
        - Success criteria
        - Instructions for structured output
        """
        # Build history summary
        history_summary = ""
        if history:
            history_summary = "\n\n**Actions taken so far:**\n"
            for i, action in enumerate(history[-5:], 1):  # Last 5 actions
                history_summary += f"{i}. {action['action']['type']}"
                if 'selector' in action['action']:
                    history_summary += f" on {action['action']['selector']}"
                if 'text' in action['action']:
                    history_summary += f" with text '{action['action']['text']}'"
                history_summary += f"\n   Result: {action.get('result', {}).get('success', 'unknown')}\n"

        prompt = f"""You are an autonomous web browser agent analyzing a screenshot to accomplish a task.

**Goal:** {goal}

**Current Page:**
- URL: {page_state.get('url', 'unknown')}
- Title: {page_state.get('title', 'unknown')}
- Loaded: {page_state.get('loaded', False)}
{history_summary}

**Your task:**
1. Analyze the screenshot carefully
2. Determine the next action to accomplish the goal
3. If the goal is complete, extract the requested information
4. If you're stuck or can't proceed, indicate that

**Available actions:**
- **click**: Click an element (button, link, checkbox, etc.)
  {{type: 'click', selector: '#element-id', text: 'Button Text'}}
  {{type: 'click', selector: 'button.submit'}}

- **type**: Type text into an input field
  {{type: 'type', selector: '#input-id', text: 'text to type'}}

- **scroll**: Scroll the page to reveal more content
  {{type: 'scroll', direction: 'down'|'up'|'top'|'bottom', amount: 500}}

- **navigate**: Navigate to a different URL
  {{type: 'navigate', url: 'https://...'}}

- **extract**: Extract text/data from elements (for final result)
  {{type: 'extract', selector: '.product-price'}}

- **wait**: Wait for page to load/update
  {{type: 'wait', seconds: 2}}

**Common scenarios to handle:**

1. **Popups/Modals/Cookie Banners:**
   - If you see a cookie consent banner, privacy notice, or modal blocking content
   - Click "Accept", "Agree", "Close", or "X" button to dismiss it
   - Common selectors: button[aria-label="Close"], .cookie-accept, #accept-cookies
   - High priority: clear these before proceeding with main task

2. **Missing elements:**
   - If you can't find the expected element, try scrolling down
   - The element might be below the fold
   - If still not found after scrolling, report stuck

3. **Loading states:**
   - If page shows loading spinner or "Loading..." text
   - Use wait action (2-3 seconds) to let content load
   - Don't proceed until content is visible

4. **Forms and filters:**
   - Fill search boxes before clicking search buttons
   - Select filters/dropdowns before viewing results
   - Type first, then click submit/search

5. **Captchas/Authentication:**
   - If you see CAPTCHA or login required
   - Report stuck immediately (cannot automate these)

**Response format:**
Provide your decision as a JSON object with:
{{
    "status": "continue" | "complete" | "stuck",
    "action": {{...action object...}},
    "reasoning": "explanation of why this action",
    "confidence": 0-100,
    "extracted_data": {{...data if complete...}}
}}

**Important guidelines:**
- Use CSS selectors when possible (#id, .class, tag[attribute])
- Prefer specific selectors over generic ones (e.g., #search-btn vs button)
- If task is complete, set status='complete' and include extracted_data
- If you can't find elements or encounter CAPTCHA, set status='stuck'
- Be specific about what you see and why you're taking the action
- For extraction, use descriptive keys (e.g., {{"price": "$99", "title": "Product"}} not {{"value": "$99"}})
- High confidence (80-100): Element clearly visible, action is obvious
- Medium confidence (50-79): Element found but action might need adjustment
- Low confidence (0-49): Uncertain, might be stuck soon
"""

        return prompt

    async def _analyze_with_vision(
        self,
        screenshot: bytes,
        prompt: str
    ) -> str:
        """
        Call agent with vision to analyze screenshot.

        Uses pydantic-ai's BinaryContent to send screenshot to Claude Vision API.

        Args:
            screenshot: Screenshot bytes (PNG format)
            prompt: Analysis prompt

        Returns:
            Agent's response text (JSON formatted)

        Raises:
            VisionDecisionError: If vision API call fails
        """
        try:
            # Import BinaryContent for vision
            from pydantic_ai import BinaryContent

            logger.debug(f"Calling Claude Vision API with {len(screenshot)} byte screenshot")

            # Call agent with vision (screenshot + text prompt)
            result = await self.agent.run(
                user_prompt=[
                    prompt,
                    BinaryContent(data=screenshot, media_type='image/png'),
                ]
            )

            logger.debug(f"Vision API returned: {str(result.data)[:200]}...")

            return result.data

        except Exception as e:
            logger.error(f"Vision API call failed: {e}")
            raise VisionDecisionError(f"Vision analysis failed: {e}")

    def _parse_decision(
        self,
        response: str,
        goal: str,
        page_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Parse Claude's response into structured action.

        Args:
            response: Claude's text response
            goal: Original goal
            page_state: Current page state

        Returns:
            Parsed decision dictionary
        """
        import json

        try:
            # Try to parse as JSON
            decision = json.loads(response.strip())

            # Validate required fields
            if 'status' not in decision:
                decision['status'] = 'continue'

            if 'action' not in decision:
                decision['action'] = {'type': 'wait', 'seconds': 1}

            if 'reasoning' not in decision:
                decision['reasoning'] = "No reasoning provided"

            if 'confidence' not in decision:
                decision['confidence'] = 50  # Default to medium confidence

            # Ensure confidence is in range 0-100
            decision['confidence'] = max(0, min(100, float(decision['confidence'])))

            return decision

        except json.JSONDecodeError:
            logger.warning("Failed to parse decision as JSON, using fallback")

            # Fallback: try to extract action from text
            return {
                'status': 'continue',
                'action': {'type': 'wait', 'seconds': 1},
                'reasoning': f"Could not parse structured decision. Response: {response[:200]}",
                'confidence': 0,
                'extracted_data': None
            }

    def _validate_action(self, action: Dict[str, Any]) -> bool:
        """
        Validate that action has required fields.

        Args:
            action: Action dictionary

        Returns:
            True if valid, False otherwise
        """
        if not isinstance(action, dict):
            return False

        action_type = action.get('type')

        # Valid action types
        valid_types = ['click', 'type', 'scroll', 'navigate', 'extract', 'wait']

        if action_type not in valid_types:
            return False

        # Type-specific validation
        if action_type == 'click':
            return 'selector' in action or 'text' in action

        elif action_type == 'type':
            return 'selector' in action and 'text' in action

        elif action_type == 'scroll':
            return 'direction' in action

        elif action_type == 'navigate':
            return 'url' in action

        elif action_type == 'extract':
            return 'selector' in action

        elif action_type == 'wait':
            return 'seconds' in action

        return False

    def estimate_cost(self, screenshot_bytes: int, history_length: int) -> float:
        """
        Estimate API cost for vision analysis.

        Args:
            screenshot_bytes: Size of screenshot in bytes
            history_length: Number of previous actions

        Returns:
            Estimated cost in USD

        Note:
            This is a rough estimate based on Claude Vision API pricing.
            Actual costs may vary.
        """
        # Rough estimates (update based on actual pricing):
        # - Vision API: ~$0.01 per image
        # - Text tokens: ~$0.000003 per token
        # - Typical prompt: ~500-1000 tokens

        base_vision_cost = 0.01  # Per screenshot
        text_tokens = 500 + (history_length * 50)  # Base + history
        text_cost = text_tokens * 0.000003

        total_cost = base_vision_cost + text_cost

        return total_cost
