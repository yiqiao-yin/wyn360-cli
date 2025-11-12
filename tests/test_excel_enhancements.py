"""
Integration tests for Excel enhancements (Phase 5.4.1-5.4.3)

Tests cover:
- Chart extraction from Excel sheets
- Named ranges extraction from workbook
- Formula tracking in cells
- Integration with existing ExcelReader workflow
- Edge cases and error handling
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import sys

# Mock openpyxl
sys.modules['openpyxl'] = MagicMock()
sys.modules['openpyxl.chart'] = MagicMock()

from wyn360_cli.document_readers import ExcelReader


def create_mock_sheet(title="Sheet1", cells_data=None):
    """Helper to create a properly mocked Excel sheet."""
    mock_sheet = MagicMock()
    mock_sheet.title = title

    # Default cells data if not provided
    if cells_data is None:
        cells_data = [[Mock(value="Data", row=1, column=1)]]

    mock_sheet.iter_rows.return_value = cells_data

    # Mock cell access
    def mock_cell(row, column):
        cell = Mock()
        cell.value = "Data"
        return cell
    mock_sheet.cell = mock_cell
    mock_sheet.merged_cells.ranges = []

    return mock_sheet


class TestExcelChartExtraction:
    """Test chart extraction functionality."""

    def test_reader_initialization_with_chart_extraction(self):
        """Test reader initializes with chart extraction enabled."""
        with tempfile.NamedTemporaryFile(suffix=".xlsx") as tmpfile:
            reader = ExcelReader(
                file_path=tmpfile.name,
                extract_charts=True
            )

            assert reader.extract_charts is True

    def test_reader_initialization_charts_disabled(self):
        """Test reader with chart extraction disabled (default)."""
        with tempfile.NamedTemporaryFile(suffix=".xlsx") as tmpfile:
            reader = ExcelReader(file_path=tmpfile.name)

            assert reader.extract_charts is False

    @patch('wyn360_cli.document_readers.HAS_OPENPYXL', True)
    @patch('wyn360_cli.document_readers.openpyxl')
    def test_extract_charts_from_sheet(self, mock_openpyxl):
        """Test extracting charts from Excel sheet."""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmpfile:
            tmpfile_path = tmpfile.name

        try:
            # Mock workbook and sheet with charts
            mock_wb = MagicMock()
            mock_sheet = MagicMock()
            mock_sheet.title = "Sheet1"

            # Mock iter_rows with proper cell objects
            mock_cell1 = Mock(value="Data", row=1, column=1)
            mock_cell2 = Mock(value="Data2", row=1, column=2)
            mock_sheet.iter_rows.return_value = [[mock_cell1, mock_cell2]]

            # Mock cell access
            def mock_cell(row, column):
                cell = Mock()
                cell.value = "Data"
                return cell
            mock_sheet.cell = mock_cell
            mock_sheet.merged_cells.ranges = []

            # Mock chart objects
            mock_chart1 = MagicMock()
            mock_chart1.__class__.__name__ = "BarChart"
            mock_chart1.title = "Sales Chart"
            mock_chart1.anchor = "E2"
            mock_chart1.series = [Mock(), Mock()]  # 2 series

            mock_chart2 = MagicMock()
            mock_chart2.__class__.__name__ = "LineChart"
            mock_chart2.title = "Trend Chart"
            mock_chart2.anchor = "E15"
            mock_chart2.series = [Mock()]  # 1 series

            mock_sheet._charts = [mock_chart1, mock_chart2]

            mock_wb.sheetnames = ["Sheet1"]
            mock_wb.__getitem__.return_value = mock_sheet
            mock_openpyxl.load_workbook.return_value = mock_wb

            # Read with chart extraction enabled
            reader = ExcelReader(file_path=tmpfile_path, extract_charts=True)
            result = reader.read()

            # Verify charts were extracted
            assert len(result["sheets"]) == 1
            assert "charts" in result["sheets"][0]
            assert result["sheets"][0]["chart_count"] == 2

            charts = result["sheets"][0]["charts"]
            assert charts[0]["type"] == "BarChart"
            assert charts[0]["title"] == "Sales Chart"
            assert charts[0]["series_count"] == 2

            assert charts[1]["type"] == "LineChart"
            assert charts[1]["title"] == "Trend Chart"
            assert charts[1]["series_count"] == 1

        finally:
            Path(tmpfile_path).unlink()

    @patch('wyn360_cli.document_readers.HAS_OPENPYXL', True)
    @patch('wyn360_cli.document_readers.openpyxl')
    def test_sheet_without_charts(self, mock_openpyxl):
        """Test sheet with no charts."""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmpfile:
            tmpfile_path = tmpfile.name

        try:
            mock_wb = MagicMock()
            mock_sheet = create_mock_sheet("Sheet1")
            mock_sheet._charts = []  # No charts

            mock_wb.sheetnames = ["Sheet1"]
            mock_wb.__getitem__.return_value = mock_sheet
            mock_openpyxl.load_workbook.return_value = mock_wb

            reader = ExcelReader(file_path=tmpfile_path, extract_charts=True)
            result = reader.read()

            # Should not have charts key if no charts
            assert "charts" not in result["sheets"][0] or len(result["sheets"][0]["charts"]) == 0

        finally:
            Path(tmpfile_path).unlink()

    @patch('wyn360_cli.document_readers.HAS_OPENPYXL', True)
    @patch('wyn360_cli.document_readers.openpyxl')
    def test_chart_extraction_disabled(self, mock_openpyxl):
        """Test that charts are not extracted when disabled."""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmpfile:
            tmpfile_path = tmpfile.name

        try:
            mock_wb = MagicMock()
            mock_sheet = create_mock_sheet("Sheet1")

            # Has charts but extraction disabled
            mock_chart = MagicMock()
            mock_sheet._charts = [mock_chart]

            mock_wb.sheetnames = ["Sheet1"]
            mock_wb.__getitem__.return_value = mock_sheet
            mock_openpyxl.load_workbook.return_value = mock_wb

            # Read with chart extraction DISABLED
            reader = ExcelReader(file_path=tmpfile_path, extract_charts=False)
            result = reader.read()

            # Should not have charts in result
            assert "charts" not in result["sheets"][0]

        finally:
            Path(tmpfile_path).unlink()


class TestExcelNamedRanges:
    """Test named ranges extraction functionality."""

    def test_reader_initialization_with_named_ranges(self):
        """Test reader initializes with named ranges enabled."""
        with tempfile.NamedTemporaryFile(suffix=".xlsx") as tmpfile:
            reader = ExcelReader(
                file_path=tmpfile.name,
                extract_named_ranges=True
            )

            assert reader.extract_named_ranges is True

    @patch('wyn360_cli.document_readers.HAS_OPENPYXL', True)
    @patch('wyn360_cli.document_readers.openpyxl')
    def test_extract_named_ranges(self, mock_openpyxl):
        """Test extracting named ranges from workbook."""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmpfile:
            tmpfile_path = tmpfile.name

        try:
            mock_wb = MagicMock()
            mock_sheet = MagicMock()
            mock_sheet.title = "Sheet1"
            mock_sheet.max_row = 10
            mock_sheet.max_column = 5
            mock_sheet.iter_rows.return_value = []

            # Mock named ranges
            mock_range1 = MagicMock()
            mock_range1.attr_text = "Sheet1!$A$1:$A$10"
            mock_range2 = MagicMock()
            mock_range2.attr_text = "Sheet1!$B$1:$B$10"

            mock_wb.defined_names = {
                "SalesData": mock_range1,
                "Prices": mock_range2
            }
            mock_wb.sheetnames = ["Sheet1"]
            mock_wb.__getitem__.return_value = mock_sheet
            mock_openpyxl.load_workbook.return_value = mock_wb

            # Read with named ranges extraction
            reader = ExcelReader(file_path=tmpfile_path, extract_named_ranges=True)
            result = reader.read()

            # Verify named ranges were extracted
            assert "named_ranges" in result
            assert len(result["named_ranges"]) == 2

            assert "SalesData" in result["named_ranges"]
            assert result["named_ranges"]["SalesData"]["refers_to"] == "Sheet1!$A$1:$A$10"
            assert result["named_ranges"]["SalesData"]["scope"] == "workbook"

            assert "Prices" in result["named_ranges"]
            assert result["named_ranges"]["Prices"]["refers_to"] == "Sheet1!$B$1:$B$10"

        finally:
            Path(tmpfile_path).unlink()

    @patch('wyn360_cli.document_readers.HAS_OPENPYXL', True)
    @patch('wyn360_cli.document_readers.openpyxl')
    def test_workbook_without_named_ranges(self, mock_openpyxl):
        """Test workbook with no named ranges."""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmpfile:
            tmpfile_path = tmpfile.name

        try:
            mock_wb = MagicMock()
            mock_sheet = MagicMock()
            mock_sheet.title = "Sheet1"
            mock_sheet.max_row = 10
            mock_sheet.max_column = 5
            mock_sheet.iter_rows.return_value = []

            mock_wb.defined_names = {}  # No named ranges
            mock_wb.sheetnames = ["Sheet1"]
            mock_wb.__getitem__.return_value = mock_sheet
            mock_openpyxl.load_workbook.return_value = mock_wb

            reader = ExcelReader(file_path=tmpfile_path, extract_named_ranges=True)
            result = reader.read()

            # Should not have named_ranges key if none exist
            assert "named_ranges" not in result or len(result["named_ranges"]) == 0

        finally:
            Path(tmpfile_path).unlink()

    @patch('wyn360_cli.document_readers.HAS_OPENPYXL', True)
    @patch('wyn360_cli.document_readers.openpyxl')
    def test_named_ranges_disabled(self, mock_openpyxl):
        """Test that named ranges are not extracted when disabled."""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmpfile:
            tmpfile_path = tmpfile.name

        try:
            mock_wb = MagicMock()
            mock_sheet = MagicMock()
            mock_sheet.title = "Sheet1"
            mock_sheet.max_row = 10
            mock_sheet.max_column = 5
            mock_sheet.iter_rows.return_value = []

            # Has named ranges but extraction disabled
            mock_range = MagicMock()
            mock_range.attr_text = "Sheet1!$A$1"
            mock_wb.defined_names = {"TestRange": mock_range}
            mock_wb.sheetnames = ["Sheet1"]
            mock_wb.__getitem__.return_value = mock_sheet
            mock_openpyxl.load_workbook.return_value = mock_wb

            # Read with named ranges extraction DISABLED
            reader = ExcelReader(file_path=tmpfile_path, extract_named_ranges=False)
            result = reader.read()

            # Should not have named_ranges in result
            assert "named_ranges" not in result

        finally:
            Path(tmpfile_path).unlink()


class TestExcelFormulaTracking:
    """Test formula tracking functionality."""

    def test_reader_initialization_with_formula_tracking(self):
        """Test reader initializes with formula tracking enabled."""
        with tempfile.NamedTemporaryFile(suffix=".xlsx") as tmpfile:
            reader = ExcelReader(
                file_path=tmpfile.name,
                track_formulas=True
            )

            assert reader.track_formulas is True

    @patch('wyn360_cli.document_readers.HAS_OPENPYXL', True)
    @patch('wyn360_cli.document_readers.openpyxl')
    def test_track_formulas_in_sheet(self, mock_openpyxl):
        """Test tracking formulas in Excel sheet."""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmpfile:
            tmpfile_path = tmpfile.name

        try:
            mock_wb = MagicMock()

            # Mock cells with formulas
            mock_cell1 = Mock(value="=SUM(B1:B10)", row=1, column=1, coordinate="A1")
            mock_cell2 = Mock(value="Regular text", row=1, column=2, coordinate="A2")
            mock_cell3 = Mock(value="=A1*2", row=2, column=1, coordinate="B1")

            cells_data = [
                [mock_cell1, mock_cell2],
                [mock_cell3]
            ]

            mock_sheet = create_mock_sheet("Sheet1", cells_data)

            mock_wb.sheetnames = ["Sheet1"]
            mock_wb.__getitem__.return_value = mock_sheet
            mock_openpyxl.load_workbook.return_value = mock_wb

            # Read with formula tracking enabled
            reader = ExcelReader(file_path=tmpfile_path, track_formulas=True)
            result = reader.read()

            # Verify formulas were tracked
            assert len(result["sheets"]) == 1
            assert "formulas" in result["sheets"][0]
            assert result["sheets"][0]["formula_count"] == 2

            formulas = result["sheets"][0]["formulas"]
            assert formulas[0]["cell"] == "A1"
            assert formulas[0]["formula"] == "=SUM(B1:B10)"
            assert formulas[0]["sheet"] == "Sheet1"

            assert formulas[1]["cell"] == "B1"
            assert formulas[1]["formula"] == "=A1*2"

        finally:
            Path(tmpfile_path).unlink()

    @patch('wyn360_cli.document_readers.HAS_OPENPYXL', True)
    @patch('wyn360_cli.document_readers.openpyxl')
    def test_sheet_without_formulas(self, mock_openpyxl):
        """Test sheet with no formulas."""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmpfile:
            tmpfile_path = tmpfile.name

        try:
            mock_wb = MagicMock()

            # Mock cells without formulas
            mock_cell1 = Mock(value="Text", row=1, column=1)
            mock_cell2 = Mock(value=123, row=1, column=2)

            cells_data = [[mock_cell1, mock_cell2]]
            mock_sheet = create_mock_sheet("Sheet1", cells_data)

            mock_wb.sheetnames = ["Sheet1"]
            mock_wb.__getitem__.return_value = mock_sheet
            mock_openpyxl.load_workbook.return_value = mock_wb

            reader = ExcelReader(file_path=tmpfile_path, track_formulas=True)
            result = reader.read()

            # Should not have formulas key if no formulas
            assert "formulas" not in result["sheets"][0] or len(result["sheets"][0]["formulas"]) == 0

        finally:
            Path(tmpfile_path).unlink()

    @patch('wyn360_cli.document_readers.HAS_OPENPYXL', True)
    @patch('wyn360_cli.document_readers.openpyxl')
    def test_formula_tracking_disabled(self, mock_openpyxl):
        """Test that formulas are not tracked when disabled."""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmpfile:
            tmpfile_path = tmpfile.name

        try:
            mock_wb = MagicMock()
            mock_sheet = MagicMock()
            mock_sheet.title = "Sheet1"
            mock_sheet.max_row = 1
            mock_sheet.max_column = 1

            # Has formulas but tracking disabled
            mock_cell = MagicMock()
            mock_cell.value = "=SUM(A1:A10)"
            mock_sheet.iter_rows.return_value = [[mock_cell]]

            mock_wb.sheetnames = ["Sheet1"]
            mock_wb.__getitem__.return_value = mock_sheet
            mock_openpyxl.load_workbook.return_value = mock_wb

            # Read with formula tracking DISABLED
            reader = ExcelReader(file_path=tmpfile_path, track_formulas=False)
            result = reader.read()

            # Should not have formulas in result
            assert "formulas" not in result["sheets"][0]

        finally:
            Path(tmpfile_path).unlink()


class TestExcelEnhancementsIntegration:
    """Test integration of all enhancements together."""

    @patch('wyn360_cli.document_readers.HAS_OPENPYXL', True)
    @patch('wyn360_cli.document_readers.openpyxl')
    def test_all_enhancements_enabled(self, mock_openpyxl):
        """Test all enhancements working together."""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmpfile:
            tmpfile_path = tmpfile.name

        try:
            mock_wb = MagicMock()
            mock_sheet = MagicMock()
            mock_sheet.title = "Dashboard"
            mock_sheet.max_row = 5
            mock_sheet.max_column = 3

            # Mock chart
            mock_chart = MagicMock()
            mock_chart.__class__.__name__ = "PieChart"
            mock_chart.title = "Revenue"
            mock_chart.anchor = "D2"
            mock_chart.series = [Mock()]
            mock_sheet._charts = [mock_chart]

            # Mock formula cell
            mock_cell = MagicMock()
            mock_cell.coordinate = "C5"
            mock_cell.value = "=SUM(A1:A4)"
            mock_sheet.iter_rows.return_value = [[mock_cell]]

            # Mock named range
            mock_range = MagicMock()
            mock_range.attr_text = "Dashboard!$A$1:$A$4"
            mock_wb.defined_names = {"Revenue": mock_range}

            mock_wb.sheetnames = ["Dashboard"]
            mock_wb.__getitem__.return_value = mock_sheet
            mock_openpyxl.load_workbook.return_value = mock_wb

            # Read with ALL enhancements enabled
            reader = ExcelReader(
                file_path=tmpfile_path,
                extract_charts=True,
                extract_named_ranges=True,
                track_formulas=True
            )
            result = reader.read()

            # Verify all enhancements present
            assert "charts" in result["sheets"][0]
            assert result["sheets"][0]["chart_count"] == 1
            assert "formulas" in result["sheets"][0]
            assert result["sheets"][0]["formula_count"] == 1
            assert "named_ranges" in result
            assert len(result["named_ranges"]) == 1

        finally:
            Path(tmpfile_path).unlink()

    @patch('wyn360_cli.document_readers.HAS_OPENPYXL', True)
    @patch('wyn360_cli.document_readers.openpyxl')
    def test_all_enhancements_disabled(self, mock_openpyxl):
        """Test all enhancements disabled (backward compatibility)."""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmpfile:
            tmpfile_path = tmpfile.name

        try:
            mock_wb = MagicMock()
            mock_sheet = create_mock_sheet("Sheet1")

            mock_wb.sheetnames = ["Sheet1"]
            mock_wb.__getitem__.return_value = mock_sheet
            mock_openpyxl.load_workbook.return_value = mock_wb

            # Read with ALL enhancements disabled
            reader = ExcelReader(
                file_path=tmpfile_path,
                extract_charts=False,
                extract_named_ranges=False,
                track_formulas=False
            )
            result = reader.read()

            # Verify no enhancement data in result
            assert "charts" not in result["sheets"][0]
            assert "formulas" not in result["sheets"][0]
            assert "named_ranges" not in result

        finally:
            Path(tmpfile_path).unlink()


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
