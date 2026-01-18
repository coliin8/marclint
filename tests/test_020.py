"""Pytest-based checks for 020 (ISBN) field validation.

These tests verify that the Python port correctly validates ISBN fields according to
the current implementation in linter.py, which:
- Checks ISBN-10 and ISBN-13 format and checksums
- Validates qualifier spacing in $a
- Checks for invalid characters in $a
- Validates numerically correct ISBNs in $z (cancelled/invalid)
"""

from pytest import fixture
from pymarc import Record, Field, Subfield

from tests.conftest import create_minimal_record


@fixture
def cases():
    """Generate synthetic MARC records with various 020 scenarios."""

    def create_record(fields: list[Field]) -> Record:
        """Helper to build a Record from a list of fields."""
        return create_minimal_record(fields)

    cases = {}

    # Case 1: Valid ISBN-10
    f1 = Field(
        tag="020",
        indicators=[" ", " "],
        subfields=[
            Subfield("a", "0123456789"),
        ],
    )
    cases["valid_isbn10"] = create_record([f1])

    # Case 2: Valid ISBN-10 with X checksum
    f2 = Field(
        tag="020",
        indicators=[" ", " "],
        subfields=[
            Subfield("a", "155404295X"),
        ],
    )
    cases["valid_isbn10_with_x"] = create_record([f2])

    # Case 3: Valid ISBN-13
    f3 = Field(
        tag="020",
        indicators=[" ", " "],
        subfields=[
            Subfield("a", "9780123456786"),
        ],
    )
    cases["valid_isbn13"] = create_record([f3])

    # Case 4: Valid ISBN-10 with hyphens
    f4 = Field(
        tag="020",
        indicators=[" ", " "],
        subfields=[
            Subfield("a", "0-12-345678-9"),
        ],
    )
    cases["valid_isbn10_with_hyphens"] = create_record([f4])

    # Case 5: Valid ISBN-10 with qualifier (proper spacing)
    f5 = Field(
        tag="020",
        indicators=[" ", " "],
        subfields=[
            Subfield("a", "0123456789 (hardcover)"),
        ],
    )
    cases["valid_isbn10_with_qualifier"] = create_record([f5])

    # Case 6: ISBN-10 with bad checksum
    f6 = Field(
        tag="020",
        indicators=[" ", " "],
        subfields=[
            Subfield("a", "0123456788"),  # Should be 9
        ],
    )
    cases["isbn10_bad_checksum"] = create_record([f6])

    # Case 7: ISBN-13 with bad checksum
    f7 = Field(
        tag="020",
        indicators=[" ", " "],
        subfields=[
            Subfield("a", "9780123456787"),  # Should be 6
        ],
    )
    cases["isbn13_bad_checksum"] = create_record([f7])

    # Case 8: ISBN with wrong number of digits
    f8 = Field(
        tag="020",
        indicators=[" ", " "],
        subfields=[
            Subfield("a", "012345678"),  # Only 9 digits
        ],
    )
    cases["isbn_wrong_length"] = create_record([f8])

    # Case 9: ISBN with qualifier but no space before parenthesis
    f9 = Field(
        tag="020",
        indicators=[" ", " "],
        subfields=[
            Subfield("a", "0123456789(hardcover)"),  # Missing space
        ],
    )
    cases["isbn_qualifier_no_space"] = create_record([f9])

    # Case 10: ISBN with invalid characters
    f10 = Field(
        tag="020",
        indicators=[" ", " "],
        subfields=[
            Subfield("a", "ISBN 0123456789"),  # Should not start with "ISBN"
        ],
    )
    cases["isbn_invalid_characters"] = create_record([f10])

    # Case 11: Valid numerically correct ISBN in $z (should warn)
    # Note: must be hyphenated or start with "ISBN" to trigger check
    f11 = Field(
        tag="020",
        indicators=[" ", " "],
        subfields=[
            Subfield("z", "0-12-345678-9"),
        ],
    )
    cases["isbn_z_numerically_valid"] = create_record([f11])

    # Case 12: Invalid ISBN in $z (should not warn about validity)
    f12 = Field(
        tag="020",
        indicators=[" ", " "],
        subfields=[
            Subfield("z", "0123456788"),  # Bad checksum
        ],
    )
    cases["isbn_z_invalid"] = create_record([f12])

    # Case 13: ISBN in $z with "ISBN" prefix
    f13 = Field(
        tag="020",
        indicators=[" ", " "],
        subfields=[
            Subfield("z", "ISBN 0123456789"),
        ],
    )
    cases["isbn_z_with_prefix"] = create_record([f13])

    # Case 14: ISBN in $z with hyphenated format
    f14 = Field(
        tag="020",
        indicators=[" ", " "],
        subfields=[
            Subfield("z", "0-12-345678-9"),
        ],
    )
    cases["isbn_z_hyphenated"] = create_record([f14])

    # Case 15: Multiple ISBNs (both $a and $z)
    f15 = Field(
        tag="020",
        indicators=[" ", " "],
        subfields=[
            Subfield("a", "0123456789 (hardcover)"),
            Subfield("z", "9876543210"),  # Bad checksum
        ],
    )
    cases["multiple_isbns"] = create_record([f15])

    # Case 16: ISBN-13 with qualifier
    f16 = Field(
        tag="020",
        indicators=[" ", " "],
        subfields=[
            Subfield("a", "9780123456786 (paperback)"),
        ],
    )
    cases["isbn13_with_qualifier"] = create_record([f16])

    # Case 17: ISBN with multiple qualifiers
    f17 = Field(
        tag="020",
        indicators=[" ", " "],
        subfields=[
            Subfield("a", "0123456789 (v. 1 : hardcover)"),
        ],
    )
    cases["isbn_multiple_qualifiers"] = create_record([f17])

    # Case 18: ISBN-10 with X not at end
    f18 = Field(
        tag="020",
        indicators=[" ", " "],
        subfields=[
            Subfield("a", "X123456789"),  # X should only be at end
        ],
    )
    cases["isbn10_x_not_at_end"] = create_record([f18])

    # Case 19: Valid ISBN with price
    f19 = Field(
        tag="020",
        indicators=[" ", " "],
        subfields=[
            Subfield("a", "0123456789"),
            Subfield("c", "$29.95"),
        ],
    )
    cases["isbn_with_price"] = create_record([f19])

    # Case 20: Empty $a subfield
    f20 = Field(
        tag="020",
        indicators=[" ", " "],
        subfields=[
            Subfield("a", ""),
        ],
    )
    cases["isbn_empty"] = create_record([f20])

    return cases


