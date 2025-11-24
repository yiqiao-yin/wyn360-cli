"""
Browser automation tools for WYN360 CLI using DOM-first approach

These tools integrate with the pydantic-ai agent system to provide
intelligent browser automation capabilities with fallback strategies.
"""

import json
import logging
from typing import Optional, Dict, List, Any, Union
from dataclasses import asdict
from playwright.async_api import Browser, Page, async_playwright
from pydantic_ai import RunContext

from .dom_analyzer import DOMExtractor, DOMAnalysis, format_dom_for_llm
from .browser_manager import browser_manager

logger = logging.getLogger(__name__)


class BrowserAutomationTools:
    """Browser automation tools with DOM-first approach"""

    def __init__(self):
        self.dom_extractor = DOMExtractor()
        self.page: Optional[Page] = None

    async def analyze_page_dom(
        self,
        ctx: RunContext[None],
        url: str,
        task_description: Optional[str] = None,
        confidence_threshold: float = 0.7,
        show_browser: bool = False
    ) -> Dict[str, Any]:
        """
        Analyze webpage DOM structure for intelligent automation

        Args:
            ctx: Pydantic AI run context
            url: URL to analyze
            task_description: Optional description of what user wants to do
            confidence_threshold: Minimum confidence for DOM analysis
            show_browser: Whether to show browser window for debugging

        Returns:
            Dict containing DOM analysis and recommendation
        """
        try:
            logger.info(f"Analyzing DOM for: {url}")

            # Initialize unified browser if needed
            await browser_manager.initialize(headless=not show_browser)

            # Get or create page
            self.page = await browser_manager.get_page("dom_analysis")

            # Navigate to page
            await self.page.goto(url)
            await self.page.wait_for_load_state('networkidle')

            # Extract DOM
            dom_analysis = await self.dom_extractor.extract_dom(self.page)

            # Format for LLM analysis
            llm_input = format_dom_for_llm(dom_analysis, max_elements=15, include_content=True)

            # Add task context if provided
            if task_description:
                llm_input = f"User Task: {task_description}\n\n{llm_input}"

            # Generate result
            result = {
                'success': True,
                'url': url,
                'title': dom_analysis.title,
                'confidence': dom_analysis.analysis_confidence,
                'dom_analysis_text': llm_input,
                'interactive_elements_count': len(dom_analysis.interactive_elements),
                'forms_count': len(dom_analysis.forms),
                'recommended_approach': self._determine_automation_approach(
                    dom_analysis, confidence_threshold
                ),
                'raw_analysis': {
                    'interactive_elements': [asdict(elem) for elem in dom_analysis.interactive_elements[:10]],
                    'forms': dom_analysis.forms,
                    'total_elements': dom_analysis.total_elements
                }
            }

            logger.info(f"DOM analysis complete: {result['confidence']:.2f} confidence, "
                       f"{result['interactive_elements_count']} interactive elements")

            return result

        except Exception as e:
            logger.error(f"Error analyzing DOM: {e}")
            return {
                'success': False,
                'error': str(e),
                'url': url,
                'confidence': 0.0,
                'recommended_approach': 'vision_fallback'
            }

    async def execute_dom_action(
        self,
        ctx: RunContext[None],
        url: str,
        action: str,
        target_description: str,
        action_data: Optional[Dict[str, Any]] = None,
        confidence_threshold: float = 0.7,
        show_browser: bool = False
    ) -> Dict[str, Any]:
        """
        Execute an action on a webpage using DOM analysis

        Args:
            ctx: Pydantic AI run context
            url: URL to perform action on
            action: Type of action (click, type, select, submit, etc.)
            target_description: Description of element to interact with
            action_data: Additional data for the action (text to type, option to select, etc.)
            confidence_threshold: Minimum confidence to proceed with DOM approach
            show_browser: Whether to show browser window

        Returns:
            Dict containing execution result
        """
        try:
            logger.info(f"Executing DOM action: {action} on {target_description} at {url}")

            # First analyze the DOM
            analysis_result = await self.analyze_page_dom(
                ctx, url, f"{action} on {target_description}", confidence_threshold, show_browser
            )

            if not analysis_result['success']:
                return {
                    'success': False,
                    'error': 'DOM analysis failed',
                    'recommendation': 'Use stagehand or vision fallback'
                }

            # Check if DOM confidence is sufficient
            if analysis_result['confidence'] < confidence_threshold:
                return {
                    'success': False,
                    'confidence': analysis_result['confidence'],
                    'error': f'DOM confidence ({analysis_result["confidence"]:.2f}) below threshold ({confidence_threshold})',
                    'recommendation': 'Use stagehand fallback',
                    'dom_analysis': analysis_result['dom_analysis_text']
                }

            # Try to find and interact with the target element
            element_found = await self._find_element_by_description(target_description)

            if not element_found:
                return {
                    'success': False,
                    'error': f'Could not find element: {target_description}',
                    'recommendation': 'Use stagehand fallback with this DOM context',
                    'dom_analysis': analysis_result['dom_analysis_text']
                }

            # Execute the action
            action_result = await self._execute_action_on_element(
                element_found, action, action_data
            )

            if action_result['success']:
                # Wait for any navigation or page updates
                try:
                    await self.page.wait_for_load_state('networkidle', timeout=5000)
                except:
                    pass  # Timeout is okay

                return {
                    'success': True,
                    'action': action,
                    'target': target_description,
                    'confidence': analysis_result['confidence'],
                    'result': action_result['result'],
                    'approach_used': 'dom_analysis'
                }
            else:
                return {
                    'success': False,
                    'error': action_result['error'],
                    'recommendation': 'Retry with stagehand or vision fallback',
                    'dom_analysis': analysis_result['dom_analysis_text']
                }

        except Exception as e:
            logger.error(f"Error executing DOM action: {e}")
            return {
                'success': False,
                'error': str(e),
                'recommendation': 'Use stagehand or vision fallback'
            }

    async def close_browser(self):
        """Clean up browser resources"""
        try:
            # Close our specific page
            if self.page:
                await browser_manager.close_page("dom_analysis")
                self.page = None
            logger.info("DOM analysis browser resources cleaned up")
        except Exception as e:
            logger.warning(f"Error closing browser: {e}")

    # Browser initialization is now handled by the unified browser manager

    def _determine_automation_approach(
        self,
        dom_analysis: DOMAnalysis,
        confidence_threshold: float
    ) -> str:
        """Determine the best automation approach based on DOM analysis"""

        if dom_analysis.analysis_confidence >= confidence_threshold:
            if len(dom_analysis.interactive_elements) >= 3:
                return 'dom_analysis'
            elif len(dom_analysis.forms) > 0:
                return 'dom_analysis'
            else:
                return 'stagehand_recommended'
        elif dom_analysis.analysis_confidence >= (confidence_threshold * 0.7):
            return 'stagehand_recommended'
        else:
            return 'vision_fallback'

    async def _find_element_by_description(self, description: str) -> Optional[Any]:
        """
        Find element by description using simple text matching
        This is a basic implementation - in a full system this would be more sophisticated
        """
        try:
            # Simple approach: try to find by text content, then by common attributes
            description_lower = description.lower()

            # Try finding by exact text match first
            elements = await self.page.query_selector_all('*')

            for element in elements:
                try:
                    text_content = await element.text_content()
                    if text_content and description_lower in text_content.lower():
                        return element

                    # Check common attributes
                    for attr in ['aria-label', 'title', 'placeholder', 'alt']:
                        attr_value = await element.get_attribute(attr)
                        if attr_value and description_lower in attr_value.lower():
                            return element

                except:
                    continue

            return None

        except Exception as e:
            logger.warning(f"Error finding element by description: {e}")
            return None

    async def _execute_action_on_element(
        self,
        element: Any,
        action: str,
        action_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute action on the found element"""
        try:
            action_lower = action.lower()

            if action_lower == 'click':
                await element.click()
                return {'success': True, 'result': 'Element clicked successfully'}

            elif action_lower == 'type':
                if action_data and 'text' in action_data:
                    await element.fill(action_data['text'])
                    return {'success': True, 'result': f'Typed: {action_data["text"]}'}
                else:
                    return {'success': False, 'error': 'No text provided for typing'}

            elif action_lower == 'clear':
                await element.fill('')
                return {'success': True, 'result': 'Element cleared'}

            elif action_lower == 'select':
                if action_data and 'option' in action_data:
                    await element.select_option(label=action_data['option'])
                    return {'success': True, 'result': f'Selected: {action_data["option"]}'}
                else:
                    return {'success': False, 'error': 'No option provided for selection'}

            else:
                return {'success': False, 'error': f'Unknown action: {action}'}

        except Exception as e:
            return {'success': False, 'error': f'Action execution failed: {e}'}


# Global instance for the agent
browser_tools = BrowserAutomationTools()