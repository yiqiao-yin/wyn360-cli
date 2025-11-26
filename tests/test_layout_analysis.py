#!/usr/bin/env python3
"""
Test script for PyMuPDF Layout enhanced PDF analysis.

This script tests the new layout analysis integration that provides:
- 10x faster PDF parsing
- Enhanced structure detection
- Better table extraction
- Automatic OCR when beneficial
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the package to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from wyn360_cli.agent import WYN360Agent


async def test_layout_analysis():
    """Test layout analysis enhanced PDF reading with different providers."""

    # Test configuration - using Anthropic by default
    os.environ['CHOOSE_CLIENT'] = '1'
    os.environ['ANTHROPIC_API_KEY'] = '<your_anthropic_key_here>'
    os.environ['ANTHROPIC_MODEL'] = 'claude-sonnet-4-20250514'

    print("🔬 PyMuPDF Layout Analysis Test")
    print("=" * 50)

    try:
        # Test 1: Check if layout analysis is available
        print("🔍 Checking layout analysis availability...")
        from wyn360_cli.document_readers import HAS_PYMUPDF_LAYOUT

        if HAS_PYMUPDF_LAYOUT:
            print("✅ PyMuPDF Layout is available")
        else:
            print("❌ PyMuPDF Layout not available")
            print("📦 Install with: poetry add pymupdf-layout pymupdf4llm")
            return

        # Test 2: Create agent and test enhanced PDF reading
        print("\n🤖 Creating AI agent...")
        agent = WYN360Agent()
        print(f"✅ Agent created: {agent.model_name}")

        # Test 3: Test layout-enhanced PDF reading
        pdf_path = "tests/test_files/test.pdf"
        if not Path(pdf_path).exists():
            print(f"❌ PDF file not found: {pdf_path}")
            return

        print(f"\n📄 Testing layout-enhanced PDF reading...")
        print(f"📁 File: {pdf_path}")

        # Test with explicit request for layout analysis
        prompt = f"""Please analyze the PDF file at {pdf_path} using enhanced layout analysis.
        I want to see how the new PyMuPDF Layout integration improves the structure detection and parsing speed."""

        print("🔄 Running analysis...")
        response = await agent.agent.run(prompt)

        # Check response for layout enhancement indicators
        response_text = response.output
        layout_indicators = [
            "layout", "structure", "markdown", "enhanced", "pymupdf_layout",
            "table", "header", "section"
        ]

        enhanced_features = sum(1 for indicator in layout_indicators
                               if indicator.lower() in response_text.lower())

        print(f"\n📊 Analysis Results:")
        print(f"   📝 Response length: {len(response_text)} characters")
        print(f"   🎯 Layout features detected: {enhanced_features}/{len(layout_indicators)}")

        # Show preview of response
        preview_length = 300
        print(f"\n📖 Response Preview:")
        print("-" * 50)
        print(response_text[:preview_length] + ("..." if len(response_text) > preview_length else ""))
        print("-" * 50)

        # Check if layout analysis was actually used
        if "engine" in response_text.lower() and "layout" in response_text.lower():
            print("✅ Layout analysis appears to have been used!")
        elif enhanced_features >= 3:
            print("✅ Enhanced structure detection appears to be working!")
        else:
            print("⚠️  Layout enhancement may not be active - check configuration")

        print("\n🎉 Layout analysis test completed!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


async def compare_standard_vs_layout():
    """Compare standard vs layout-enhanced PDF reading."""
    print("\n" + "=" * 60)
    print("📊 COMPARISON: Standard vs Layout-Enhanced Analysis")
    print("=" * 60)

    # This would require modifying the PDFReader to allow disabling layout analysis
    # for comparison purposes. For now, we'll just show the concept.

    print("🔄 This comparison feature could test:")
    print("   • Parsing speed differences (layout should be ~10x faster)")
    print("   • Structure detection quality")
    print("   • Table extraction accuracy")
    print("   • Header/footer filtering")
    print("   • Automatic OCR activation")

    print("\n💡 To implement full comparison:")
    print("   1. Add enable_layout_analysis=False option to PDFReader")
    print("   2. Time both approaches")
    print("   3. Compare output quality metrics")


if __name__ == "__main__":
    print("🚀 Starting PyMuPDF Layout Analysis Tests...")

    try:
        # Run main test
        asyncio.run(test_layout_analysis())

        # Show comparison concept
        asyncio.run(compare_standard_vs_layout())

    except KeyboardInterrupt:
        print("\n⛔ Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Test suite failed: {e}")
        import traceback
        traceback.print_exc()