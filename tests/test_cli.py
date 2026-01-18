"""Tests for CLI functionality."""

import json
import sys
from unittest import mock

import pytest
from pymarc import Field, Record, Subfield

from marc_lint.cli import main


def _create_valid_record(extra_fields: list[Field] | None = None) -> Record:
    """Create a properly formed MARC record for CLI testing."""
    record = Record()
    record.leader = "00000nam a2200000 i 4500"
    record.add_field(Field(tag="001", data="test001"))
    record.add_field(Field(tag="008", data="240101s2024    xxu           000 0 eng d"))
    record.add_field(
        Field(
            tag="245", indicators=["1", "0"], subfields=[Subfield("a", "Test title.")]
        )
    )
    if extra_fields:
        for f in extra_fields:
            record.add_field(f)
    return record


@pytest.fixture
def mock_marc_file(tmp_path):
    """Create a temporary MARC file for testing."""
    marc_file = tmp_path / "test.mrc"

    # Create a valid MARC record with proper leader and control fields
    record = _create_valid_record()

    with open(marc_file, "wb") as f:
        f.write(record.as_marc())

    return marc_file


@pytest.fixture
def mock_marc_file_with_warnings(tmp_path):
    """Create a temporary MARC file with validation warnings."""
    marc_file = tmp_path / "test_warnings.mrc"

    # Create a record with an invalid ISBN
    record = _create_valid_record(
        [
            Field(
                tag="020",
                indicators=[" ", " "],
                subfields=[Subfield("a", "invalid-isbn")],
            )
        ]
    )

    with open(marc_file, "wb") as f:
        f.write(record.as_marc())

    return marc_file


def test_main_no_arguments(capsys):
    """Test CLI with no arguments shows usage."""
    with mock.patch.object(sys, "argv", ["marc-lint"]):
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Usage: marc-lint" in captured.out
        assert "Lint MARC21 records" in captured.out


def test_main_help_option(capsys):
    """Test CLI with --help shows usage and exits 0."""
    with mock.patch.object(sys, "argv", ["marc-lint", "--help"]):
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Usage: marc-lint" in captured.out
        assert "--format" in captured.out
        assert "--quiet" in captured.out


def test_main_file_not_found(capsys):
    """Test CLI with non-existent file."""
    with mock.patch.object(sys, "argv", ["marc-lint", "nonexistent.mrc"]):
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 2
        captured = capsys.readouterr()
        assert "Error: File 'nonexistent.mrc' not found" in captured.err


def test_main_valid_file_no_warnings(capsys, mock_marc_file):
    """Test CLI with valid MARC file and no warnings."""
    with mock.patch.object(sys, "argv", ["marc-lint", str(mock_marc_file)]):
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Processed 1 record(s)" in captured.out
        assert "Found 0 warning(s)" in captured.out
        assert "✓ No validation warnings found!" in captured.out


