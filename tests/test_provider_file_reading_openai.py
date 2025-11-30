#!/usr/bin/env python3
"""Unit tests for OpenAI API provider file reading capabilities."""

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


class TestOpenAIFileReading:
    """Test file reading tools with OpenAI API provider."""

    @pytest.fixture(scope="class")
    def setup_openai_client(self):
        """Setup OpenAI client for testing - matches user documentation."""
        # Configure environment exactly as documented for users:
        # export CHOOSE_CLIENT=4
        # export OPENAI_API_KEY=your_key_here  # find in .env file
        # export OPENAI_MODEL=gpt-4o

        # Set hardcoded values as documented
        os.environ['CHOOSE_CLIENT'] = '4'  # OpenAI API
        os.environ['OPENAI_MODEL'] = 'gpt-4o'

        # Get API key from .env file (already loaded via load_dotenv)
        openai_key = os.getenv('OPENAI_API_KEY')
        if not openai_key:
            pytest.skip("OPENAI_API_KEY not found in .env file")

        # Set API key from .env
        os.environ['OPENAI_API_KEY'] = openai_key

        return openai_key

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
    async def test_openai_pdf_reading(self, setup_openai_client, test_files_paths):
        """Test OpenAI API can read PDF files through read_pdf tool."""
        print("🔄 Testing OpenAI API PDF reading...")

        try:
            # Create agent
            agent = WYN360Agent()
            print(f"✅ Agent created: {agent.model_name}")
            assert "gpt" in agent.model_name.lower() or "openai" in agent.model_name.lower()

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
            print("✅ OpenAI PDF reading successful!")

        except Exception as e:
            print(f"❌ OpenAI PDF Error: {e}")
            pytest.fail(f"OpenAI PDF reading failed: {e}")

    @pytest.mark.asyncio
    async def test_openai_excel_reading(self, setup_openai_client, test_files_paths):
        """Test OpenAI API can read Excel files through read_excel tool."""
        print("🔄 Testing OpenAI API Excel reading...")

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
            print("✅ OpenAI Excel reading successful!")

        except Exception as e:
            print(f"❌ OpenAI Excel Error: {e}")
            pytest.fail(f"OpenAI Excel reading failed: {e}")

    @pytest.mark.asyncio
    async def test_openai_word_reading(self, setup_openai_client, test_files_paths):
        """Test OpenAI API can read Word documents through read_word tool."""
        print("🔄 Testing OpenAI API Word reading...")

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
            print("✅ OpenAI Word reading successful!")

        except Exception as e:
            print(f"❌ OpenAI Word Error: {e}")
            pytest.fail(f"OpenAI Word reading failed: {e}")

    @pytest.mark.asyncio
    async def test_openai_sequential_file_reading(self, setup_openai_client, test_files_paths):
        """Test OpenAI API can handle sequential file reading requests."""
        print("🔄 Testing OpenAI API sequential file reading...")

        try:
            # Create agent
            agent = WYN360Agent()
            print(f"✅ Agent created: {agent.model_name}")

            # Test reading files in sequence
            pdf_path = test_files_paths['pdf']
            xlsx_path = test_files_paths['xlsx']
            docx_path = test_files_paths['docx']

            # First request - PDF
            response1 = await agent.agent.run(
                f"Please read this PDF: {pdf_path} and tell me what it's about."
            )
            response1_text = getattr(response1, 'output', '') or getattr(response1, 'data', '')
            assert len(response1_text) > 30, "PDF response too short"

            # Second request - Excel
            response2 = await agent.agent.run(
                f"Now please read this Excel file: {xlsx_path} and describe its structure."
            )
            response2_text = getattr(response2, 'output', '') or getattr(response2, 'data', '')
            assert len(response2_text) > 30, "Excel response too short"

            # Third request - Word
            response3 = await agent.agent.run(
                f"Finally, read this Word document: {docx_path} and summarize it."
            )
            response3_text = getattr(response3, 'output', '') or getattr(response3, 'data', '')
            assert len(response3_text) > 30, "Word response too short"

            print(f"📁 Sequential reading successful - all files processed")
            print("✅ OpenAI sequential file reading successful!")

        except Exception as e:
            print(f"❌ OpenAI Sequential Reading Error: {e}")
            pytest.fail(f"OpenAI sequential file reading failed: {e}")

    @pytest.mark.asyncio
    async def test_openai_file_comparison(self, setup_openai_client, test_files_paths):
        """Test OpenAI API can compare and analyze multiple file types."""
        print("🔄 Testing OpenAI API file comparison...")

        try:
            # Create agent
            agent = WYN360Agent()
            print(f"✅ Agent created: {agent.model_name}")

            # Test comparison between different file types
            pdf_path = test_files_paths['pdf']
            xlsx_path = test_files_paths['xlsx']

            response = await agent.agent.run(
                f"I have two different types of documents:\n"
                f"1. A PDF file: {pdf_path}\n"
                f"2. An Excel file: {xlsx_path}\n"
                f"Please read both files and explain what each contains and how they differ in terms of content structure and data type."
            )

            # Verify comprehensive response
            response_text = getattr(response, 'output', '') or getattr(response, 'data', '')
            assert len(response_text) > 150, "Response too short for file comparison"

            # Should mention both file types
            response_lower = response_text.lower()
            assert 'pdf' in response_lower or 'document' in response_lower, "Should mention PDF"
            assert 'excel' in response_lower or 'spreadsheet' in response_lower, "Should mention Excel"

            print(f"🔄 File comparison response preview: {response_text[:200]}...")
            print("✅ OpenAI file comparison successful!")

        except Exception as e:
            print(f"❌ OpenAI File Comparison Error: {e}")
            pytest.fail(f"OpenAI file comparison failed: {e}")


if __name__ == "__main__":
    # Run tests directly
    import pytest
    pytest.main([__file__, "-v", "-s"])