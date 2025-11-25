"""
Enhanced Code Generator for Browser Automation

This module implements smolagents-inspired code-first browser automation,
generating complete Python scripts instead of step-by-step tool calls.
"""

import re
import json
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from .code_templates import AutomationTemplates


class TaskComplexity(Enum):
    """Classification of automation task complexity"""
    SIMPLE = "simple"           # Single action (click, fill, navigate)
    MODERATE = "moderate"       # Multiple actions with basic logic
    COMPLEX = "complex"         # Loops, conditionals, data extraction


class CodeOptimizationLevel(Enum):
    """Level of code optimization to apply"""
    BASIC = "basic"             # Basic error handling and waits
    STANDARD = "standard"       # Enhanced selectors and retries
    ADVANCED = "advanced"       # Intelligent waits and fallbacks


@dataclass
class CodeGenerationContext:
    """Context for code generation"""
    task_description: str
    url: str
    expected_output_schema: Optional[Dict] = None
    complexity: TaskComplexity = TaskComplexity.MODERATE
    optimization_level: CodeOptimizationLevel = CodeOptimizationLevel.STANDARD
    include_error_handling: bool = True
    include_waits: bool = True
    max_retries: int = 3


class EnhancedCodeGenerator:
    """
    Generate optimized browser automation code using smolagents-inspired patterns
    """

    def __init__(self):
        self.templates = AutomationTemplates()
        self._code_patterns = self._initialize_patterns()
        self._optimization_rules = self._initialize_optimization_rules()

    def _initialize_patterns(self) -> Dict[str, str]:
        """Initialize reusable code patterns"""
        return {
            "navigation": """
# Navigate to page with error handling
try:
    await page.goto('{url}', wait_until='networkidle')
    await page.wait_for_load_state('domcontentloaded')
except Exception as e:
    print(f"Navigation error: {{e}}")
    await page.goto('{url}', wait_until='domcontentloaded')
""",
            "search_action": """
# Perform search with robust element detection
search_selectors = [
    'input[placeholder*="search"]',
    'input[name*="search"]',
    'input[type="search"]',
    '.search-input',
    '#search'
]

search_element = None
for selector in search_selectors:
    try:
        search_element = page.locator(selector)
        await search_element.wait_for(state='visible', timeout=5000)
        break
    except:
        continue

if search_element:
    await search_element.fill('{search_term}')
    await search_element.press('Enter')
    await page.wait_for_load_state('networkidle')
else:
    raise Exception("Could not find search element")
""",
            "data_extraction": """
# Extract data with error handling and validation
{extraction_code}

# Validate and format results
if isinstance(result, dict) and result:
    print("Extraction successful")
elif isinstance(result, list) and len(result) > 0:
    print(f"Extracted {{len(result)}} items")
else:
    print("Warning: No data extracted or invalid format")
""",
            "form_interaction": """
# Interact with form elements robustly
form_data = {form_data}

for field_name, field_value in form_data.items():
    field_selectors = [
        f'input[name="{{field_name}}"]',
        f'input[id="{{field_name}}"]',
        f'input[placeholder*="{{field_name}}"]',
        f'*[data-testid="{{field_name}}"]'
    ]

    field_element = None
    for selector in field_selectors:
        try:
            field_element = page.locator(selector)
            await field_element.wait_for(state='visible', timeout=3000)
            break
        except:
            continue

    if field_element:
        await field_element.fill(str(field_value))
    else:
        print(f"Warning: Could not find field {{field_name}}")
"""
        }

    def _initialize_optimization_rules(self) -> Dict[str, List[str]]:
        """Initialize code optimization rules"""
        return {
            "waits": [
                "Add explicit waits after navigation",
                "Wait for elements before interaction",
                "Use networkidle for dynamic content"
            ],
            "selectors": [
                "Use multiple selector strategies",
                "Prefer semantic selectors over brittle ones",
                "Include fallback selectors"
            ],
            "error_handling": [
                "Wrap critical operations in try-catch",
                "Provide meaningful error messages",
                "Implement graceful degradation"
            ],
            "performance": [
                "Batch similar operations",
                "Minimize page reloads",
                "Use efficient locator strategies"
            ]
        }

    async def generate_automation_code(self, context: CodeGenerationContext) -> str:
        """
        Generate complete automation code based on task context

        Args:
            context: Code generation context with task details

        Returns:
            Complete Python automation script
        """
        # Analyze task to determine structure
        task_analysis = await self._analyze_task(context)

        # Generate code components
        code_blocks = []

        # Header and imports
        code_blocks.append(self._generate_header())

        # Setup and initialization
        code_blocks.append(self._generate_setup(context))

        # Main automation logic
        main_logic = await self._generate_main_logic(context, task_analysis)
        code_blocks.append(main_logic)

        # Result processing and output
        code_blocks.append(self._generate_result_processing(context))

        # Combine all code blocks
        automation_body = "\n\n".join(code_blocks)

        # Wrap in async function structure
        if context.include_error_handling:
            complete_code = self._wrap_with_error_handling(automation_body)
        else:
            complete_code = self._wrap_in_async_function(automation_body)

        # Apply optimizations
        if context.optimization_level != CodeOptimizationLevel.BASIC:
            complete_code = await self._optimize_code(complete_code, context)

        return complete_code

    async def _analyze_task(self, context: CodeGenerationContext) -> Dict[str, Any]:
        """Analyze task to determine automation approach"""
        task = context.task_description.lower()

        analysis = {
            "involves_search": any(term in task for term in ["search", "find", "look for"]),
            "involves_navigation": any(term in task for term in ["browse", "go to", "navigate"]),
            "involves_forms": any(term in task for term in ["fill", "submit", "login", "register"]),
            "involves_extraction": any(term in task for term in ["extract", "get data", "collect", "scrape"]),
            "involves_interaction": any(term in task for term in ["click", "select", "choose"]),
            "involves_filtering": any(term in task for term in ["filter", "sort", "under", "over", "less than"]),
            "requires_loops": any(term in task for term in ["all", "every", "each", "multiple"]),
            "complexity_indicators": []
        }

        # Determine complexity based on analysis
        complexity_score = sum([
            analysis["involves_search"],
            analysis["involves_forms"],
            analysis["involves_extraction"],
            analysis["involves_filtering"],
            analysis["requires_loops"]
        ])

        if complexity_score >= 3:
            analysis["complexity"] = TaskComplexity.COMPLEX
        elif complexity_score >= 2:
            analysis["complexity"] = TaskComplexity.MODERATE
        else:
            analysis["complexity"] = TaskComplexity.SIMPLE

        return analysis

    def _generate_header(self) -> str:
        """Generate code header with imports"""
        return """# Generated Browser Automation Script
# Created by WYN360 Enhanced Code Generator

import asyncio
import json
import re
from typing import Dict, List, Optional, Any

# Browser automation result
result = None"""

    def _generate_setup(self, context: CodeGenerationContext) -> str:
        """Generate setup and initialization code"""
        return f"""
# Setup and initialization
url = "{context.url}"
task_description = "{context.task_description}"

print(f"Starting automation task: {{task_description}}")
print(f"Target URL: {{url}}")
"""

    async def _generate_main_logic(self,
                                 context: CodeGenerationContext,
                                 task_analysis: Dict[str, Any]) -> str:
        """Generate main automation logic based on task analysis"""

        logic_blocks = []

        # Navigation
        if task_analysis["involves_navigation"] or context.url:
            navigation_code = self._code_patterns["navigation"].format(url=context.url)
            logic_blocks.append(navigation_code)

        # Search functionality
        if task_analysis["involves_search"]:
            search_terms = self._extract_search_terms(context.task_description)
            for search_term in search_terms:
                search_code = self._code_patterns["search_action"].format(
                    search_term=search_term
                )
                logic_blocks.append(search_code)

        # Form interactions
        if task_analysis["involves_forms"]:
            form_data = self._extract_form_data(context.task_description)
            form_code = self._code_patterns["form_interaction"].format(
                form_data=json.dumps(form_data)
            )
            logic_blocks.append(form_code)

        # Filtering and interactions
        if task_analysis["involves_filtering"]:
            filter_code = await self._generate_filter_code(context.task_description)
            logic_blocks.append(filter_code)

        # Data extraction
        if task_analysis["involves_extraction"]:
            extraction_code = await self._generate_extraction_code(
                context.task_description,
                context.expected_output_schema
            )
            logic_blocks.append(extraction_code)

        return "\n\n".join(logic_blocks)

    def _extract_search_terms(self, task_description: str) -> List[str]:
        """Extract search terms from task description"""
        # Look for quoted terms or common search patterns
        quoted_terms = re.findall(r'"([^"]+)"', task_description)
        if quoted_terms:
            return quoted_terms

        # Look for terms after "search for", "find", etc.
        patterns = [
            r'search for (.+?)(?:\s+(?:on|in|at)|$)',
            r'find (.+?)(?:\s+(?:on|in|at)|$)',
            r'look for (.+?)(?:\s+(?:on|in|at)|$)'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, task_description, re.IGNORECASE)
            if matches:
                return [match.strip() for match in matches]

        # Default fallback - extract key terms
        task_lower = task_description.lower()
        potential_terms = []

        # Common product terms
        if "mouse" in task_lower:
            potential_terms.append("wireless mouse")
        elif "headphone" in task_lower or "earphone" in task_lower:
            potential_terms.append("headphones")
        elif "keyboard" in task_lower:
            potential_terms.append("keyboard")

        return potential_terms if potential_terms else [""]

    def _extract_form_data(self, task_description: str) -> Dict[str, str]:
        """Extract form data from task description"""
        form_data = {}

        # Look for login information
        if "login" in task_description.lower():
            form_data.update({
                "email": "user@example.com",
                "password": "password"
            })

        # Look for registration information
        if "register" in task_description.lower() or "sign up" in task_description.lower():
            form_data.update({
                "name": "Test User",
                "email": "user@example.com",
                "password": "password123"
            })

        return form_data

    async def _generate_filter_code(self, task_description: str) -> str:
        """Generate filtering and selection code"""
        task_lower = task_description.lower()
        filter_actions = []

        # Price filters
        price_pattern = r'(?:under|less than|below)\s*\$?(\d+)'
        price_matches = re.findall(price_pattern, task_lower)
        if price_matches:
            max_price = price_matches[0]
            filter_actions.append(f"""
# Apply price filter (under ${max_price})
price_selectors = [
    'text="Under ${max_price}"',
    'text="Less than ${max_price}"',
    f'*[data-price-max="{max_price}"]',
    f'input[value="${max_price}"]'
]

price_filter_applied = False
for selector in price_selectors:
    try:
        price_filter = page.locator(selector)
        await price_filter.wait_for(state='visible', timeout=3000)
        await price_filter.click()
        price_filter_applied = True
        print(f"Applied price filter: under ${max_price}")
        break
    except:
        continue

if not price_filter_applied:
    print("Warning: Could not apply price filter")
""")

        # Rating filters
        if "star" in task_lower or "rating" in task_lower:
            filter_actions.append("""
# Apply rating filter (4+ stars)
rating_selectors = [
    'text="4 stars & Up"',
    'text="4+ stars"',
    '*[data-rating="4"]',
    'input[value="4"]'
]

rating_filter_applied = False
for selector in rating_selectors:
    try:
        rating_filter = page.locator(selector)
        await rating_filter.wait_for(state='visible', timeout=3000)
        await rating_filter.click()
        rating_filter_applied = True
        print("Applied rating filter: 4+ stars")
        break
    except:
        continue

if not rating_filter_applied:
    print("Warning: Could not apply rating filter")
""")

        return "\n".join(filter_actions)

    async def _generate_extraction_code(self,
                                      task_description: str,
                                      schema: Optional[Dict] = None) -> str:
        """Generate data extraction code"""

        if schema:
            # Generate extraction based on provided schema
            extraction_logic = self._generate_schema_based_extraction(schema)
        else:
            # Generate extraction based on task description
            extraction_logic = self._generate_task_based_extraction(task_description)

        return self._code_patterns["data_extraction"].format(
            extraction_code=extraction_logic
        )

    def _generate_schema_based_extraction(self, schema: Dict) -> str:
        """Generate extraction code based on provided schema"""
        extraction_code = "result = {}\n"

        for field_name, field_type in schema.items():
            if field_type == str:
                extraction_code += f"""
# Extract {field_name}
try:
    {field_name}_element = page.locator('.{field_name}, .title, .name, h1, h2, h3').first
    result['{field_name}'] = await {field_name}_element.inner_text()
except:
    result['{field_name}'] = None
"""
            elif field_type == float:
                extraction_code += f"""
# Extract {field_name} (price/number)
try:
    {field_name}_element = page.locator('.price, .cost, .{field_name}').first
    {field_name}_text = await {field_name}_element.inner_text()
    result['{field_name}'] = float(re.findall(r'[\\d.]+', {field_name}_text)[0])
except:
    result['{field_name}'] = None
"""
            elif field_type == bool:
                extraction_code += f"""
# Extract {field_name} (availability/boolean)
try:
    {field_name}_element = page.locator('.in-stock, .available, .{field_name}').first
    {field_name}_text = await {field_name}_element.inner_text()
    result['{field_name}'] = 'available' in {field_name}_text.lower() or 'in stock' in {field_name}_text.lower()
except:
    result['{field_name}'] = False
"""

        return extraction_code

    def _generate_task_based_extraction(self, task_description: str) -> str:
        """Generate extraction code based on task description"""
        task_lower = task_description.lower()

        if any(term in task_lower for term in ["product", "item", "mouse", "keyboard"]):
            return """
# Extract product information
result = []

try:
    # Find product containers
    products = page.locator('.product-item, .s-result-item, .product, [data-testid="product"]')

    # Extract data from each product
    for i, product in enumerate(await products.all()):
        if i >= 10:  # Limit to first 10 products
            break

        product_data = {}

        # Extract name/title
        try:
            name_element = product.locator('.title, .name, h3, .product-title, .s-link').first
            product_data['name'] = await name_element.inner_text()
        except:
            product_data['name'] = 'Unknown'

        # Extract price
        try:
            price_element = product.locator('.price, .a-price, .cost, .price-current').first
            price_text = await price_element.inner_text()
            # Extract numeric price
            price_match = re.findall(r'[\\d.]+', price_text.replace(',', ''))
            product_data['price'] = float(price_match[0]) if price_match else None
        except:
            product_data['price'] = None

        # Extract rating
        try:
            rating_element = product.locator('.rating, .stars, .a-icon-alt').first
            rating_text = await rating_element.inner_text()
            rating_match = re.findall(r'(\\d+\\.?\\d*)\\s*(?:star|out of)', rating_text)
            product_data['rating'] = float(rating_match[0]) if rating_match else None
        except:
            product_data['rating'] = None

        if product_data['name'] != 'Unknown':
            result.append(product_data)

except Exception as e:
    print(f"Extraction error: {e}")
    result = []
"""
        else:
            return """
# Extract general page data
result = {}

try:
    # Extract page title
    result['title'] = await page.title()

    # Extract main content
    main_content = page.locator('main, .main-content, .content, body')
    result['content'] = await main_content.inner_text()

    # Extract links
    links = page.locator('a[href]')
    result['links'] = []
    for link in await links.all():
        href = await link.get_attribute('href')
        text = await link.inner_text()
        if href and text.strip():
            result['links'].append({'url': href, 'text': text.strip()})
        if len(result['links']) >= 20:  # Limit links
            break

except Exception as e:
    print(f"Extraction error: {e}")
    result = {}
"""

    def _generate_result_processing(self, context: CodeGenerationContext) -> str:
        """Generate result processing and output code"""
        return """
# Process and output results
if result:
    if isinstance(result, dict):
        print("\\nExtracted Data:")
        for key, value in result.items():
            print(f"  {key}: {value}")
    elif isinstance(result, list):
        print(f"\\nExtracted {len(result)} items:")
        for i, item in enumerate(result[:5]):  # Show first 5 items
            print(f"  Item {i+1}: {item}")
        if len(result) > 5:
            print(f"  ... and {len(result) - 5} more items")
    else:
        print(f"\\nResult: {result}")
else:
    print("\\nNo data extracted")

print("\\nAutomation completed successfully!")
"""

    def _wrap_in_async_function(self, code: str) -> str:
        """Wrap code in basic async function"""
        return f"""
# Browser automation script
async def execute_automation():
{self._indent_code(code, 4)}
    return result

# Execute the automation
import asyncio
result = None

async def main():
    global result
    result = await execute_automation()
    return result

if __name__ == "__main__":
    asyncio.run(main())
"""

    def _wrap_with_error_handling(self, code: str) -> str:
        """Wrap code with comprehensive error handling"""
        return f"""
# Enhanced error handling wrapper
async def execute_automation():
    try:
{self._indent_code(code, 8)}
        return result
    except Exception as automation_error:
        print(f"Automation error occurred: {{automation_error}}")
        print("Attempting graceful recovery...")

        # Basic recovery attempt
        try:
            await page.reload()
            await page.wait_for_load_state('networkidle')
            print("Page reloaded successfully")
        except Exception as recovery_error:
            print(f"Recovery failed: {{recovery_error}}")

        # Return partial results if available
        if 'result' in locals() and result:
            print("Returning partial results...")
            return result
        else:
            print("No results to return")
            return None

# Execute the automation
import asyncio
result = None

async def main():
    global result
    result = await execute_automation()
    return result

if __name__ == "__main__":
    asyncio.run(main())
"""

    def _indent_code(self, code: str, spaces: int) -> str:
        """Indent code by specified number of spaces"""
        lines = code.split('\n')
        indented_lines = [' ' * spaces + line if line.strip() else line for line in lines]
        return '\n'.join(indented_lines)

    async def _optimize_code(self,
                           code: str,
                           context: CodeGenerationContext) -> str:
        """Apply optimization rules to generated code"""

        optimized_code = code

        if context.optimization_level == CodeOptimizationLevel.ADVANCED:
            # Add intelligent waits
            optimized_code = self._add_intelligent_waits(optimized_code)

            # Enhance selectors
            optimized_code = self._enhance_selectors(optimized_code)

            # Add performance optimizations
            optimized_code = self._add_performance_optimizations(optimized_code)

        return optimized_code

    def _add_intelligent_waits(self, code: str) -> str:
        """Add intelligent waiting strategies"""
        # Add networkidle waits after navigation
        code = re.sub(
            r"(await page\.goto\([^)]+\))",
            r"\1\n        await page.wait_for_load_state('networkidle')",
            code
        )

        # Add element visibility waits
        code = re.sub(
            r"(page\.locator\([^)]+\))",
            r"\1.wait_for(state='visible', timeout=5000)",
            code
        )

        return code

    def _enhance_selectors(self, code: str) -> str:
        """Enhance selectors with fallbacks"""
        # This would implement more sophisticated selector enhancement
        # For now, return as-is since we already include multiple selectors
        return code

    def _add_performance_optimizations(self, code: str) -> str:
        """Add performance optimizations"""
        # Add batching hints for similar operations
        optimizations = [
            "# Performance optimization: Batch similar operations when possible",
            "# Use efficient locator strategies",
            "# Minimize unnecessary waits"
        ]

        return "\n".join(optimizations) + "\n\n" + code

    async def validate_generated_code(self, code: str) -> Tuple[bool, List[str]]:
        """Validate generated code for syntax and logic errors"""
        issues = []

        try:
            # Wrap code in async function for validation if it contains await
            if 'await ' in code and 'async def' not in code:
                wrapped_code = f"""
async def validate_wrapper():
{self._indent_code(code, 4)}
"""
                compile(wrapped_code, '<generated_code>', 'exec')
            else:
                # Basic syntax check
                compile(code, '<generated_code>', 'exec')
        except SyntaxError as e:
            issues.append(f"Syntax error: {e}")

        # Check for required imports
        if 'import asyncio' not in code:
            issues.append("Missing asyncio import")

        # Check for result assignment
        if 'result =' not in code:
            issues.append("No result assignment found")

        # Check for basic error handling
        if 'try:' not in code and 'except:' not in code:
            issues.append("No error handling found")

        return len(issues) == 0, issues

    async def estimate_execution_complexity(self, context: CodeGenerationContext) -> Dict[str, Any]:
        """Estimate execution complexity and resource requirements"""

        task_analysis = await self._analyze_task(context)

        complexity_factors = {
            "navigation_steps": 1 if task_analysis["involves_navigation"] else 0,
            "search_operations": 1 if task_analysis["involves_search"] else 0,
            "form_interactions": 2 if task_analysis["involves_forms"] else 0,
            "data_extraction": 2 if task_analysis["involves_extraction"] else 0,
            "filtering_operations": 1 if task_analysis["involves_filtering"] else 0,
            "loop_operations": 3 if task_analysis["requires_loops"] else 0
        }

        total_complexity = sum(complexity_factors.values())

        return {
            "complexity_score": total_complexity,
            "estimated_execution_time": total_complexity * 2,  # seconds
            "estimated_api_calls": max(1, total_complexity // 2),
            "resource_intensity": "high" if total_complexity > 6 else "medium" if total_complexity > 3 else "low",
            "factors": complexity_factors
        }