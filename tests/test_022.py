"""Tests for 022 field (ISSN) validation."""

import pytest
from pymarc import Record, Field, Subfield

from tests.conftest import create_minimal_record


def _create_record_with_022(field_022: Field) -> Record:
    """Helper to create a minimal MARC record with 245 and 022 fields."""
    return create_minimal_record([field_022])


def _warnings_match(actual: list[str], expected: list[str]) -> bool:
    """Check that actual warnings contain the expected warning messages.

    Handles the record_id prefix in actual warnings by checking if
    each expected message is contained within an actual warning.
    """
    if len(actual) != len(expected):
        return False
    if not expected:
        return True
    # Each expected warning should appear in exactly one actual warning
    matched = set()
    for exp in expected:
        for i, act in enumerate(actual):
            if i not in matched and exp in act:
                matched.add(i)
                break
        else:
            return False
    return True


@pytest.fixture
def cases():
    """Define test cases for 022 field validation."""
    return [
        # Case 1: Valid ISSN with hyphen
        {
            "field": Field(
                tag="022",
                indicators=[" ", " "],
                subfields=[Subfield("a", "0378-5955")],
            ),
            "expected_warnings": [],
            "description": "Valid ISSN with hyphen format",
        },
        # Case 2: Valid ISSN without hyphen
        {
            "field": Field(
                tag="022",
                indicators=[" ", " "],
                subfields=[Subfield("a", "03785955")],
            ),
            "expected_warnings": [],
            "description": "Valid ISSN without hyphen",
        },
        # Case 3: Valid ISSN with X check digit
        {
            "field": Field(
                tag="022",
                indicators=[" ", " "],
                subfields=[Subfield("a", "0028-0836")],
            ),
            "expected_warnings": [],
            "description": "Valid ISSN (Nature journal)",
        },
        # Case 4: Invalid ISSN - bad checksum
        {
            "field": Field(
                tag="022",
                indicators=[" ", " "],
                subfields=[Subfield("a", "0378-5956")],
            ),
            "expected_warnings": ["022: Subfield a has bad checksum, 0378-5956."],
            "description": "Invalid ISSN with bad checksum",
        },
        # Case 5: Invalid ISSN - wrong length
        {
            "field": Field(
                tag="022",
                indicators=[" ", " "],
                subfields=[Subfield("a", "0378-59")],
            ),
            "expected_warnings": [
                "022: Subfield a has the wrong number of digits, 0378-59."
            ],
            "description": "ISSN too short",
        },
        # Case 6: Invalid ISSN - improper hyphen placement
        {
            "field": Field(
                tag="022",
                indicators=[" ", " "],
                subfields=[Subfield("a", "037-85955")],
            ),
            "expected_warnings": [
                "022: Subfield a has the wrong number of digits, 037-85955.",
            ],
            "description": "ISSN with hyphen in wrong position",
        },
        # Case 7: Subfield $y with numerically valid ISSN (should warn)
        {
            "field": Field(
                tag="022",
                indicators=[" ", " "],
                subfields=[Subfield("a", "0378-5955"), Subfield("y", "0028-0836")],
            ),
            "expected_warnings": ["022: Subfield y is numerically valid."],
            "description": "Incorrect ISSN ($y) that is numerically valid",
        },
        # Case 8: Subfield $y with invalid ISSN (should not warn)
        {
            "field": Field(
                tag="022",
                indicators=[" ", " "],
                subfields=[Subfield("a", "0378-5955"), Subfield("y", "0046-2255")],
            ),
            "expected_warnings": [],
            "description": "Incorrect ISSN ($y) that is invalid - no warning expected",
        },
        # Case 9: Subfield $z (canceled ISSN)
        {
            "field": Field(
                tag="022",
                indicators=[" ", " "],
                subfields=[Subfield("a", "0410-7543"), Subfield("z", "0527-740X")],
            ),
            "expected_warnings": [],
            "description": "Canceled ISSN in subfield $z",
        },
        # Case 10: Multiple ISSNs - all valid
        {
            "field": Field(
                tag="022",
                indicators=[" ", " "],
                subfields=[
                    Subfield("a", "0378-5955"),
                    Subfield("y", "1234-5678"),
                    Subfield("z", "0527-740X"),
                ],
            ),
            "expected_warnings": [],
            "description": "Multiple ISSN subfields with valid formats",
        },
        # Case 11: ISSN with lowercase x
        {
            "field": Field(
                tag="022",
                indicators=[" ", " "],
                subfields=[Subfield("a", "0002-953x")],
            ),
            "expected_warnings": [],
            "description": "Valid ISSN with lowercase x check digit",
        },
        # Case 12: ISSN with invalid characters
        {
            "field": Field(
                tag="022",
                indicators=[" ", " "],
                subfields=[Subfield("a", "ABC-DEFG")],
            ),
            "expected_warnings": [
                "022: Subfield a has the wrong number of digits, ABC-DEFG."
            ],
            "description": "ISSN with alphabetic characters",
        },
        # Case 13: Empty subfield $a
        {
            "field": Field(
                tag="022",
                indicators=[" ", " "],
                subfields=[Subfield("a", "")],
            ),
            "expected_warnings": ["022: Subfield a has the wrong number of digits, ."],
            "description": "Empty ISSN subfield",
        },
        # Case 14: ISSN with extra text
        {
            "field": Field(
                tag="022",
                indicators=[" ", " "],
                subfields=[Subfield("a", "0378-5955 (print)")],
            ),
            "expected_warnings": [],
            "description": "ISSN with qualifier text",
        },
        # Case 15: Subfield $z with invalid format
        {
            "field": Field(
                tag="022",
                indicators=[" ", " "],
                subfields=[Subfield("a", "0378-5955"), Subfield("z", "12345")],
            ),
            "expected_warnings": ["022: Subfield z has invalid format, 12345."],
            "description": "Canceled ISSN with wrong length",
        },
    ]


