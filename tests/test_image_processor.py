"""
Unit tests for ImageProcessor class (Phase 5.1.4)

Tests cover:
- Image format detection
- Image type detection (chart, diagram, photo, etc.)
- Vision API integration
- Batch processing
- Context-aware prompts
- Error handling
- Markdown formatting
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from wyn360_cli.document_readers import ImageProcessor, HAS_PIL


class TestImageProcessor:
    """Test ImageProcessor functionality."""

    def test_processor_initialization(self):
        """Test processor initializes with correct parameters."""
        processor = ImageProcessor(api_key="test-key", model="claude-sonnet-4-20250514")

        assert processor.api_key == "test-key"
        assert processor.model == "claude-sonnet-4-20250514"

    def test_processor_initialization_default_model(self):
        """Test processor initializes with default model."""
        processor = ImageProcessor(api_key="test-key")

        assert processor.model == "claude-3-5-sonnet-20241022"

    def test_detect_image_format_png(self):
        """Test PNG format detection."""
        processor = ImageProcessor(api_key="test-key")

        # PNG magic bytes
        png_data = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100

        format_detected = processor._detect_image_format(png_data)
        assert format_detected == "png"

    def test_detect_image_format_jpeg(self):
        """Test JPEG format detection."""
        processor = ImageProcessor(api_key="test-key")

        # JPEG magic bytes
        jpeg_data = b'\xff\xd8\xff' + b'\x00' * 100

        format_detected = processor._detect_image_format(jpeg_data)
        assert format_detected == "jpeg"

    def test_detect_image_format_gif(self):
        """Test GIF format detection."""
        processor = ImageProcessor(api_key="test-key")

        # GIF magic bytes
        gif_data = b'GIF89a' + b'\x00' * 100

        format_detected = processor._detect_image_format(gif_data)
        assert format_detected == "gif"

    def test_detect_image_format_webp(self):
        """Test WebP format detection."""
        processor = ImageProcessor(api_key="test-key")

        # WebP magic bytes (RIFF....WEBP)
        webp_data = b'RIFF' + b'\x00\x00\x00\x00' + b'WEBP' + b'\x00' * 100

        format_detected = processor._detect_image_format(webp_data)
        assert format_detected == "webp"

    def test_detect_image_format_unknown(self):
        """Test unknown format detection."""
        processor = ImageProcessor(api_key="test-key")

        # Unknown format
        unknown_data = b'\x00\x00\x00\x00' + b'\x00' * 100

        format_detected = processor._detect_image_format(unknown_data)
        assert format_detected is None  # Returns None for unknown formats

    def test_detect_image_type_chart(self):
        """Test chart image type detection."""
        processor = ImageProcessor(api_key="test-key")

        # Simulate chart description
        description = "A bar chart showing sales data over time"

        image_type = processor._detect_image_type(description)
        assert image_type == "chart"

    def test_detect_image_type_diagram(self):
        """Test diagram image type detection."""
        processor = ImageProcessor(api_key="test-key")

        # Simulate diagram description (flowchart contains "chart" but should match diagram)
        # Note: Since "flowchart" is in the diagram keywords, it will be checked there
        description = "A diagram showing the system architecture"

        image_type = processor._detect_image_type(description)
        assert image_type == "diagram"

    def test_detect_image_type_screenshot(self):
        """Test screenshot image type detection."""
        processor = ImageProcessor(api_key="test-key")

        # Simulate screenshot description
        description = "A screenshot of the application interface"

        image_type = processor._detect_image_type(description)
        assert image_type == "screenshot"

    def test_detect_image_type_photo(self):
        """Test photo image type detection."""
        processor = ImageProcessor(api_key="test-key")

        # Simulate photo description
        description = "A photo of a sunset over the ocean"

        image_type = processor._detect_image_type(description)
        assert image_type == "photo"

    def test_detect_image_type_default(self):
        """Test default image type detection."""
        processor = ImageProcessor(api_key="test-key")

        # Generic description
        description = "Some visual content"

        image_type = processor._detect_image_type(description)
        assert image_type == "other"

    def test_build_image_prompt_no_context(self):
        """Test building image prompt without context."""
        processor = ImageProcessor(api_key="test-key")

        prompt = processor._build_image_prompt(context=None)

        assert "Describe this image" in prompt
        assert "concise" in prompt

    def test_build_image_prompt_with_context(self):
        """Test building image prompt with context."""
        processor = ImageProcessor(api_key="test-key")

        context = {
            "doc_type": "pdf",
            "page_number": 5,
            "section": "Results"
        }

        prompt = processor._build_image_prompt(context=context)

        assert "page 5" in prompt.lower()
        assert "pdf" in prompt.lower() or "document" in prompt.lower()

    def test_format_image_markdown_chart(self):
        """Test markdown formatting for chart."""
        processor = ImageProcessor(api_key="test-key")

        markdown = processor.format_image_markdown(
            description="A bar chart showing sales over time",
            image_type="chart",
            image_index=1
        )

        assert "📊" in markdown
        assert "[Image 1]" in markdown
        assert "sales over time" in markdown

    def test_format_image_markdown_diagram(self):
        """Test markdown formatting for diagram."""
        processor = ImageProcessor(api_key="test-key")

        markdown = processor.format_image_markdown(
            description="A diagram showing the process",
            image_type="diagram",
            image_index=2
        )

        assert "📐" in markdown
        assert "[Image 2]" in markdown
        assert "diagram" in markdown

    def test_format_image_markdown_with_index(self):
        """Test markdown formatting with image index."""
        processor = ImageProcessor(api_key="test-key")

        markdown = processor.format_image_markdown(
            description="A photo of a sunset",
            image_type="photo",
            image_index=3
        )

        assert "📷" in markdown
        assert "[Image 3]" in markdown
        assert "sunset" in markdown

    @pytest.mark.asyncio
    @patch('wyn360_cli.document_readers.Anthropic')
    async def test_describe_image_success(self, mock_anthropic_class):
        """Test successful image description."""
        # Mock the Anthropic client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock(text="A chart showing quarterly sales data")]
        mock_response.usage = Mock(input_tokens=1150, output_tokens=25)

        mock_client.messages.create = Mock(return_value=mock_response)
        mock_anthropic_class.return_value = mock_client

        processor = ImageProcessor(api_key="test-key")
        processor.client = mock_client

        # Test image data
        image_data = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100

        result = await processor.describe_image(image_data)

        # Verify result
        assert "description" in result
        assert "chart showing quarterly sales" in result["description"].lower()
        assert result["image_type"] == "chart"
        assert result["tokens_used"] == 1175  # input + output

    @pytest.mark.asyncio
    @patch('wyn360_cli.document_readers.Anthropic')
    async def test_describe_image_with_context(self, mock_anthropic_class):
        """Test image description with context."""
        # Mock the Anthropic client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock(text="A diagram of the system architecture")]
        mock_response.usage = Mock(input_tokens=1150, output_tokens=30)

        mock_client.messages.create = Mock(return_value=mock_response)
        mock_anthropic_class.return_value = mock_client

        processor = ImageProcessor(api_key="test-key")
        processor.client = mock_client

        # Test with context
        image_data = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
        context = {"doc_type": "word", "section": "Architecture"}

        result = await processor.describe_image(image_data, context=context)

        # Verify result includes context
        assert "description" in result
        assert result["image_type"] == "diagram"

    @pytest.mark.asyncio
    @patch('wyn360_cli.document_readers.Anthropic')
    async def test_describe_image_handles_error(self, mock_anthropic_class):
        """Test image description error handling."""
        # Mock the Anthropic client to raise an error
        mock_client = Mock()
        mock_client.messages.create = Mock(side_effect=Exception("API Error"))
        mock_anthropic_class.return_value = mock_client

        processor = ImageProcessor(api_key="test-key")
        processor.client = mock_client

        # Test error handling
        image_data = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100

        result = await processor.describe_image(image_data)

        # Should return error result
        assert "error" in result["description"].lower()
        assert result["tokens_used"] == 0

    @pytest.mark.asyncio
    @patch('wyn360_cli.document_readers.Anthropic')
    async def test_describe_images_batch(self, mock_anthropic_class):
        """Test batch image processing."""
        # Mock the Anthropic client
        mock_client = Mock()
        mock_response1 = Mock()
        mock_response1.content = [Mock(text="First image: A chart")]
        mock_response1.usage = Mock(input_tokens=1150, output_tokens=20)

        mock_response2 = Mock()
        mock_response2.content = [Mock(text="Second image: A diagram")]
        mock_response2.usage = Mock(input_tokens=1150, output_tokens=25)

        mock_client.messages.create = Mock(side_effect=[mock_response1, mock_response2])
        mock_anthropic_class.return_value = mock_client

        processor = ImageProcessor(api_key="test-key")
        processor.client = mock_client

        # Test batch processing
        images = [
            {"data": b'\x89PNG\r\n\x1a\n' + b'\x00' * 100, "format": "png", "context": {"index": 0}},
            {"data": b'\x89PNG\r\n\x1a\n' + b'\x00' * 100, "format": "png", "context": {"index": 1}}
        ]

        results = await processor.describe_images_batch(images)

        # Verify results
        assert len(results) == 2
        assert "chart" in results[0]["description"].lower()
        assert "diagram" in results[1]["description"].lower()
        assert results[0]["tokens_used"] == 1170  # input + output
        assert results[1]["tokens_used"] == 1175  # input + output

    @pytest.mark.asyncio
    async def test_describe_images_batch_empty(self):
        """Test batch processing with empty list."""
        processor = ImageProcessor(api_key="test-key")

        results = await processor.describe_images_batch([])

        assert results == []

    def test_format_image_markdown_no_index(self):
        """Test markdown formatting without image index."""
        processor = ImageProcessor(api_key="test-key")

        markdown = processor.format_image_markdown(
            description="Generic image",
            image_type="other",
            image_index=None
        )

        assert "🖼️" in markdown
        assert "[Image]" in markdown  # No number when index is None
        assert "Generic image" in markdown


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
