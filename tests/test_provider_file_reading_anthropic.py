#!/usr/bin/env python3
"""Unit tests for Anthropic API provider file reading capabilities."""

import os
import sys
import pytest
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Add the parent directory to sys.path so we can import from wyn360_cli
sys.path.insert(0, str(Path(__file__).parent.parent))

from wyn360_cli.agent import WYN360Agent


class TestAnthropicFileReading:
    """Test file reading tools with Anthropic API provider."""

    @pytest.fixture(scope="class")
    def setup_anthropic_client(self):
        """Setup Anthropic client for testing - matches user documentation."""
        # Configure environment exactly as documented for users:
        # export CHOOSE_CLIENT=1
        # export ANTHROPIC_API_KEY=your_key_here  # find in .env file
        # export ANTHROPIC_MODEL=claude-sonnet-4-20250514

        # Set hardcoded values as documented
        os.environ['CHOOSE_CLIENT'] = '1'  # Anthropic API
        os.environ['ANTHROPIC_MODEL'] = 'claude-sonnet-4-20250514'

        # Get API key from .env file (already loaded via load_dotenv)
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        if not anthropic_key:
            pytest.skip("ANTHROPIC_API_KEY not found in .env file")

        # Set API key from .env
        os.environ['ANTHROPIC_API_KEY'] = anthropic_key

        return anthropic_key

    @pytest.fixture
    def test_files_paths(self):
        """Get absolute paths to test files."""
        base_path = Path(__file__).parent / "test_files"
        return {
            'pdf': str(base_path / "test.pdf"),
            'xlsx': str(base_path / "sales_invoice.xlsx"),
            'docx': str(base_path / "test_cl.docx")
        }

    @pytest.mark.asyncio
    async def test_anthropic_pdf_reading(self, setup_anthropic_client, test_files_paths):
        """Test Anthropic API can read PDF files through read_pdf tool."""
        print("🔄 Testing Anthropic API PDF reading...")

        try:
            # Create agent
            agent = WYN360Agent()
            print(f"✅ Agent created: {agent.model_name}")
            assert "anthropic" in agent.model_name.lower() or "claude" in agent.model_name.lower()

            # Test PDF reading with natural language request
            pdf_path = test_files_paths['pdf']
            assert os.path.exists(pdf_path), f"Test PDF file not found: {pdf_path}"

            response = await agent.agent.run(
                f"Please read the PDF document at {pdf_path} and give me a brief summary of its contents."
            )

            # Verify response
            assert response is not None
            assert hasattr(response, 'output') or hasattr(response, 'data')
            response_text = getattr(response, 'output', '') or getattr(response, 'data', '')
            assert len(response_text) > 50, "Response too short - PDF may not have been read"

            print(f"📄 PDF Response preview: {response_text[:200]}...")
            print("✅ Anthropic PDF reading successful!")

        except Exception as e:
            print(f"❌ Anthropic PDF Error: {e}")
            pytest.fail(f"Anthropic PDF reading failed: {e}")

    @pytest.mark.asyncio
    async def test_anthropic_excel_reading(self, setup_anthropic_client, test_files_paths):
        """Test Anthropic API can read Excel files through read_excel tool."""
        print("🔄 Testing Anthropic API Excel reading...")

        try:
            # Create agent
            agent = WYN360Agent()
            print(f"✅ Agent created: {agent.model_name}")

            # Test Excel reading
            xlsx_path = test_files_paths['xlsx']
            assert os.path.exists(xlsx_path), f"Test Excel file not found: {xlsx_path}"

            response = await agent.agent.run(
                f"Please read the Excel spreadsheet at {xlsx_path} and tell me what data it contains."
            )

            # Verify response
            assert response is not None
            response_text = getattr(response, 'output', '') or getattr(response, 'data', '')
            assert len(response_text) > 50, "Response too short - Excel may not have been read"

            print(f"📊 Excel Response preview: {response_text[:200]}...")
            print("✅ Anthropic Excel reading successful!")

        except Exception as e:
            print(f"❌ Anthropic Excel Error: {e}")
            pytest.fail(f"Anthropic Excel reading failed: {e}")

    @pytest.mark.asyncio
    async def test_anthropic_word_reading(self, setup_anthropic_client, test_files_paths):
        """Test Anthropic API can read Word documents through read_word tool."""
        print("🔄 Testing Anthropic API Word reading...")

        try:
            # Create agent
            agent = WYN360Agent()
            print(f"✅ Agent created: {agent.model_name}")

            # Test Word reading
            docx_path = test_files_paths['docx']
            assert os.path.exists(docx_path), f"Test Word file not found: {docx_path}"

            response = await agent.agent.run(
                f"Please read the Word document at {docx_path} and summarize its contents."
            )

            # Verify response
            assert response is not None
            response_text = getattr(response, 'output', '') or getattr(response, 'data', '')
            assert len(response_text) > 50, "Response too short - Word document may not have been read"

            print(f"📝 Word Response preview: {response_text[:200]}...")
            print("✅ Anthropic Word reading successful!")

        except Exception as e:
            print(f"❌ Anthropic Word Error: {e}")
            pytest.fail(f"Anthropic Word reading failed: {e}")

    @pytest.mark.asyncio
    async def test_anthropic_multiple_file_types(self, setup_anthropic_client, test_files_paths):
        """Test Anthropic API can handle requests mentioning multiple file types."""
        print("🔄 Testing Anthropic API multiple file types...")

        try:
            # Create agent
            agent = WYN360Agent()
            print(f"✅ Agent created: {agent.model_name}")

            # Test multiple file reading in sequence
            pdf_path = test_files_paths['pdf']
            xlsx_path = test_files_paths['xlsx']
            docx_path = test_files_paths['docx']

            response = await agent.agent.run(
                f"I have three documents I'd like you to analyze:\n"
                f"1. PDF: {pdf_path}\n"
                f"2. Excel: {xlsx_path}\n"
                f"3. Word: {docx_path}\n"
                f"Please read each file and give me a brief overview of what each contains."
            )

            # Verify response mentions all file types
            response_text = getattr(response, 'output', '') or getattr(response, 'data', '')
            assert len(response_text) > 100, "Response too short for multiple files"

            # Check that response mentions reading different file types
            response_lower = response_text.lower()
            assert any(word in response_lower for word in ['pdf', 'excel', 'word', 'document']), \
                "Response should mention file types"

            print(f"📁 Multiple files response preview: {response_text[:200]}...")
            print("✅ Anthropic multiple file types successful!")

        except Exception as e:
            print(f"❌ Anthropic Multiple Files Error: {e}")
            pytest.fail(f"Anthropic multiple files reading failed: {e}")


if __name__ == "__main__":
    # Run tests directly
    import pytest
    pytest.main([__file__, "-v", "-s"])