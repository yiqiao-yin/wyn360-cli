#!/usr/bin/env python3
"""Test OpenAI provider with PDF reading."""
import os
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from wyn360_cli.agent import WYN360Agent

async def test_openai_pdf():
    """Test OpenAI PDF reading."""
    os.environ['CHOOSE_CLIENT'] = '4'
    os.environ['OPENAI_API_KEY'] = '<your_openai_key_here>'
    os.environ['OPENAI_MODEL'] = 'gpt-4o'

    try:
        print("🔄 Creating OpenAI agent...")
        agent = WYN360Agent()
        print(f"✅ Agent created: {agent.model_name}")

        print("🔄 Testing PDF reading...")
        response = await agent.agent.run("Please use the read_pdf tool to analyze tests/test_files/test.pdf")
        print(f"📄 Response preview: {response.output[:200]}...")
        print("✅ OpenAI PDF reading successful!")

    except Exception as e:
        print(f"❌ OpenAI Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_openai_pdf())