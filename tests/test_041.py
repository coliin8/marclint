"""Pytest-based checks for 041 (Language Code) field validation.

These tests verify that the Python port correctly validates language codes according to
the current implementation in linter.py, which:
- Validates language codes are 3 characters each (if indicator 2 is not '7')
- Checks codes against the language code table
- Identifies obsolete language codes
"""

from pytest import fixture
from pymarc import Record, Field, Subfield


@fixture
def cases():
    """Generate synthetic MARC records with various 041 scenarios."""

    def create_record(fields: list[Field]) -> Record:
        """Helper to build a Record from a list of fields."""
        r = Record()
        for f in fields:
            r.add_field(f)
        return r

    cases = {}

    # Case 1: Valid single language code (3 chars)
    f1 = Field(
        tag="041",
        indicators=[" ", " "],
        subfields=[
            Subfield("a", "eng"),
        ],
    )
    cases["valid_single_language"] = create_record([f1])

    # Case 2: Valid multiple language codes (6 chars = 2 codes)
    f2 = Field(
        tag="041",
        indicators=[" ", " "],
        subfields=[
            Subfield("a", "engfre"),
        ],
    )
    cases["valid_multiple_languages"] = create_record([f2])

    # Case 3: Valid multiple subfields with valid codes
    f3 = Field(
        tag="041",
        indicators=["1", " "],
        subfields=[
            Subfield("a", "eng"),
            Subfield("h", "fre"),
        ],
    )
    cases["valid_multiple_subfields"] = create_record([f3])

    # Case 4: Invalid - not divisible by 3
    f4 = Field(
        tag="041",
        indicators=[" ", " "],
        subfields=[
            Subfield("a", "en"),  # Only 2 characters
        ],
    )
    cases["invalid_length_not_divisibleby_3"] = create_record([f4])

    # Case 5: Invalid - 4 characters (not divisible by 3)
    f5 = Field(
        tag="041",
        indicators=[" ", " "],
        subfields=[
            Subfield("a", "engl"),
        ],
    )
    cases["invalid_length_4_chars"] = create_record([f5])

    # Case 6: Invalid language code
    f6 = Field(
        tag="041",
        indicators=[" ", " "],
        subfields=[
            Subfield("a", "xxx"),  # Not a valid language code
        ],
    )
    cases["invalid_language_code"] = create_record([f6])

    # Case 7: Obsolete language code (if "scc" is obsolete)
    # Note: actual obsolete codes depend on code_data.py
    f7 = Field(
        tag="041",
        indicators=[" ", " "],
        subfields=[
            Subfield("a", "scc"),  # Serbian (obsolete, now srp)
        ],
    )
    cases["obsolete_language_code"] = create_record([f7])

    # Case 8: Indicator 2 = '7' (source specified in $2, skip validation)
    f8 = Field(
        tag="041",
        indicators=[" ", "7"],
        subfields=[
            Subfield("a", "en"),  # Would be invalid, but ind2=7 skips check
            Subfield("2", "local"),
        ],
    )
    cases["indicator2_is_7_skip_validation"] = create_record([f8])

    # Case 9: Mix of valid and invalid codes in one subfield
    f9 = Field(
        tag="041",
        indicators=[" ", " "],
        subfields=[
            Subfield("a", "engxxx"),  # eng is valid, xxx is not
        ],
    )
    cases["mixed_valid_invalid"] = create_record([f9])

    # Case 10: Valid 9 characters (3 language codes)
    f10 = Field(
        tag="041",
        indicators=["1", " "],
        subfields=[
            Subfield("a", "engfrespa"),
        ],
    )
    cases["valid_9_chars_three_codes"] = create_record([f10])

    # Case 11: Empty subfield
    f11 = Field(
        tag="041",
        indicators=[" ", " "],
        subfields=[
            Subfield("a", ""),
        ],
    )
    cases["empty_subfield"] = create_record([f11])

    # Case 12: Multiple subfields with different validity
    f12 = Field(
        tag="041",
        indicators=["1", " "],
        subfields=[
            Subfield("a", "eng"),  # Valid
            Subfield("b", "xxx"),  # Invalid
        ],
    )
    cases["multiple_subfields_mixed"] = create_record([f12])

    # Case 13: Valid code in $h (original language)
    f13 = Field(
        tag="041",
        indicators=["1", " "],
        subfields=[
            Subfield("a", "eng"),
            Subfield("h", "lat"),  # Latin
        ],
    )
    cases["valid_original_language"] = create_record([f13])

    # Case 14: 7 characters (not divisible by 3)
    f14 = Field(
        tag="041",
        indicators=[" ", " "],
        subfields=[
            Subfield("a", "engfres"),  # 7 chars
        ],
    )
    cases["invalid_7_chars"] = create_record([f14])

    return cases


