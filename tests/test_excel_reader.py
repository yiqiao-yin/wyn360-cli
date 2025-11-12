"""
Unit tests for ExcelReader class (Phase 13.2)

Tests cover:
- Excel file reading with openpyxl
- Data region detection (not assuming A1)
- Merged cell handling
- Markdown table conversion
- Sheet chunking (full sheet and partial)
- Error handling (file not found, openpyxl not installed)
- Edge cases (empty sheets, large sheets)
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from wyn360_cli.document_readers import ExcelReader, count_tokens


class TestExcelReader:
    """Test ExcelReader functionality."""

    def test_reader_initialization(self):
        """Test reader initializes with correct parameters."""
        reader = ExcelReader(file_path="test.xlsx", chunk_size=1000)

        assert reader.file_path == Path("test.xlsx")
        assert reader.chunk_size == 1000
        assert reader.include_sheets is None

    def test_reader_initialization_with_sheets(self):
        """Test reader initializes with sheet filter."""
        reader = ExcelReader(
            file_path="test.xlsx",
            chunk_size=500,
            include_sheets=["Sheet1", "Sheet2"]
        )

        assert reader.include_sheets == ["Sheet1", "Sheet2"]
        assert reader.chunk_size == 500

    @patch('wyn360_cli.document_readers.HAS_OPENPYXL', False)
    def test_read_without_openpyxl(self):
        """Test error when openpyxl not installed."""
        with tempfile.NamedTemporaryFile(suffix=".xlsx") as tmpfile:
            reader = ExcelReader(file_path=tmpfile.name)

            with pytest.raises(ImportError) as exc_info:
                reader.read()

            assert "openpyxl not installed" in str(exc_info.value)

    @patch('wyn360_cli.document_readers.HAS_OPENPYXL', True)
    @patch('wyn360_cli.document_readers.openpyxl')
    def test_read_nonexistent_file(self, mock_openpyxl):
        """Test error when file doesn't exist."""
        reader = ExcelReader(file_path="/nonexistent/file.xlsx")

        with pytest.raises(FileNotFoundError):
            reader.read()

    @patch('wyn360_cli.document_readers.openpyxl')
    @patch('wyn360_cli.document_readers.HAS_OPENPYXL', True)
    def test_read_simple_sheet(self, mock_openpyxl):
        """Test reading a simple Excel sheet."""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmpfile:
            tmpfile_path = tmpfile.name

        try:
            # Mock workbook
            mock_workbook = MagicMock()
            mock_sheet = MagicMock()

            # Set up sheet data (2x3 table starting at A1)
            mock_sheet.title = "TestSheet"
            mock_sheet.iter_rows.return_value = [
                [
                    Mock(value="Header1", row=1, column=1),
                    Mock(value="Header2", row=1, column=2),
                ],
                [
                    Mock(value="Data1", row=2, column=1),
                    Mock(value="Data2", row=2, column=2),
                ],
                [
                    Mock(value="Data3", row=3, column=1),
                    Mock(value="Data4", row=3, column=2),
                ]
            ]

            # Mock cell access
            def mock_cell(row, column):
                data = {
                    (1, 1): "Header1", (1, 2): "Header2",
                    (2, 1): "Data1", (2, 2): "Data2",
                    (3, 1): "Data3", (3, 2): "Data4"
                }
                cell = Mock()
                cell.value = data.get((row, column))
                return cell

            mock_sheet.cell = mock_cell
            mock_sheet.merged_cells.ranges = []

            mock_workbook.sheetnames = ["TestSheet"]
            mock_workbook.__getitem__.return_value = mock_sheet
            mock_openpyxl.load_workbook.return_value = mock_workbook

            # Read Excel file
            reader = ExcelReader(file_path=tmpfile_path)
            result = reader.read()

            # Verify results
            assert result["total_sheets"] == 1
            assert len(result["sheets"]) == 1
            assert result["sheets"][0]["name"] == "TestSheet"
            assert result["sheets"][0]["row_count"] == 3
            assert result["sheets"][0]["col_count"] == 2
            assert "Header1" in result["sheets"][0]["markdown"]
            assert "Data1" in result["sheets"][0]["markdown"]

        finally:
            Path(tmpfile_path).unlink()

    @patch('wyn360_cli.document_readers.openpyxl')
    @patch('wyn360_cli.document_readers.HAS_OPENPYXL', True)
    def test_detect_data_region_not_at_a1(self, mock_openpyxl):
        """Test data region detection when data doesn't start at A1."""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmpfile:
            tmpfile_path = tmpfile.name

        try:
            # Mock workbook with data starting at C3
            mock_workbook = MagicMock()
            mock_sheet = MagicMock()

            mock_sheet.title = "DataSheet"
            mock_sheet.iter_rows.return_value = [
                [Mock(value=None, row=1, column=1), Mock(value=None, row=1, column=2), Mock(value=None, row=1, column=3)],
                [Mock(value=None, row=2, column=1), Mock(value=None, row=2, column=2), Mock(value=None, row=2, column=3)],
                [Mock(value=None, row=3, column=1), Mock(value=None, row=3, column=2), Mock(value="Header", row=3, column=3)],
                [Mock(value=None, row=4, column=1), Mock(value=None, row=4, column=2), Mock(value="Data", row=4, column=3)],
            ]

            def mock_cell(row, column):
                if row >= 3 and column >= 3:
                    return Mock(value="Header" if row == 3 else "Data")
                return Mock(value=None)

            mock_sheet.cell = mock_cell
            mock_sheet.merged_cells.ranges = []

            mock_workbook.sheetnames = ["DataSheet"]
            mock_workbook.__getitem__.return_value = mock_sheet
            mock_openpyxl.load_workbook.return_value = mock_workbook

            # Read Excel file
            reader = ExcelReader(file_path=tmpfile_path)
            result = reader.read()

            # Data region should be detected starting at row 3, column 3
            assert result["sheets"][0]["data_region"] == (3, 3, 4, 3)
            assert result["sheets"][0]["row_count"] == 2
            assert result["sheets"][0]["col_count"] == 1

        finally:
            Path(tmpfile_path).unlink()

    @patch('wyn360_cli.document_readers.openpyxl')
    @patch('wyn360_cli.document_readers.HAS_OPENPYXL', True)
    def test_handle_merged_cells(self, mock_openpyxl):
        """Test handling of merged cells."""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmpfile:
            tmpfile_path = tmpfile.name

        try:
            # Mock workbook with merged cell at A1:B1
            mock_workbook = MagicMock()
            mock_sheet = MagicMock()

            mock_sheet.title = "MergedSheet"
            mock_sheet.iter_rows.return_value = [
                [
                    Mock(value="Merged Header", row=1, column=1),
                    Mock(value=None, row=1, column=2),
                ],
                [
                    Mock(value="Data1", row=2, column=1),
                    Mock(value="Data2", row=2, column=2),
                ]
            ]

            def mock_cell(row, column):
                if row == 1 and column == 1:
                    return Mock(value="Merged Header")
                elif row == 1 and column == 2:
                    return Mock(value=None)
                elif row == 2:
                    return Mock(value="Data1" if column == 1 else "Data2")
                return Mock(value=None)

            mock_sheet.cell = mock_cell

            # Mock merged cells
            mock_range = Mock()
            mock_range.min_row = 1
            mock_range.min_col = 1
            mock_range.max_row = 1
            mock_range.max_col = 2
            mock_sheet.merged_cells.ranges = [mock_range]

            mock_workbook.sheetnames = ["MergedSheet"]
            mock_workbook.__getitem__.return_value = mock_sheet
            mock_openpyxl.load_workbook.return_value = mock_workbook

            # Read Excel file
            reader = ExcelReader(file_path=tmpfile_path)
            result = reader.read()

            # Verify merged cell is handled (value shown once, other cells empty)
            assert result["sheets"][0]["name"] == "MergedSheet"
            assert result["sheets"][0]["has_merged_cells"] is True
            markdown = result["sheets"][0]["markdown"]
            assert "Merged Header" in markdown

        finally:
            Path(tmpfile_path).unlink()

    @patch('wyn360_cli.document_readers.openpyxl')
    @patch('wyn360_cli.document_readers.HAS_OPENPYXL', True)
    def test_empty_sheet(self, mock_openpyxl):
        """Test handling of empty sheet."""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmpfile:
            tmpfile_path = tmpfile.name

        try:
            # Mock workbook with empty sheet
            mock_workbook = MagicMock()
            mock_sheet = MagicMock()

            mock_sheet.title = "EmptySheet"
            mock_sheet.iter_rows.return_value = [
                [Mock(value=None, row=1, column=1), Mock(value=None, row=1, column=2)]
            ]

            mock_workbook.sheetnames = ["EmptySheet"]
            mock_workbook.__getitem__.return_value = mock_sheet
            mock_openpyxl.load_workbook.return_value = mock_workbook

            # Read Excel file
            reader = ExcelReader(file_path=tmpfile_path)
            result = reader.read()

            # Empty sheet should be skipped
            assert result["total_sheets"] == 0
            assert len(result["sheets"]) == 0

        finally:
            Path(tmpfile_path).unlink()

    @patch('wyn360_cli.document_readers.openpyxl')
    @patch('wyn360_cli.document_readers.HAS_OPENPYXL', True)
    def test_include_sheets_filter(self, mock_openpyxl):
        """Test include_sheets filter."""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmpfile:
            tmpfile_path = tmpfile.name

        try:
            # Mock workbook with multiple sheets
            mock_workbook = MagicMock()

            # Create sheets
            sheet1 = MagicMock()
            sheet1.title = "Sheet1"
            sheet1.iter_rows.return_value = [[Mock(value="Data1", row=1, column=1)]]
            sheet1.cell.return_value = Mock(value="Data1")
            sheet1.merged_cells.ranges = []

            sheet2 = MagicMock()
            sheet2.title = "Sheet2"
            sheet2.iter_rows.return_value = [[Mock(value="Data2", row=1, column=1)]]
            sheet2.cell.return_value = Mock(value="Data2")
            sheet2.merged_cells.ranges = []

            sheet3 = MagicMock()
            sheet3.title = "Sheet3"
            sheet3.iter_rows.return_value = [[Mock(value="Data3", row=1, column=1)]]
            sheet3.cell.return_value = Mock(value="Data3")
            sheet3.merged_cells.ranges = []

            mock_workbook.sheetnames = ["Sheet1", "Sheet2", "Sheet3"]
            mock_workbook.__getitem__.side_effect = lambda name: {
                "Sheet1": sheet1, "Sheet2": sheet2, "Sheet3": sheet3
            }[name]
            mock_openpyxl.load_workbook.return_value = mock_workbook

            # Read Excel file with filter
            reader = ExcelReader(
                file_path=tmpfile_path,
                include_sheets=["Sheet1", "Sheet3"]
            )
            result = reader.read()

            # Only Sheet1 and Sheet3 should be included
            assert result["total_sheets"] == 2
            sheet_names = [s["name"] for s in result["sheets"]]
            assert "Sheet1" in sheet_names
            assert "Sheet3" in sheet_names
            assert "Sheet2" not in sheet_names

        finally:
            Path(tmpfile_path).unlink()

    def test_chunk_sheets_single_small_sheet(self):
        """Test chunking a single small sheet."""
        reader = ExcelReader(file_path="test.xlsx", chunk_size=1000)

        sheets_data = [
            {
                "name": "Sheet1",
                "markdown": "## Sheet: Sheet1\n\n| A | B |\n| --- | --- |\n| 1 | 2 |",
                "tokens": 50
            }
        ]

        chunks = reader.chunk_sheets(sheets_data)

        # Single small sheet should be one chunk
        assert len(chunks) == 1
        assert chunks[0]["sheet_name"] == "Sheet1"
        assert chunks[0]["tokens"] == 50
        assert chunks[0]["position"]["chunk_type"] == "full_sheet"

    def test_chunk_sheets_multiple_small_sheets(self):
        """Test chunking multiple small sheets."""
        reader = ExcelReader(file_path="test.xlsx", chunk_size=1000)

        sheets_data = [
            {"name": "Sheet1", "markdown": "Data1" * 20, "tokens": 100},
            {"name": "Sheet2", "markdown": "Data2" * 20, "tokens": 100},
            {"name": "Sheet3", "markdown": "Data3" * 20, "tokens": 100}
        ]

        chunks = reader.chunk_sheets(sheets_data)

        # Each sheet should be its own chunk
        assert len(chunks) == 3
        assert all(c["position"]["chunk_type"] == "full_sheet" for c in chunks)

    def test_chunk_sheets_large_sheet(self):
        """Test chunking a large sheet that exceeds chunk_size."""
        reader = ExcelReader(file_path="test.xlsx", chunk_size=200)

        # Create large sheet with table structure
        markdown = "## Sheet: LargeSheet\n\nData Region: Rows 1-100\n\n"
        markdown += "| A | B |\n| --- | --- |\n"
        # Add 100 rows (each row ~10 tokens = 1000 tokens total)
        for i in range(100):
            markdown += f"| Data{i} | Value{i} |\n"

        sheets_data = [
            {
                "name": "LargeSheet",
                "markdown": markdown,
                "tokens": count_tokens(markdown)
            }
        ]

        chunks = reader.chunk_sheets(sheets_data)

        # Large sheet should be split into multiple chunks
        assert len(chunks) > 1
        assert all(c["sheet_name"] == "LargeSheet" for c in chunks)
        # At least one chunk should be marked as partial
        assert any(c["position"]["chunk_type"] == "partial" for c in chunks)

    def test_markdown_table_formatting(self):
        """Test markdown table formatting."""
        reader = ExcelReader(file_path="test.xlsx")

        # Test with mock sheet
        mock_sheet = Mock()
        mock_sheet.title = "TestSheet"

        data_region = (1, 1, 3, 2)  # 3 rows, 2 cols
        merged_cells = {}

        # Mock cell values
        def mock_cell(row, column):
            values = {
                (1, 1): "Header1", (1, 2): "Header2",
                (2, 1): "Data1", (2, 2): "Data2",
                (3, 1): "Data3", (3, 2): "Data4"
            }
            cell = Mock()
            cell.value = values.get((row, column))
            return cell

        mock_sheet.cell = mock_cell

        markdown = reader._sheet_to_markdown(mock_sheet, data_region, merged_cells)

        # Verify markdown structure
        assert "## Sheet: TestSheet" in markdown
        assert "| Header1 | Header2 |" in markdown
        assert "| --- | --- |" in markdown
        assert "| Data1 | Data2 |" in markdown
        assert "| Data3 | Data4 |" in markdown

    def test_escape_pipe_characters(self):
        """Test that pipe characters in cells are escaped."""
        reader = ExcelReader(file_path="test.xlsx")

        mock_sheet = Mock()
        mock_sheet.title = "TestSheet"

        data_region = (1, 1, 1, 1)
        merged_cells = {}

        # Mock cell with pipe character
        def mock_cell(row, column):
            cell = Mock()
            cell.value = "Value|With|Pipes"
            return cell

        mock_sheet.cell = mock_cell

        markdown = reader._sheet_to_markdown(mock_sheet, data_region, merged_cells)

        # Pipe should be escaped
        assert "Value\\|With\\|Pipes" in markdown


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
