"""Tests for CLI functionality."""

import sys
from unittest import mock

import pytest
from pymarc import Field, Record, Subfield

from marc_lint.cli import main


@pytest.fixture
def mock_marc_file(tmp_path):
    """Create a temporary MARC file for testing."""
    marc_file = tmp_path / "test.mrc"

    # Create a valid MARC record
    record = Record()
    record.add_field(
        Field(
            tag="245", indicators=["1", "0"], subfields=[Subfield("a", "Test title.")]
        )
    )

    with open(marc_file, "wb") as f:
        f.write(record.as_marc())

    return marc_file


@pytest.fixture
def mock_marc_file_with_warnings(tmp_path):
    """Create a temporary MARC file with validation warnings."""
    marc_file = tmp_path / "test_warnings.mrc"

    # Create a record with an invalid ISBN
    record = Record()
    record.add_field(
        Field(
            tag="245", indicators=["1", "0"], subfields=[Subfield("a", "Test title.")]
        )
    )
    record.add_field(
        Field(
            tag="020", indicators=[" ", " "], subfields=[Subfield("a", "invalid-isbn")]
        )
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
        assert "Usage: marc-lint <file.mrc>" in captured.out
        assert "Lint a MARC21 file" in captured.out


def test_main_file_not_found(capsys):
    """Test CLI with non-existent file."""
    with mock.patch.object(sys, "argv", ["marc-lint", "nonexistent.mrc"]):
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Error: File 'nonexistent.mrc' not found" in captured.out


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
        assert "--- Record 1 ---" in captured.out
        assert "020:" in captured.out  # Just check for ISBN-related warning
        assert "Processed 1 record(s)" in captured.out
        assert "Found" in captured.out and "warning(s)" in captured.out


def test_main_multiple_records(capsys, tmp_path):
    """Test CLI with multiple MARC records."""
    marc_file = tmp_path / "multiple.mrc"

    # Create two valid records
    record1 = Record()
    record1.add_field(
        Field(
            tag="245", indicators=["1", "0"], subfields=[Subfield("a", "First title.")]
        )
    )

    record2 = Record()
    record2.add_field(
        Field(
            tag="245", indicators=["1", "0"], subfields=[Subfield("a", "Second title.")]
        )
    )

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
    record1 = Record()
    record1.add_field(
        Field(
            tag="245", indicators=["1", "0"], subfields=[Subfield("a", "Valid title.")]
        )
    )

    # Record with warning
    record2 = Record()
    record2.add_field(
        Field(
            tag="245",
            indicators=["1", "0"],
            subfields=[Subfield("a", "Title with warning.")],
        )
    )
    record2.add_field(
        Field(tag="020", indicators=[" ", " "], subfields=[Subfield("a", "bad-isbn")])
    )

    # Another valid record
    record3 = Record()
    record3.add_field(
        Field(
            tag="245",
            indicators=["1", "0"],
            subfields=[Subfield("a", "Another title.")],
        )
    )

    with open(marc_file, "wb") as f:
        f.write(record1.as_marc())
        f.write(record2.as_marc())
        f.write(record3.as_marc())

    with mock.patch.object(sys, "argv", ["marc-lint", str(marc_file)]):
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "--- Record 2 ---" in captured.out
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
        assert "Record 1" in captured.out or "Error reading MARC file:" in captured.out


def test_main_empty_file(capsys, tmp_path):
    """Test CLI with empty MARC file."""
    empty_file = tmp_path / "empty.mrc"
    empty_file.touch()

    with mock.patch.object(sys, "argv", ["marc-lint", str(empty_file)]):
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Processed 0 record(s)" in captured.out
        assert "Found 0 warning(s)" in captured.out


def test_main_record_with_multiple_warnings(capsys, tmp_path):
    """Test CLI with a record containing multiple warnings."""
    marc_file = tmp_path / "multi_warnings.mrc"

    # Create a record with multiple invalid fields
    record = Record()
    record.add_field(
        Field(
            tag="020",
            indicators=[" ", " "],
            subfields=[Subfield("a", "invalid-isbn-1")],
        )
    )
    record.add_field(
        Field(
            tag="020",
            indicators=[" ", " "],
            subfields=[Subfield("a", "invalid-isbn-2")],
        )
    )

    with open(marc_file, "wb") as f:
        f.write(record.as_marc())

    with mock.patch.object(sys, "argv", ["marc-lint", str(marc_file)]):
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "--- Record 1 ---" in captured.out
        # Should have multiple warnings
        output_lines = captured.out.split("\n")
        print(output_lines)
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