def test_020_valid_isbn10(linter, cases):
    """Valid ISBN-10 should not produce warnings."""
    record = cases["valid_isbn10"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    assert "020: Subfield a has bad checksum" not in warnings
    assert "020: Subfield a has the wrong number of digits" not in warnings


def test_020_valid_isbn10_with_x(linter, cases):
    """Valid ISBN-10 with X checksum should not produce warnings."""
    record = cases["valid_isbn10_with_x"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    assert "020: Subfield a has bad checksum" not in warnings


def test_020_valid_isbn13(linter, cases):
    """Valid ISBN-13 should not produce warnings."""
    record = cases["valid_isbn13"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    assert "020: Subfield a has bad checksum" not in warnings


def test_020_valid_isbn10_with_hyphens(linter, cases):
    """Valid ISBN-10 with hyphens should not produce warnings."""
    record = cases["valid_isbn10_with_hyphens"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    assert "020: Subfield a has bad checksum" not in warnings


def test_020_valid_isbn10_with_qualifier(linter, cases):
    """Valid ISBN-10 with properly spaced qualifier should not produce warnings."""
    record = cases["valid_isbn10_with_qualifier"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    assert "020: Subfield a qualifier must be preceded by space" not in warnings
    assert "020: Subfield a has bad checksum" not in warnings


def test_020_isbn10_bad_checksum(linter, cases):
    """ISBN-10 with bad checksum should warn."""
    record = cases["isbn10_bad_checksum"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    assert "020: Subfield a has bad checksum" in warnings


def test_020_isbn13_bad_checksum(linter, cases):
    """ISBN-13 with bad checksum should warn."""
    record = cases["isbn13_bad_checksum"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    assert "020: Subfield a has bad checksum (13 digit)" in warnings


def test_020_isbn_wrong_length(linter, cases):
    """ISBN with wrong number of digits should warn."""
    record = cases["isbn_wrong_length"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    assert "020: Subfield a has the wrong number of digits" in warnings


def test_020_isbn_qualifier_no_space(linter, cases):
    """ISBN with qualifier but no space before parenthesis should warn."""
    record = cases["isbn_qualifier_no_space"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    assert "020: Subfield a qualifier must be preceded by space" in warnings


def test_020_isbn_invalid_characters(linter, cases):
    """ISBN with invalid characters (prefix) should warn."""
    record = cases["isbn_invalid_characters"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    assert "020: Subfield a may have invalid characters" in warnings


def test_020_isbn_z_numerically_valid(linter, cases):
    """Numerically valid ISBN in $z should warn (it's marked as cancelled but valid)."""
    record = cases["isbn_z_numerically_valid"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    assert "020: Subfield z is numerically valid" in warnings


def test_020_isbn_z_invalid(linter, cases):
    """Invalid ISBN in $z should not warn about validity (it's supposed to be invalid)."""
    record = cases["isbn_z_invalid"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    # Should not warn because $z is for invalid/cancelled ISBNs
    assert "020: Subfield z is numerically valid" not in warnings


def test_020_isbn_z_with_prefix(linter, cases):
    """ISBN in $z with 'ISBN' prefix and valid number should warn."""
    record = cases["isbn_z_with_prefix"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    assert "020: Subfield z is numerically valid" in warnings


def test_020_isbn_z_hyphenated(linter, cases):
    """Hyphenated ISBN in $z that's numerically valid should warn."""
    record = cases["isbn_z_hyphenated"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    assert "020: Subfield z is numerically valid" in warnings


def test_020_multiple_isbns(linter, cases):
    """Multiple ISBNs in $a and $z should validate independently."""
    record = cases["multiple_isbns"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    # $a should be valid
    assert "020: Subfield a has bad checksum" not in warnings
    # $z should not warn (bad checksum is expected)
    assert "020: Subfield z is numerically valid" not in warnings


def test_020_isbn13_with_qualifier(linter, cases):
    """Valid ISBN-13 with qualifier should not produce warnings."""
    record = cases["isbn13_with_qualifier"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    assert "020: Subfield a has bad checksum" not in warnings
    assert "020: Subfield a qualifier must be preceded by space" not in warnings


def test_020_isbn_multiple_qualifiers(linter, cases):
    """ISBN with multiple qualifiers should not produce warnings if properly spaced."""
    record = cases["isbn_multiple_qualifiers"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    assert "020: Subfield a qualifier must be preceded by space" not in warnings


def test_020_isbn10_x_not_at_end(linter, cases):
    """ISBN-10 with X not at end should warn about wrong number of digits."""
    record = cases["isbn10_x_not_at_end"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    assert "020: Subfield a has the wrong number of digits" in warnings


def test_020_isbn_with_price(linter, cases):
    """ISBN with price in $c should validate ISBN normally."""
    record = cases["isbn_with_price"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    assert "020: Subfield a has bad checksum" not in warnings


def test_020_isbn_empty(linter, cases):
    """Empty ISBN should warn about wrong number of digits."""
    record = cases["isbn_empty"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    assert "020: Subfield a has the wrong number of digits" in warnings


def test_020_comprehensive_smoke(linter, cases):
    """All 020 test cases should process without crashing."""
    for name, record in cases.items():
        linter.clear_warnings()
        linter.check_record(record)
        # Basic assertion: we get a list of warnings
        assert isinstance(linter.warnings(), list)