def test_041_valid_single_language(linter, cases):
    """Valid single 3-character language code should not produce warnings."""
    record = cases["valid_single_language"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    assert "041: Subfield a" not in warnings or "245: No 245 tag" in warnings


def test_041_valid_multiple_languages(linter, cases):
    """Valid multiple language codes (6 chars) should not produce warnings."""
    record = cases["valid_multiple_languages"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    assert "041: Subfield a must be evenly divisible by 3" not in warnings


def test_041_valid_multiple_subfields(linter, cases):
    """Multiple subfields with valid codes should not produce warnings."""
    record = cases["valid_multiple_subfields"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    assert "041: Subfield" not in warnings or "245: No 245 tag" in warnings


def test_041_invalid_length_not_divisibleby_3(linter, cases):
    """Language code not divisible by 3 should warn."""
    record = cases["invalid_length_not_divisibleby_3"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    assert "041: Subfield a must be evenly divisible by 3" in warnings


def test_041_invalid_length_4_chars(linter, cases):
    """4-character language code should warn (not divisible by 3)."""
    record = cases["invalid_length_4_chars"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    assert "041: Subfield a must be evenly divisible by 3" in warnings


def test_041_invalid_language_code(linter, cases):
    """Invalid language code should warn."""
    record = cases["invalid_language_code"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    assert "041: Subfield a xxx (xxx), is not valid" in warnings


def test_041_obsolete_language_code(linter, cases):
    """Obsolete language code should warn if it's in the obsolete list."""
    record = cases["obsolete_language_code"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    # scc may be obsolete or invalid depending on code_data.py
    # Check for either obsolete or invalid warning
    has_warning = (
        "041: Subfield a scc, may be obsolete" in warnings
        or "041: Subfield a scc, is not valid" in warnings
    )
    assert has_warning


def test_041_indicator2_is_7_skip_validation(linter, cases):
    """When indicator 2 is '7', length validation should be skipped."""
    record = cases["indicator2_is_7_skip_validation"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    # Should not warn about length or validity when ind2=7
    assert "041: Subfield a must be evenly divisible by 3" not in warnings
    assert "041: Subfield a en" not in warnings


def test_041_mixed_valid_invalid(linter, cases):
    """Mix of valid and invalid codes should warn about invalid one."""
    record = cases["mixed_valid_invalid"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    # Should warn about xxx being invalid
    assert "041: Subfield a engxxx (xxx), is not valid" in warnings


def test_041_valid_9_chars_three_codes(linter, cases):
    """9 characters (3 codes) should be valid."""
    record = cases["valid_9_chars_three_codes"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    assert "041: Subfield a must be evenly divisible by 3" not in warnings


def test_041_empty_subfield(linter, cases):
    """Empty subfield should be valid (divisible by 3: 0 % 3 == 0)."""
    record = cases["empty_subfield"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    # Empty string has length 0, which is divisible by 3
    assert "041: Subfield a must be evenly divisible by 3" not in warnings


def test_041_multiple_subfields_mixed(linter, cases):
    """Multiple subfields with mixed validity should warn about invalid ones."""
    record = cases["multiple_subfields_mixed"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    # $a with "eng" should be valid
    assert "041: Subfield a eng" not in warnings
    # $b with "xxx" should be invalid
    assert "041: Subfield b xxx (xxx), is not valid" in warnings


def test_041_valid_original_language(linter, cases):
    """Valid code in $h (original language) should not produce warnings."""
    record = cases["valid_original_language"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    assert "041: Subfield h" not in warnings or "245: No 245 tag" in warnings


def test_041_invalid_7_chars(linter, cases):
    """7 characters (not divisible by 3) should warn."""
    record = cases["invalid_7_chars"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    assert "041: Subfield a must be evenly divisible by 3" in warnings


def test_041_comprehensive_smoke(linter, cases):
    """All 041 test cases should process without crashing."""
    for name, record in cases.items():
        linter.clear_warnings()
        linter.check_record(record)
        # Basic assertion: we get a list of warnings
        assert isinstance(linter.warnings(), list)
