#!/usr/bin/env python3
"""Test Google Gemini provider with PDF reading."""
import os
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from wyn360_cli.agent import WYN360Agent

async def test_gemini_pdf():
    """Test Google Gemini PDF reading."""
    os.environ['CHOOSE_CLIENT'] = '3'
    os.environ['GEMINI_API_KEY'] = '<your_gemini_key_here>'
    os.environ['GEMINI_MODEL'] = 'gemini-2.5-flash'

    try:
        print("🔄 Creating Google Gemini agent...")
        agent = WYN360Agent()
        print(f"✅ Agent created: {agent.model_name}")

        print("🔄 Testing PDF reading...")
        response = await agent.agent.run("Please use the read_pdf tool to analyze tests/test_files/test.pdf")
        print(f"📄 Response preview: {response.output[:200]}...")
        print("✅ Google Gemini PDF reading successful!")

    except Exception as e:
        print(f"❌ Google Gemini Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_gemini_pdf())