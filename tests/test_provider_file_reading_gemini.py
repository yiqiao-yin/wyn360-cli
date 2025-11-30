#!/usr/bin/env python3
"""Unit tests for Google Gemini API provider file reading capabilities."""

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


class TestGeminiFileReading:
    """Test file reading tools with Google Gemini API provider."""

    @pytest.fixture(scope="class")
    def setup_gemini_client(self):
        """Setup Gemini client for testing - matches user documentation."""
        # Configure environment exactly as documented for users:
        # export CHOOSE_CLIENT=3
        # export GEMINI_API_KEY=your_key_here  # find in .env file
        # export GEMINI_MODEL=gemini-2.5-flash

        # Set hardcoded values as documented
        os.environ['CHOOSE_CLIENT'] = '3'  # Google Gemini
        os.environ['GEMINI_MODEL'] = 'gemini-2.5-flash'

        # Get API key from .env file (already loaded via load_dotenv)
        gemini_key = os.getenv('GEMINI_API_KEY')
        if not gemini_key:
            pytest.skip("GEMINI_API_KEY not found in .env file")

        # Set API key from .env
        os.environ['GEMINI_API_KEY'] = gemini_key

        return gemini_key

    @pytest.fixture
    def fresh_agent(self, setup_gemini_client):
        """Create a fresh agent instance for each test to avoid event loop issues."""
        def _create_agent():
            return WYN360Agent()
        return _create_agent

    @pytest.fixture(autouse=True)
    def cleanup_after_test(self):
        """Cleanup after each test to prevent event loop issues."""
        yield
        # Cleanup logic - let garbage collection handle cleanup
        import gc
        gc.collect()

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
    async def test_gemini_pdf_reading(self, fresh_agent, test_files_paths):
        """Test Gemini API can read PDF files through read_pdf tool."""
        print("🔄 Testing Gemini API PDF reading...")

        try:
            # Create fresh agent to avoid event loop issues
            agent = fresh_agent()
            print(f"✅ Agent created: {agent.model_name}")
            assert "gemini" in agent.model_name.lower()

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
            print("✅ Gemini PDF reading successful!")

        except Exception as e:
            print(f"❌ Gemini PDF Error: {e}")
            pytest.fail(f"Gemini PDF reading failed: {e}")

    @pytest.mark.asyncio
    async def test_gemini_excel_reading(self, fresh_agent, test_files_paths):
        """Test Gemini API can read Excel files through read_excel tool."""
        print("🔄 Testing Gemini API Excel reading...")

        try:
            # Create fresh agent to avoid event loop issues
            agent = fresh_agent()
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
            print("✅ Gemini Excel reading successful!")

        except Exception as e:
            print(f"❌ Gemini Excel Error: {e}")
            pytest.fail(f"Gemini Excel reading failed: {e}")

    @pytest.mark.asyncio
    async def test_gemini_word_reading(self, fresh_agent, test_files_paths):
        """Test Gemini API can read Word documents through read_word tool."""
        print("🔄 Testing Gemini API Word reading...")

        try:
            # Create fresh agent to avoid event loop issues
            agent = fresh_agent()
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
            print("✅ Gemini Word reading successful!")

        except Exception as e:
            print(f"❌ Gemini Word Error: {e}")
            pytest.fail(f"Gemini Word reading failed: {e}")

    @pytest.mark.asyncio
    async def test_gemini_file_type_detection(self, fresh_agent, test_files_paths):
        """Test Gemini API can detect and handle different file types appropriately."""
        print("🔄 Testing Gemini API file type detection...")

        try:
            # Create fresh agent to avoid event loop issues
            agent = fresh_agent()
            print(f"✅ Agent created: {agent.model_name}")

            # Test with ambiguous request that should trigger appropriate tool
            pdf_path = test_files_paths['pdf']

            response = await agent.agent.run(
                f"I need you to analyze this document: {pdf_path}. "
                f"Can you tell me what type of file it is and what it contains?"
            )

            # Verify response
            response_text = getattr(response, 'output', '') or getattr(response, 'data', '')
            assert len(response_text) > 50, "Response too short"

            # Should mention PDF or document type
            response_lower = response_text.lower()
            assert any(word in response_lower for word in ['pdf', 'document', 'file']), \
                "Response should identify file type"

            print(f"🔍 File detection response preview: {response_text[:200]}...")
            print("✅ Gemini file type detection successful!")

        except Exception as e:
            print(f"❌ Gemini File Detection Error: {e}")
            pytest.fail(f"Gemini file detection failed: {e}")

    @pytest.mark.asyncio
    async def test_gemini_cross_file_analysis(self, fresh_agent, test_files_paths):
        """Test Gemini API can analyze and compare content across different file types."""
        print("🔄 Testing Gemini API cross-file analysis...")

        try:
            # Create fresh agent to avoid event loop issues
            agent = fresh_agent()
            print(f"✅ Agent created: {agent.model_name}")

            # Test analysis across file types
            pdf_path = test_files_paths['pdf']
            xlsx_path = test_files_paths['xlsx']

            response = await agent.agent.run(
                f"Please analyze these two files and compare their content types:\n"
                f"1. {pdf_path}\n"
                f"2. {xlsx_path}\n"
                f"What kind of information does each contain and how do they differ?"
            )

            # Verify response mentions both files
            response_text = getattr(response, 'output', '') or getattr(response, 'data', '')
            assert len(response_text) > 100, "Response too short for cross-file analysis"

            # Should mention different aspects of the files
            response_lower = response_text.lower()
            file_indicators = ['pdf', 'excel', 'spreadsheet', 'document', 'data', 'text']
            mentioned_indicators = [word for word in file_indicators if word in response_lower]
            assert len(mentioned_indicators) >= 2, \
                f"Response should mention multiple file aspects, found: {mentioned_indicators}"

            print(f"🔄 Cross-file analysis preview: {response_text[:200]}...")
            print("✅ Gemini cross-file analysis successful!")

        except Exception as e:
            print(f"❌ Gemini Cross-File Analysis Error: {e}")
            pytest.fail(f"Gemini cross-file analysis failed: {e}")


if __name__ == "__main__":
    # Run tests directly
    import pytest
    pytest.main([__file__, "-v", "-s"])