def test_022_valid_issn_with_hyphen(linter, cases):
    """Test valid ISSN with standard hyphen format."""
    case = cases[0]
    rec = _create_record_with_022(case["field"])
    linter.check_record(rec)
    assert _warnings_match(linter.warnings(), case["expected_warnings"])


def test_022_valid_issn_no_hyphen(linter, cases):
    """Test valid ISSN without hyphen."""
    case = cases[1]
    rec = _create_record_with_022(case["field"])
    linter.check_record(rec)
    assert _warnings_match(linter.warnings(), case["expected_warnings"])


def test_022_valid_issn_nature(linter, cases):
    """Test well-known valid ISSN."""
    case = cases[2]
    rec = _create_record_with_022(case["field"])
    linter.check_record(rec)
    assert _warnings_match(linter.warnings(), case["expected_warnings"])


def test_022_invalid_checksum(linter, cases):
    """Test ISSN with invalid checksum."""
    case = cases[3]
    rec = _create_record_with_022(case["field"])
    linter.check_record(rec)
    assert _warnings_match(linter.warnings(), case["expected_warnings"])


def test_022_wrong_length(linter, cases):
    """Test ISSN with wrong number of digits."""
    case = cases[4]
    rec = _create_record_with_022(case["field"])
    linter.check_record(rec)
    assert _warnings_match(linter.warnings(), case["expected_warnings"])


def test_022_improper_hyphen(linter, cases):
    """Test ISSN with hyphen in wrong position."""
    case = cases[5]
    rec = _create_record_with_022(case["field"])
    linter.check_record(rec)
    assert _warnings_match(linter.warnings(), case["expected_warnings"])


def test_022_subfield_y_valid(linter, cases):
    """Test incorrect ISSN ($y) that is numerically valid."""
    case = cases[6]
    rec = _create_record_with_022(case["field"])
    linter.check_record(rec)
    assert _warnings_match(linter.warnings(), case["expected_warnings"])


def test_022_subfield_y_invalid(linter, cases):
    """Test incorrect ISSN ($y) that is invalid - no warning."""
    case = cases[7]
    rec = _create_record_with_022(case["field"])
    linter.check_record(rec)
    assert _warnings_match(linter.warnings(), case["expected_warnings"])


def test_022_subfield_z_canceled(linter, cases):
    """Test canceled ISSN in subfield $z."""
    case = cases[8]
    rec = _create_record_with_022(case["field"])
    linter.check_record(rec)
    assert _warnings_match(linter.warnings(), case["expected_warnings"])


def test_022_multiple_issns(linter, cases):
    """Test multiple ISSN subfields."""
    case = cases[9]
    rec = _create_record_with_022(case["field"])
    linter.check_record(rec)
    assert _warnings_match(linter.warnings(), case["expected_warnings"])


def test_022_lowercase_x(linter, cases):
    """Test ISSN with lowercase x check digit."""
    case = cases[10]
    rec = _create_record_with_022(case["field"])
    linter.check_record(rec)
    assert _warnings_match(linter.warnings(), case["expected_warnings"])


def test_022_invalid_characters(linter, cases):
    """Test ISSN with alphabetic characters."""
    case = cases[11]
    rec = _create_record_with_022(case["field"])
    linter.check_record(rec)
    assert _warnings_match(linter.warnings(), case["expected_warnings"])


def test_022_empty_subfield(linter, cases):
    """Test empty ISSN subfield."""
    case = cases[12]
    rec = _create_record_with_022(case["field"])
    linter.check_record(rec)
    assert _warnings_match(linter.warnings(), case["expected_warnings"])


def test_022_with_qualifier(linter, cases):
    """Test ISSN with qualifier text."""
    case = cases[13]
    rec = _create_record_with_022(case["field"])
    linter.check_record(rec)
    assert _warnings_match(linter.warnings(), case["expected_warnings"])


def test_022_subfield_z_invalid_format(linter, cases):
    """Test canceled ISSN with invalid format."""
    case = cases[14]
    rec = _create_record_with_022(case["field"])
    linter.check_record(rec)
    assert _warnings_match(linter.warnings(), case["expected_warnings"])


def test_022_comprehensive_smoke(linter):
    """Comprehensive smoke test with multiple 022 scenarios."""
    # Create record with proper leader/008 to avoid leader/control field warnings
    rec = create_minimal_record()

    # Valid ISSN
    rec.add_field(
        Field(
            tag="022",
            indicators=[" ", " "],
            subfields=[Subfield("a", "0378-5955")],
        )
    )

    # Invalid checksum
    rec.add_field(
        Field(
            tag="022",
            indicators=[" ", " "],
            subfields=[Subfield("a", "0378-5956")],
        )
    )

    # With incorrect (numerically valid) and canceled
    rec.add_field(
        Field(
            tag="022",
            indicators=[" ", " "],
            subfields=[
                Subfield("a", "0378-5955"),
                Subfield("y", "0028-0836"),
                Subfield("z", "0527-740X"),
            ],
        )
    )

    linter.check_record(rec)
    warnings = linter.warnings()

    # Should have warnings for invalid checksum and valid $y
    assert any("has bad checksum" in w for w in warnings)
    assert any("Subfield y is numerically valid" in w for w in warnings)
    assert len(warnings) == 2
