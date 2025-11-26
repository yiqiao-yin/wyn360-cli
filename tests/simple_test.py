#!/usr/bin/env python3
"""
Simple test script to debug PDF reading issues.
"""
import os
import sys
import asyncio
from pathlib import Path

# Add the package to the path
sys.path.insert(0, str(Path(__file__).parent))

from wyn360_cli.agent import WYN360Agent

async def test_pdf():
    """Simple PDF reading test."""

    # Set Anthropic mode
    os.environ['CHOOSE_CLIENT'] = '1'
    os.environ['ANTHROPIC_API_KEY'] = '<your_anthropic_key_here>'
    os.environ['ANTHROPIC_MODEL'] = 'claude-sonnet-4-20250514'

    try:
        print("🔄 Creating Anthropic agent...")
        agent = WYN360Agent()
        print(f"✅ Agent created: {agent.model_name}")

        print("🔄 Testing PDF reading...")
        response = await agent.agent.run("Please use the read_pdf tool to analyze tests/test_files/test.pdf")
        print(f"📄 Response: {response.output[:200]}...")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_pdf())