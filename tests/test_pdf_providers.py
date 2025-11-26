#!/usr/bin/env python3
"""
Test script to verify PDF reading functionality across all AI providers.

This script tests whether Anthropic Claude, Google Gemini, and OpenAI
can properly trigger the read_pdf tool with the tests/test.pdf file.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the package to the path
sys.path.insert(0, str(Path(__file__).parent))

from wyn360_cli.agent import WYN360Agent


async def test_provider_pdf_reading(provider_name: str, choose_client: int, model_override: str = None):
    """Test PDF reading for a specific provider."""
    print(f"\n{'='*60}")
    print(f"Testing {provider_name} (CHOOSE_CLIENT={choose_client})")
    print(f"{'='*60}")

    # Set environment variables for this test
    original_choose_client = os.environ.get('CHOOSE_CLIENT')
    original_model = os.environ.get('ANTHROPIC_MODEL')

    try:
        os.environ['CHOOSE_CLIENT'] = str(choose_client)
        if model_override:
            os.environ['ANTHROPIC_MODEL'] = model_override

        # Create agent
        print(f"🔄 Creating {provider_name} agent...")
        agent = WYN360Agent()

        print(f"✅ Agent created successfully")
        print(f"   - Provider: {provider_name}")
        print(f"   - Model: {agent.model_name}")
        print(f"   - use_openai: {getattr(agent, 'use_openai', False)}")
        print(f"   - use_gemini: {getattr(agent, 'use_gemini', False)}")
        print(f"   - use_bedrock: {getattr(agent, 'use_bedrock', False)}")
        print(f"   - cache_dir: {agent.cache_dir}")

        # Test 1: Check if PDF file exists
        pdf_path = Path("tests/test_files/test.pdf")
        if pdf_path.exists():
            print(f"✅ PDF file found: {pdf_path} ({pdf_path.stat().st_size} bytes)")
        else:
            print(f"❌ PDF file not found: {pdf_path}")
            return False, "PDF file not found"

        # Test 2: Try to read the PDF
        print(f"🔄 Testing PDF reading...")

        # Use different prompts to ensure tool triggering
        test_prompts = [
            "Please read the file tests/test_files/test.pdf and give me a brief summary",
            "Use the read_pdf tool to analyze tests/test_files/test.pdf",
            "I need you to read and summarize the PDF file at tests/test_files/test.pdf"
        ]

        success = False
        for i, prompt in enumerate(test_prompts, 1):
            try:
                print(f"   Attempt {i}: {prompt[:50]}...")
                response = await agent.agent.run(prompt)
                response_text = response.output

                # Check if the response indicates successful PDF reading
                pdf_indicators = [
                    "pdf", "document", "page", "article", "content", "summary",
                    "text", "chapter", "section", "title", "author"
                ]

                # Check for successful tool usage
                generic_responses = [
                    "install", "library", "package", "pip install",
                    "technical issue", "try again later", "can't read",
                    "unable to", "not available"
                ]

                has_pdf_content = any(indicator.lower() in response_text.lower()
                                    for indicator in pdf_indicators)
                has_generic_response = any(generic.lower() in response_text.lower()
                                         for generic in generic_responses)

                print(f"   Response length: {len(response_text)} characters")
                print(f"   Has PDF content indicators: {has_pdf_content}")
                print(f"   Has generic response: {has_generic_response}")
                print(f"   Response preview: {response_text[:200]}...")

                if has_pdf_content and not has_generic_response and len(response_text) > 100:
                    print(f"✅ PDF reading appears successful!")
                    success = True
                    break
                else:
                    print(f"⚠️  Response suggests tool may not have been called properly")

            except Exception as e:
                print(f"❌ Error during attempt {i}: {e}")
                continue

        if success:
            return True, "PDF reading successful"
        else:
            return False, "PDF tool not triggered properly"

    except Exception as e:
        print(f"❌ Failed to test {provider_name}: {e}")
        import traceback
        traceback.print_exc()
        return False, f"Agent creation failed: {e}"

    finally:
        # Restore original environment
        if original_choose_client is not None:
            os.environ['CHOOSE_CLIENT'] = original_choose_client
        else:
            os.environ.pop('CHOOSE_CLIENT', None)

        if original_model is not None:
            os.environ['ANTHROPIC_MODEL'] = original_model


async def main():
    """Run comprehensive PDF reading tests across all providers."""
    print("📊 WYN360 CLI - PDF Reading Provider Test Suite")
    print("=" * 70)

    # Check if we have the required API keys
    print("🔑 Checking API Key Availability:")
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    gemini_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
    openai_key = os.getenv('OPENAI_API_KEY')

    print(f"   Anthropic: {'✅ Available' if anthropic_key else '❌ Missing'}")
    print(f"   Gemini: {'✅ Available' if gemini_key else '❌ Missing'}")
    print(f"   OpenAI: {'✅ Available' if openai_key else '❌ Missing'}")

    # Test configuration
    test_configs = []

    if anthropic_key:
        test_configs.append(("Anthropic Claude", 1, "claude-sonnet-4-20250514"))

    if gemini_key:
        test_configs.append(("Google Gemini", 3, None))

    if openai_key:
        test_configs.append(("OpenAI", 4, None))

    if not test_configs:
        print("❌ No API keys available for testing!")
        return

    # Run tests
    results = []
    for provider_name, choose_client, model_override in test_configs:
        success, message = await test_provider_pdf_reading(provider_name, choose_client, model_override)
        results.append((provider_name, success, message))

        # Add delay between tests
        await asyncio.sleep(1)

    # Summary
    print(f"\n{'='*70}")
    print("📊 TEST SUMMARY")
    print(f"{'='*70}")

    for provider_name, success, message in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status:8} {provider_name:15} - {message}")

    # Overall result
    total_tests = len(results)
    passed_tests = sum(1 for _, success, _ in results if success)

    print(f"\n🎯 Overall Result: {passed_tests}/{total_tests} providers working")

    if passed_tests == total_tests:
        print("🎉 All providers successfully trigger PDF reading tools!")
    elif passed_tests == 0:
        print("⚠️  No providers are working - investigate core PDF tool issues")
    else:
        print("⚠️  Some providers need attention - check specific provider configurations")

    return passed_tests, total_tests


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⛔ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()