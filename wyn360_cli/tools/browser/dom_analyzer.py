"""
DOM Analysis Module for WYN360 CLI Browser Automation

This module provides DOM extraction and analysis capabilities for intelligent
browser automation without relying on expensive vision API calls.

Key Features:
- Extract interactive elements from web pages
- Structure DOM data for LLM analysis
- Confidence scoring for action decisions
- Element attribute preservation for better context
"""

from typing import Dict, List, Optional, Any, Union
import json
import re
from dataclasses import dataclass
from playwright.async_api import Page, ElementHandle
import logging

logger = logging.getLogger(__name__)


@dataclass
class DOMElement:
    """Represents a single DOM element with its properties"""
    tag: str
    text: str
    attributes: Dict[str, str]
    xpath: str
    selector: str
    is_interactive: bool
    element_type: str  # button, input, link, form, etc.
    confidence: float  # How confident we are this element can be interacted with


@dataclass
class DOMAnalysis:
    """Complete DOM analysis result"""
    url: str
    title: str
    interactive_elements: List[DOMElement]
    forms: List[Dict[str, Any]]
    navigation_elements: List[DOMElement]
    content_elements: List[DOMElement]
    total_elements: int
    analysis_confidence: float


class DOMExtractor:
    """Extract and analyze DOM structure from web pages"""

    def __init__(self):
        self.interactive_selectors = [
            'button', 'input', 'select', 'textarea', 'a[href]',
            '[onclick]', '[role="button"]', '[role="link"]',
            '[tabindex]', 'form', 'label'
        ]

        self.navigation_selectors = [
            'nav', '[role="navigation"]', '.nav', '.navbar',
            '.menu', '.breadcrumb', 'header', 'footer'
        ]

    async def extract_dom(self, page: Page) -> DOMAnalysis:
        """
        Extract comprehensive DOM analysis from a page

        Args:
            page: Playwright page instance

        Returns:
            DOMAnalysis object with structured DOM data
        """
        try:
            logger.info(f"Extracting DOM from page: {page.url}")

            # Get page metadata
            title = await page.title()
            url = page.url

            # Extract different types of elements
            interactive_elements = await self._extract_interactive_elements(page)
            forms = await self._extract_forms(page)
            navigation_elements = await self._extract_navigation_elements(page)
            content_elements = await self._extract_content_elements(page)

            # Calculate overall analysis confidence
            total_elements = len(interactive_elements) + len(navigation_elements) + len(content_elements)
            analysis_confidence = self._calculate_analysis_confidence(
                interactive_elements, forms, navigation_elements
            )

            result = DOMAnalysis(
                url=url,
                title=title,
                interactive_elements=interactive_elements,
                forms=forms,
                navigation_elements=navigation_elements,
                content_elements=content_elements,
                total_elements=total_elements,
                analysis_confidence=analysis_confidence
            )

            logger.info(f"DOM extraction complete: {total_elements} elements, confidence: {analysis_confidence:.2f}")
            return result

        except Exception as e:
            logger.error(f"Error extracting DOM: {e}")
            raise

    async def _extract_interactive_elements(self, page: Page) -> List[DOMElement]:
        """Extract all interactive elements from the page"""
        elements = []

        for selector in self.interactive_selectors:
            try:
                element_handles = await page.query_selector_all(selector)

                for handle in element_handles:
                    dom_element = await self._create_dom_element(handle, page)
                    if dom_element:
                        dom_element.is_interactive = True
                        dom_element.element_type = self._determine_element_type(dom_element)
                        dom_element.confidence = self._calculate_element_confidence(dom_element)
                        elements.append(dom_element)

            except Exception as e:
                logger.warning(f"Error processing selector '{selector}': {e}")
                continue

        # Remove duplicates based on xpath
        unique_elements = {}
        for element in elements:
            if element.xpath not in unique_elements:
                unique_elements[element.xpath] = element
            else:
                # Keep the element with higher confidence
                if element.confidence > unique_elements[element.xpath].confidence:
                    unique_elements[element.xpath] = element

        return list(unique_elements.values())

    async def _extract_forms(self, page: Page) -> List[Dict[str, Any]]:
        """Extract form information with their fields"""
        forms = []

        try:
            form_handles = await page.query_selector_all('form')

            for i, form_handle in enumerate(form_handles):
                form_info = {
                    'index': i,
                    'action': await form_handle.get_attribute('action') or '',
                    'method': await form_handle.get_attribute('method') or 'get',
                    'fields': []
                }

                # Extract form fields
                field_selectors = ['input', 'select', 'textarea', 'button[type="submit"]']
                for selector in field_selectors:
                    fields = await form_handle.query_selector_all(selector)

                    for field in fields:
                        field_info = {
                            'tag': await field.get_attribute('tagName') or '',
                            'type': await field.get_attribute('type') or '',
                            'name': await field.get_attribute('name') or '',
                            'id': await field.get_attribute('id') or '',
                            'placeholder': await field.get_attribute('placeholder') or '',
                            'required': await field.get_attribute('required') is not None,
                            'label': await self._get_field_label(field, page)
                        }
                        form_info['fields'].append(field_info)

                forms.append(form_info)

        except Exception as e:
            logger.warning(f"Error extracting forms: {e}")

        return forms

    async def _extract_navigation_elements(self, page: Page) -> List[DOMElement]:
        """Extract navigation-related elements"""
        elements = []

        for selector in self.navigation_selectors:
            try:
                element_handles = await page.query_selector_all(selector)

                for handle in element_handles:
                    dom_element = await self._create_dom_element(handle, page)
                    if dom_element:
                        dom_element.is_interactive = False
                        dom_element.element_type = 'navigation'
                        dom_element.confidence = 0.8  # Navigation elements are usually reliable
                        elements.append(dom_element)

            except Exception as e:
                logger.warning(f"Error processing navigation selector '{selector}': {e}")
                continue

        return elements

    async def _extract_content_elements(self, page: Page) -> List[DOMElement]:
        """Extract main content elements"""
        elements = []
        content_selectors = ['main', 'article', '.content', '.main-content', 'section']

        for selector in content_selectors:
            try:
                element_handles = await page.query_selector_all(selector)

                for handle in element_handles:
                    dom_element = await self._create_dom_element(handle, page)
                    if dom_element and len(dom_element.text.strip()) > 50:  # Only meaningful content
                        dom_element.is_interactive = False
                        dom_element.element_type = 'content'
                        dom_element.confidence = 0.7
                        elements.append(dom_element)

            except Exception as e:
                logger.warning(f"Error processing content selector '{selector}': {e}")
                continue

        return elements

    async def _create_dom_element(self, handle: ElementHandle, page: Page) -> Optional[DOMElement]:
        """Create a DOMElement from an ElementHandle"""
        try:
            # Get element properties
            tag = await handle.get_attribute('tagName') or ''
            tag = tag.lower()

            # Get text content (truncate if too long)
            text = await handle.text_content() or ''
            text = text.strip()[:200]  # Limit text length

            # Get all attributes
            attributes = {}
            for attr in ['id', 'class', 'name', 'type', 'role', 'aria-label', 'title', 'href', 'value']:
                value = await handle.get_attribute(attr)
                if value:
                    attributes[attr] = value

            # Get selector paths
            xpath = await self._get_xpath(handle, page)
            selector = await self._get_css_selector(handle, page)

            return DOMElement(
                tag=tag,
                text=text,
                attributes=attributes,
                xpath=xpath,
                selector=selector,
                is_interactive=False,  # Will be set by caller
                element_type='',       # Will be set by caller
                confidence=0.0         # Will be calculated by caller
            )

        except Exception as e:
            logger.warning(f"Error creating DOM element: {e}")
            return None

    async def _get_xpath(self, handle: ElementHandle, page: Page) -> str:
        """Generate XPath for an element"""
        try:
            xpath = await page.evaluate('''(element) => {
                function getPath(node) {
                    if (node.nodeType !== Node.ELEMENT_NODE) return '';
                    if (node === document.documentElement) return '/html';

                    let path = '';
                    let parent = node.parentNode;
                    if (!parent) return '';

                    let siblings = Array.from(parent.children);
                    let tag = node.tagName.toLowerCase();
                    let index = siblings.filter(s => s.tagName.toLowerCase() === tag).indexOf(node) + 1;

                    path = '/' + tag + (index > 1 ? '[' + index + ']' : '');
                    return getPath(parent) + path;
                }
                return getPath(element);
            }''', handle)
            return xpath or ''
        except:
            return ''

    async def _get_css_selector(self, handle: ElementHandle, page: Page) -> str:
        """Generate CSS selector for an element"""
        try:
            # Try to get a unique selector
            selector = await page.evaluate('''(element) => {
                function getSelector(node) {
                    if (node.id) return '#' + node.id;

                    let selector = node.tagName.toLowerCase();

                    if (node.className) {
                        selector += '.' + Array.from(node.classList).join('.');
                    }

                    // Add position if not unique
                    let parent = node.parentElement;
                    if (parent) {
                        let siblings = Array.from(parent.children).filter(s =>
                            s.tagName === node.tagName && s.className === node.className
                        );
                        if (siblings.length > 1) {
                            let index = siblings.indexOf(node);
                            selector += ':nth-of-type(' + (index + 1) + ')';
                        }
                    }

                    return selector;
                }
                return getSelector(element);
            }''', handle)
            return selector or ''
        except:
            return ''

    async def _get_field_label(self, field_handle: ElementHandle, page: Page) -> str:
        """Get the label text for a form field"""
        try:
            # Try to find associated label
            field_id = await field_handle.get_attribute('id')
            if field_id:
                label = await page.query_selector(f'label[for="{field_id}"]')
                if label:
                    label_text = await label.text_content()
                    if label_text:
                        return label_text.strip()

            # Try to find parent label
            parent_label = await page.evaluate('''(element) => {
                let current = element;
                while (current && current.tagName.toLowerCase() !== 'label') {
                    current = current.parentElement;
                }
                return current ? current.textContent.trim() : '';
            }''', field_handle)

            return parent_label or ''

        except:
            return ''

    def _determine_element_type(self, element: DOMElement) -> str:
        """Determine the type of an interactive element"""
        tag = element.tag.lower()
        element_type = element.attributes.get('type', '').lower()
        role = element.attributes.get('role', '').lower()

        if tag == 'button' or role == 'button' or element_type == 'button':
            return 'button'
        elif tag == 'input':
            if element_type in ['text', 'email', 'password', 'search']:
                return 'text_input'
            elif element_type in ['submit', 'button']:
                return 'submit_button'
            elif element_type in ['checkbox', 'radio']:
                return element_type
            else:
                return 'input'
        elif tag == 'select':
            return 'select'
        elif tag == 'textarea':
            return 'textarea'
        elif tag == 'a' and 'href' in element.attributes:
            return 'link'
        elif tag == 'form':
            return 'form'
        else:
            return 'interactive'

    def _calculate_element_confidence(self, element: DOMElement) -> float:
        """Calculate confidence score for an element's interactivity"""
        confidence = 0.5  # Base confidence

        # Increase confidence based on element properties
        if element.attributes.get('id'):
            confidence += 0.1
        if element.attributes.get('name'):
            confidence += 0.1
        if element.attributes.get('aria-label'):
            confidence += 0.15
        if element.text and len(element.text.strip()) > 0:
            confidence += 0.15
        if element.attributes.get('role'):
            confidence += 0.1

        # Element type specific adjustments
        if element.element_type in ['button', 'submit_button', 'link']:
            confidence += 0.2
        elif element.element_type in ['text_input', 'select', 'textarea']:
            confidence += 0.15

        # Reduce confidence for generic elements
        if not element.attributes.get('id') and not element.attributes.get('name'):
            if element.element_type == 'interactive':
                confidence -= 0.2

        return min(1.0, max(0.0, confidence))

    def _calculate_analysis_confidence(self,
                                     interactive_elements: List[DOMElement],
                                     forms: List[Dict[str, Any]],
                                     navigation_elements: List[DOMElement]) -> float:
        """Calculate overall confidence in the DOM analysis"""
        if not interactive_elements and not forms:
            return 0.1  # Very low confidence if no interactive elements

        # Base confidence from number of elements found
        base_confidence = min(0.8, len(interactive_elements) * 0.1)

        # Bonus for well-structured elements
        well_structured = sum(1 for elem in interactive_elements
                             if elem.confidence > 0.7)
        structure_bonus = min(0.2, well_structured * 0.05)

        # Bonus for forms (usually well-structured)
        form_bonus = min(0.1, len(forms) * 0.05)

        return min(1.0, base_confidence + structure_bonus + form_bonus)