def test_main_file_with_warnings(capsys, mock_marc_file_with_warnings):
    """Test CLI with MARC file containing warnings."""
    with mock.patch.object(
        sys, "argv", ["marc-lint", str(mock_marc_file_with_warnings)]
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "--- Record test001 ---" in captured.out
        assert "020:" in captured.out  # Just check for ISBN-related warning
        assert "Processed 1 record(s)" in captured.out
        assert "Found" in captured.out and "warning(s)" in captured.out


def test_main_multiple_records(capsys, tmp_path):
    """Test CLI with multiple MARC records."""
    marc_file = tmp_path / "multiple.mrc"

    # Create two valid records with proper leader/control fields
    record1 = _create_valid_record()
    record1.get_fields("245")[0].delete_subfield("a")
    record1.get_fields("245")[0].add_subfield("a", "First title.")

    record2 = _create_valid_record()
    record2.get_fields("001")[0].data = "test002"
    record2.get_fields("245")[0].delete_subfield("a")
    record2.get_fields("245")[0].add_subfield("a", "Second title.")

    with open(marc_file, "wb") as f:
        f.write(record1.as_marc())
        f.write(record2.as_marc())

    with mock.patch.object(sys, "argv", ["marc-lint", str(marc_file)]):
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Processed 2 record(s)" in captured.out
        assert "Found 0 warning(s)" in captured.out


def test_main_multiple_records_with_warnings(capsys, tmp_path):
    """Test CLI with multiple records, some with warnings."""
    marc_file = tmp_path / "mixed.mrc"

    # Valid record
    record1 = _create_valid_record()

    # Record with warning (invalid ISBN)
    record2 = _create_valid_record(
        [Field(tag="020", indicators=[" ", " "], subfields=[Subfield("a", "bad-isbn")])]
    )
    record2.get_fields("001")[0].data = "test002"
    record2.get_fields("245")[0].delete_subfield("a")
    record2.get_fields("245")[0].add_subfield("a", "Title with warning.")

    # Another valid record
    record3 = _create_valid_record()
    record3.get_fields("001")[0].data = "test003"
    record3.get_fields("245")[0].delete_subfield("a")
    record3.get_fields("245")[0].add_subfield("a", "Another title.")

    with open(marc_file, "wb") as f:
        f.write(record1.as_marc())
        f.write(record2.as_marc())
        f.write(record3.as_marc())

    with mock.patch.object(sys, "argv", ["marc-lint", str(marc_file)]):
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "--- Record test002 ---" in captured.out
        assert "Processed 3 record(s)" in captured.out


def test_main_corrupted_file(capsys, tmp_path):
    """Test CLI with corrupted MARC file."""
    corrupt_file = tmp_path / "corrupt.mrc"

    # Write invalid MARC data
    with open(corrupt_file, "wb") as f:
        f.write(b"This is not valid MARC data")

    with mock.patch.object(sys, "argv", ["marc-lint", str(corrupt_file)]):
        with pytest.raises(SystemExit) as exc_info:
            main()

        # The corrupted data gets parsed by pymarc but generates warnings
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Record" in captured.out or "Error" in captured.err


def test_main_empty_file(capsys, tmp_path):
    """Test CLI with empty MARC file."""
    empty_file = tmp_path / "empty.mrc"
    empty_file.touch()

    with mock.patch.object(sys, "argv", ["marc-lint", str(empty_file)]):
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "No records found" in captured.out


def test_main_record_with_multiple_warnings(capsys, tmp_path):
    """Test CLI with a record containing multiple warnings."""
    marc_file = tmp_path / "multi_warnings.mrc"

    # Create a record with multiple invalid ISBN fields (but valid leader/control fields)
    record = _create_valid_record(
        [
            Field(
                tag="020",
                indicators=[" ", " "],
                subfields=[Subfield("a", "invalid-isbn-1")],
            ),
            Field(
                tag="020",
                indicators=[" ", " "],
                subfields=[Subfield("a", "invalid-isbn-2")],
            ),
        ]
    )

    with open(marc_file, "wb") as f:
        f.write(record.as_marc())

    with mock.patch.object(sys, "argv", ["marc-lint", str(marc_file)]):
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "--- Record test001 ---" in captured.out
        # Should have multiple warnings
        output_lines = captured.out.split("\n")
        warning_lines = [line for line in output_lines if "020" in line]
        assert len(warning_lines) >= 2


def test_main_path_object(capsys, mock_marc_file):
    """Test CLI handles Path object correctly."""
    # Ensure filepath is converted to string in argv
    with mock.patch.object(sys, "argv", ["marc-lint", str(mock_marc_file)]):
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Processed 1 record(s)" in captured.out


def test_main_summary_format(capsys, mock_marc_file_with_warnings):
    """Test CLI summary output format."""
    with mock.patch.object(
        sys, "argv", ["marc-lint", str(mock_marc_file_with_warnings)]
    ):
        with pytest.raises(SystemExit):
            main()

        captured = capsys.readouterr()
        # Check for separator line
        assert "=" * 60 in captured.out
        # Check summary appears after separator
        lines = captured.out.split("\n")
        sep_index = next(i for i, line in enumerate(lines) if "=" * 60 in line)
        assert any("Processed" in line for line in lines[sep_index:])
        assert any("Found" in line for line in lines[sep_index:])


# New tests for JSON output and options


def test_main_json_format(capsys, mock_marc_file):
    """Test CLI with JSON output format."""
    with mock.patch.object(
        sys, "argv", ["marc-lint", "-f", "json", str(mock_marc_file)]
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert isinstance(output, list)
        assert len(output) == 1
        assert output[0]["record_id"] == "test001"
        assert output[0]["is_valid"] is True
        assert output[0]["warnings"] == []


def test_main_json_format_with_warnings(capsys, mock_marc_file_with_warnings):
    """Test CLI JSON output with warnings."""
    with mock.patch.object(
        sys,
        "argv",
        ["marc-lint", "--format", "json", str(mock_marc_file_with_warnings)],
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output[0]["is_valid"] is False
        assert len(output[0]["warnings"]) > 0
        warning = output[0]["warnings"][0]
        assert "field" in warning
        assert "message" in warning


def test_main_quiet_mode(capsys, mock_marc_file):
    """Test CLI quiet mode suppresses summary."""
    with mock.patch.object(sys, "argv", ["marc-lint", "-q", str(mock_marc_file)]):
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        # No summary in quiet mode for valid records
        assert "Processed" not in captured.out
        assert captured.out.strip() == ""


def test_main_quiet_mode_with_warnings(capsys, mock_marc_file_with_warnings):
    """Test CLI quiet mode still shows warnings."""
    with mock.patch.object(
        sys, "argv", ["marc-lint", "--quiet", str(mock_marc_file_with_warnings)]
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        # Warnings should still appear
        assert "Record" in captured.out
        # But no summary
        assert "Processed" not in captured.out


def test_main_use_index_option(capsys, tmp_path):
    """Test CLI --use-index option."""
    marc_file = tmp_path / "no_001.mrc"

    # Create record without 001 field
    record = Record()
    record.leader = "00000nam a2200000 i 4500"
    record.add_field(Field(tag="008", data="240101s2024    xxu           000 0 eng d"))
    record.add_field(
        Field(
            tag="245",
            indicators=["1", "0"],
            subfields=[Subfield("a", "No control number.")],
        )
    )

    with open(marc_file, "wb") as f:
        f.write(record.as_marc())

    with mock.patch.object(
        sys, "argv", ["marc-lint", "-i", "-f", "json", str(marc_file)]
    ):
        with pytest.raises(SystemExit):
            main()

        captured = capsys.readouterr()
        output = json.loads(captured.out)
        # Should use "0" as the record ID
        assert output[0]["record_id"] == "0"


def test_main_invalid_format_option(capsys, mock_marc_file):
    """Test CLI with invalid format option."""
    with mock.patch.object(
        sys, "argv", ["marc-lint", "-f", "xml", str(mock_marc_file)]
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Invalid format" in captured.err


def test_main_unknown_option(capsys, mock_marc_file):
    """Test CLI with unknown option."""
    with mock.patch.object(
        sys, "argv", ["marc-lint", "--unknown", str(mock_marc_file)]
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Unknown option" in captured.err
