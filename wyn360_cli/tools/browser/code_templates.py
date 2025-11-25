"""
Code Templates for Browser Automation

This module provides reusable templates and patterns for common browser
automation tasks, inspired by smolagents' code-first approach.
"""

from typing import Dict, List, Optional
from enum import Enum


class TemplateCategory(Enum):
    """Categories of automation templates"""
    NAVIGATION = "navigation"
    SEARCH = "search"
    FORMS = "forms"
    DATA_EXTRACTION = "data_extraction"
    INTERACTION = "interaction"
    ERROR_HANDLING = "error_handling"


class AutomationTemplates:
    """
    Collection of reusable browser automation code templates
    """

    def __init__(self):
        self._templates = self._initialize_templates()
        self._patterns = self._initialize_patterns()

    def _initialize_templates(self) -> Dict[str, Dict[str, str]]:
        """Initialize all automation templates by category"""
        return {
            TemplateCategory.NAVIGATION.value: {
                "basic_navigation": """
# Navigate to URL with basic error handling
try:
    await page.goto('{url}', wait_until='domcontentloaded')
    await page.wait_for_load_state('networkidle')
except Exception as e:
    print(f"Navigation error: {{e}}")
    await page.goto('{url}', wait_until='load')
""",
                "navigation_with_retry": """
# Navigate with retry logic
max_retries = 3
for attempt in range(max_retries):
    try:
        await page.goto('{url}', wait_until='networkidle')
        print("Navigation successful")
        break
    except Exception as e:
        print(f"Navigation attempt {{attempt + 1}} failed: {{e}}")
        if attempt == max_retries - 1:
            raise
        await asyncio.sleep(2)
""",
                "conditional_navigation": """
# Navigate only if not already on target page
current_url = page.url
if not current_url.startswith('{base_url}'):
    await page.goto('{url}', wait_until='domcontentloaded')
    await page.wait_for_load_state('networkidle')
else:
    print("Already on target domain")
"""
            },

            TemplateCategory.SEARCH.value: {
                "robust_search": """
# Robust search with multiple selector strategies
search_term = '{search_term}'
search_selectors = [
    'input[placeholder*="search" i]',
    'input[name*="search" i]',
    'input[type="search"]',
    'input[aria-label*="search" i]',
    '.search-input input',
    '#search',
    '.search-box input'
]

search_executed = False
for selector in search_selectors:
    try:
        search_element = page.locator(selector).first
        await search_element.wait_for(state='visible', timeout=3000)

        # Clear any existing text and enter search term
        await search_element.clear()
        await search_element.fill(search_term)

        # Try Enter key first, then look for search button
        await search_element.press('Enter')
        await page.wait_for_load_state('networkidle', timeout=10000)

        search_executed = True
        print(f"Search executed successfully with selector: {{selector}}")
        break

    except Exception as e:
        print(f"Search attempt with {{selector}} failed: {{e}}")
        continue

if not search_executed:
    # Fallback: Look for search button
    search_buttons = [
        'button[type="submit"]',
        'button:has-text("Search")',
        '.search-button',
        '.search-btn',
        '*[data-testid*="search" i]'
    ]

    for btn_selector in search_buttons:
        try:
            search_btn = page.locator(btn_selector)
            await search_btn.wait_for(state='visible', timeout=3000)
            await search_btn.click()
            search_executed = True
            print(f"Search executed via button: {{btn_selector}}")
            break
        except:
            continue

if not search_executed:
    raise Exception(f"Could not execute search for: {{search_term}}")
""",
                "search_with_suggestions": """
# Search with autocomplete/suggestions handling
search_term = '{search_term}'
search_input = page.locator('input[placeholder*="search" i], input[name*="search" i]').first

await search_input.wait_for(state='visible')
await search_input.fill(search_term)

# Wait for suggestions to appear
try:
    await page.wait_for_selector('.suggestions, .autocomplete, .search-dropdown', timeout=2000)

    # Look for exact match in suggestions
    suggestion_selectors = [
        f'text="{search_term}"',
        f'*:has-text("{search_term}"):visible'
    ]

    suggestion_clicked = False
    for selector in suggestion_selectors:
        try:
            await page.locator(selector).first.click()
            suggestion_clicked = True
            break
        except:
            continue

    if not suggestion_clicked:
        await search_input.press('Enter')

except:
    # No suggestions appeared, just press Enter
    await search_input.press('Enter')

await page.wait_for_load_state('networkidle')
"""
            },

            TemplateCategory.FORMS.value: {
                "form_fill_robust": """
# Robust form filling with validation
form_data = {form_data}

for field_name, field_value in form_data.items():
    print(f"Filling field: {{field_name}}")

    # Multiple selector strategies for each field
    field_selectors = [
        f'input[name="{field_name}"]',
        f'input[id="{field_name}"]',
        f'input[placeholder*="{field_name}" i]',
        f'*[data-testid="{field_name}"]',
        f'label:has-text("{field_name}") + input',
        f'label:has-text("{field_name}") input'
    ]

    field_filled = False
    for selector in field_selectors:
        try:
            field_element = page.locator(selector).first
            await field_element.wait_for(state='visible', timeout=3000)

            # Check field type and fill accordingly
            field_type = await field_element.get_attribute('type') or 'text'

            if field_type == 'checkbox':
                if field_value:
                    await field_element.check()
                else:
                    await field_element.uncheck()
            elif field_type == 'radio':
                await field_element.check()
            elif field_type in ['select', 'select-one']:
                await field_element.select_option(str(field_value))
            else:
                await field_element.clear()
                await field_element.fill(str(field_value))

            field_filled = True
            print(f"Successfully filled {{field_name}} using {{selector}}")
            break

        except Exception as e:
            print(f"Failed to fill {{field_name}} with {{selector}}: {{e}}")
            continue

    if not field_filled:
        print(f"Warning: Could not fill field {{field_name}}")

print("Form filling completed")
""",
                "login_form": """
# Login form with common patterns
username = '{username}'
password = '{password}'

# Fill username
username_selectors = [
    'input[name="username"]',
    'input[name="email"]',
    'input[type="email"]',
    'input[id*="username" i]',
    'input[id*="email" i]',
    'input[placeholder*="username" i]',
    'input[placeholder*="email" i]'
]

username_filled = False
for selector in username_selectors:
    try:
        username_field = page.locator(selector).first
        await username_field.wait_for(state='visible', timeout=3000)
        await username_field.fill(username)
        username_filled = True
        print(f"Username filled with selector: {{selector}}")
        break
    except:
        continue

# Fill password
password_selectors = [
    'input[name="password"]',
    'input[type="password"]',
    'input[id*="password" i]',
    'input[placeholder*="password" i]'
]

password_filled = False
for selector in password_selectors:
    try:
        password_field = page.locator(selector).first
        await password_field.wait_for(state='visible', timeout=3000)
        await password_field.fill(password)
        password_filled = True
        print(f"Password filled with selector: {{selector}}")
        break
    except:
        continue

# Submit form
if username_filled and password_filled:
    submit_selectors = [
        'button[type="submit"]',
        'input[type="submit"]',
        'button:has-text("Log in")',
        'button:has-text("Sign in")',
        '.login-button',
        '.signin-button'
    ]

    for selector in submit_selectors:
        try:
            submit_btn = page.locator(selector)
            await submit_btn.wait_for(state='visible', timeout=3000)
            await submit_btn.click()
            print(f"Login submitted with selector: {{selector}}")
            break
        except:
            continue

    # Wait for login to process
    await page.wait_for_load_state('networkidle')
    print("Login process completed")
else:
    raise Exception("Could not fill login credentials")
"""
            },

            TemplateCategory.DATA_EXTRACTION.value: {
                "product_extraction": """
# Extract product data with robust selectors
result = []

# Find product containers
product_selectors = [
    '.product-item',
    '.s-result-item',
    '.product',
    '[data-testid*="product"]',
    '.listing-item',
    '.search-result'
]

products_found = False
for selector in product_selectors:
    try:
        products = page.locator(selector)
        product_count = await products.count()
        if product_count > 0:
            print(f"Found {{product_count}} products with selector: {{selector}}")
            products_found = True

            # Extract data from each product
            for i in range(min(product_count, 20)):  # Limit to 20 products
                try:
                    product = products.nth(i)
                    product_data = {{}}

                    # Extract product name
                    name_selectors = [
                        '.title', '.name', 'h3', '.product-title',
                        '.s-link', 'a[data-testid="product-title"]',
                        '.listing-title'
                    ]

                    for name_sel in name_selectors:
                        try:
                            name_element = product.locator(name_sel).first
                            product_data['name'] = await name_element.inner_text()
                            break
                        except:
                            continue

                    # Extract price
                    price_selectors = [
                        '.price', '.a-price', '.cost', '.price-current',
                        '.listing-price', '[data-testid*="price"]'
                    ]

                    for price_sel in price_selectors:
                        try:
                            price_element = product.locator(price_sel).first
                            price_text = await price_element.inner_text()
                            # Extract numeric price
                            import re
                            price_match = re.findall(r'[\\d,]+\\.?\\d*', price_text.replace(',', ''))
                            if price_match:
                                product_data['price'] = float(price_match[0])
                            break
                        except:
                            continue

                    # Extract rating
                    rating_selectors = [
                        '.rating', '.stars', '.a-icon-alt',
                        '[data-testid*="rating"]', '.star-rating'
                    ]

                    for rating_sel in rating_selectors:
                        try:
                            rating_element = product.locator(rating_sel).first
                            rating_text = await rating_element.inner_text()
                            rating_match = re.findall(r'(\\d+\\.?\\d*)', rating_text)
                            if rating_match:
                                product_data['rating'] = float(rating_match[0])
                            break
                        except:
                            continue

                    # Extract URL
                    try:
                        link_element = product.locator('a').first
                        product_data['url'] = await link_element.get_attribute('href')
                    except:
                        product_data['url'] = None

                    if product_data.get('name'):
                        result.append(product_data)

                except Exception as e:
                    print(f"Error extracting product {{i}}: {{e}}")
                    continue

            break  # Successfully found products

    except Exception as e:
        print(f"Failed to find products with {{selector}}: {{e}}")
        continue

if not products_found:
    print("Warning: No products found with any selector")

print(f"Extracted {{len(result)}} products")
""",
                "table_extraction": """
# Extract data from tables
result = []

table_selectors = [
    'table',
    '.data-table',
    '.table',
    '[role="table"]'
]

table_found = False
for selector in table_selectors:
    try:
        table = page.locator(selector).first
        await table.wait_for(state='visible', timeout=3000)

        # Extract headers
        header_rows = table.locator('thead tr, tr:first-child')
        headers = []

        try:
            first_row = header_rows.first
            header_cells = first_row.locator('th, td')

            for i in range(await header_cells.count()):
                cell = header_cells.nth(i)
                header_text = await cell.inner_text()
                headers.append(header_text.strip())

        except:
            headers = [f'Column {{i+1}}' for i in range(5)]  # Default headers

        print(f"Table headers: {{headers}}")

        # Extract data rows
        data_rows = table.locator('tbody tr, tr:not(:first-child)')
        row_count = await data_rows.count()

        for i in range(min(row_count, 50)):  # Limit to 50 rows
            try:
                row = data_rows.nth(i)
                cells = row.locator('td, th')
                cell_count = await cells.count()

                row_data = {{}}
                for j in range(min(cell_count, len(headers))):
                    cell = cells.nth(j)
                    cell_text = await cell.inner_text()
                    header_name = headers[j] if j < len(headers) else f'Column_{{j+1}}'
                    row_data[header_name] = cell_text.strip()

                if row_data:
                    result.append(row_data)

            except Exception as e:
                print(f"Error extracting row {{i}}: {{e}}")
                continue

        table_found = True
        print(f"Extracted {{len(result)}} rows from table")
        break

    except Exception as e:
        print(f"Failed to extract table with {{selector}}: {{e}}")
        continue

if not table_found:
    print("Warning: No table found")
"""
            },

            TemplateCategory.INTERACTION.value: {
                "filter_application": """
# Apply filters with multiple strategies
filters = {filters}

for filter_name, filter_value in filters.items():
    print(f"Applying filter: {{filter_name}} = {{filter_value}}")

    filter_applied = False

    # Strategy 1: Look for exact text match
    try:
        filter_element = page.locator(f'text="{filter_value}"').first
        await filter_element.wait_for(state='visible', timeout=3000)
        await filter_element.click()
        filter_applied = True
        print(f"Applied {{filter_name}} via exact text match")
    except:
        pass

    if not filter_applied:
        # Strategy 2: Look for input/select elements
        input_selectors = [
            f'input[name="{filter_name}"]',
            f'select[name="{filter_name}"]',
            f'*[data-filter="{filter_name}"]'
        ]

        for selector in input_selectors:
            try:
                input_element = page.locator(selector).first
                await input_element.wait_for(state='visible', timeout=3000)

                # Handle different input types
                tag_name = await input_element.evaluate('el => el.tagName.toLowerCase()')
                input_type = await input_element.get_attribute('type') or 'text'

                if tag_name == 'select':
                    await input_element.select_option(str(filter_value))
                elif input_type == 'checkbox':
                    if filter_value:
                        await input_element.check()
                elif input_type == 'radio':
                    await input_element.check()
                else:
                    await input_element.fill(str(filter_value))

                filter_applied = True
                print(f"Applied {{filter_name}} via input element")
                break

            except:
                continue

    if not filter_applied:
        print(f"Warning: Could not apply filter {{filter_name}}")

print("Filter application completed")
""",
                "pagination_navigation": """
# Navigate through pagination
page_data = []
max_pages = {max_pages}
current_page = 1

while current_page <= max_pages:
    print(f"Processing page {{current_page}}")

    # Extract data from current page
    try:
        # Add your data extraction logic here
        page_results = []  # This would be filled by extraction logic
        page_data.extend(page_results)
        print(f"Extracted {{len(page_results)}} items from page {{current_page}}")
    except Exception as e:
        print(f"Error extracting data from page {{current_page}}: {{e}}")

    # Navigate to next page
    if current_page < max_pages:
        next_page_selectors = [
            'a:has-text("Next")',
            '.next-page',
            '.pagination-next',
            'button:has-text("Next")',
            f'a:has-text("{current_page + 1}")'
        ]

        next_clicked = False
        for selector in next_page_selectors:
            try:
                next_element = page.locator(selector)
                await next_element.wait_for(state='visible', timeout=3000)

                # Check if element is enabled
                is_disabled = await next_element.get_attribute('disabled')
                if not is_disabled:
                    await next_element.click()
                    await page.wait_for_load_state('networkidle')
                    next_clicked = True
                    break

            except:
                continue

        if not next_clicked:
            print("Could not find next page link, stopping pagination")
            break

    current_page += 1

result = page_data
print(f"Total items collected: {{len(result)}}")
"""
            },

            TemplateCategory.ERROR_HANDLING.value: {
                "retry_wrapper": """
# Retry wrapper for unreliable operations
async def retry_operation(operation_func, max_retries=3, delay=1):
    for attempt in range(max_retries):
        try:
            return await operation_func()
        except Exception as e:
            print(f"Attempt {{attempt + 1}} failed: {{e}}")
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(delay * (attempt + 1))  # Exponential backoff
""",
                "graceful_degradation": """
# Graceful degradation for missing elements
async def safe_extract_text(locator_str, default="Not found"):
    try:
        element = page.locator(locator_str).first
        await element.wait_for(state='visible', timeout=3000)
        return await element.inner_text()
    except:
        return default

async def safe_click(locator_str):
    try:
        element = page.locator(locator_str).first
        await element.wait_for(state='visible', timeout=3000)
        await element.click()
        return True
    except:
        return False
""",
                "error_recovery": """
# Error recovery strategies
try:
    # Main automation logic here
    pass
except Exception as main_error:
    print(f"Main automation failed: {{main_error}}")

    # Recovery strategy 1: Refresh page and retry
    try:
        print("Attempting page refresh recovery...")
        await page.reload()
        await page.wait_for_load_state('networkidle')
        # Retry simplified version of main logic
        # ... retry logic here

    except Exception as refresh_error:
        print(f"Refresh recovery failed: {{refresh_error}}")

        # Recovery strategy 2: Navigate back to start
        try:
            print("Attempting navigation recovery...")
            await page.goto(url, wait_until='networkidle')
            # Retry with different approach
            # ... alternative logic here

        except Exception as nav_error:
            print(f"All recovery attempts failed: {{nav_error}}")
            # Set partial results or error state
            result = {{"error": "Automation failed with all recovery attempts"}}
"""
            }
        }

    def _initialize_patterns(self) -> Dict[str, str]:
        """Initialize common code patterns"""
        return {
            "wait_for_element": """
async def wait_for_element(selector, timeout=5000):
    try:
        element = page.locator(selector).first
        await element.wait_for(state='visible', timeout=timeout)
        return element
    except:
        return None
""",
            "safe_fill": """
async def safe_fill(selector, value):
    element = await wait_for_element(selector)
    if element:
        await element.clear()
        await element.fill(str(value))
        return True
    return False
""",
            "extract_with_fallback": """
async def extract_with_fallback(selectors, default=None):
    for selector in selectors:
        try:
            element = await wait_for_element(selector, timeout=2000)
            if element:
                return await element.inner_text()
        except:
            continue
    return default
"""
        }

    def get_template(self, category: str, template_name: str) -> Optional[str]:
        """Get a specific template by category and name"""
        return self._templates.get(category, {}).get(template_name)

    def get_category_templates(self, category: str) -> Dict[str, str]:
        """Get all templates in a category"""
        return self._templates.get(category, {})

    def list_templates(self) -> Dict[str, List[str]]:
        """List all available templates by category"""
        return {
            category: list(templates.keys())
            for category, templates in self._templates.items()
        }

    def get_pattern(self, pattern_name: str) -> Optional[str]:
        """Get a specific code pattern"""
        return self._patterns.get(pattern_name)

    def list_patterns(self) -> List[str]:
        """List all available patterns"""
        return list(self._patterns.keys())

    def search_templates(self, keyword: str) -> Dict[str, List[str]]:
        """Search for templates containing a keyword"""
        results = {}

        for category, templates in self._templates.items():
            matching_templates = []
            for name, code in templates.items():
                if keyword.lower() in name.lower() or keyword.lower() in code.lower():
                    matching_templates.append(name)

            if matching_templates:
                results[category] = matching_templates

        return results

    def generate_custom_template(self,
                                name: str,
                                code: str,
                                category: str = "custom") -> bool:
        """Add a custom template"""
        try:
            if category not in self._templates:
                self._templates[category] = {}

            self._templates[category][name] = code
            return True
        except:
            return False