def format_dom_for_llm(dom_analysis: DOMAnalysis,
                       max_elements: int = 20,
                       include_content: bool = False) -> str:
    """
    Format DOM analysis for LLM consumption

    Args:
        dom_analysis: DOMAnalysis object
        max_elements: Maximum number of elements to include
        include_content: Whether to include content elements

    Returns:
        Formatted string for LLM analysis
    """
    output = []

    # Page info
    output.append(f"Page: {dom_analysis.title}")
    output.append(f"URL: {dom_analysis.url}")
    output.append(f"Analysis Confidence: {dom_analysis.analysis_confidence:.2f}")
    output.append("")

    # Interactive elements
    if dom_analysis.interactive_elements:
        output.append("INTERACTIVE ELEMENTS:")
        sorted_elements = sorted(dom_analysis.interactive_elements,
                               key=lambda x: x.confidence, reverse=True)

        for i, element in enumerate(sorted_elements[:max_elements]):
            output.append(f"{i+1}. {element.element_type.upper()}: '{element.text[:50]}'")
            if element.attributes.get('id'):
                output.append(f"   ID: {element.attributes['id']}")
            if element.attributes.get('name'):
                output.append(f"   Name: {element.attributes['name']}")
            if element.attributes.get('aria-label'):
                output.append(f"   Label: {element.attributes['aria-label']}")
            output.append(f"   Confidence: {element.confidence:.2f}")
            output.append(f"   Selector: {element.selector}")
            output.append("")

    # Forms
    if dom_analysis.forms:
        output.append("FORMS:")
        for i, form in enumerate(dom_analysis.forms):
            output.append(f"{i+1}. Form (method: {form['method']}):")
            for field in form['fields'][:5]:  # Limit fields shown
                field_desc = f"   - {field['tag']}"
                if field['type']:
                    field_desc += f" (type: {field['type']})"
                if field['label']:
                    field_desc += f": {field['label']}"
                elif field['placeholder']:
                    field_desc += f": {field['placeholder']}"
                elif field['name']:
                    field_desc += f" (name: {field['name']})"
                output.append(field_desc)
            output.append("")

    # Content elements (optional)
    if include_content and dom_analysis.content_elements:
        output.append("MAIN CONTENT:")
        for i, element in enumerate(dom_analysis.content_elements[:3]):  # Limit content
            output.append(f"{i+1}. {element.text[:100]}...")
            output.append("")

    return "\n".join(output)