"""Unit tests for check_043 (Geographic Area Code validation)."""

import pytest
from pymarc import Field, Subfield

from tests.conftest import create_minimal_record


def make_043_record(subfields_data):
    """Create a minimal record with a 043 field."""
    subfields = [Subfield(code=sf[0], value=sf[1]) for sf in subfields_data]
    field_043 = Field(tag="043", indicators=[" ", " "], subfields=subfields)
    return create_minimal_record([field_043])


@pytest.fixture
def cases():
    """Test cases for 043 field validation."""
    return {
        # Valid cases
        "valid_single_code": make_043_record([("a", "n-us---")]),
        "valid_multiple_codes": make_043_record([("a", "n-us---"), ("a", "e-uk---")]),
        "valid_us_state": make_043_record([("a", "n-us-ca")]),
        "valid_asia": make_043_record([("a", "a-ja---")]),
        "valid_europe": make_043_record([("a", "e-fr---")]),
        # Invalid length cases
        "invalid_length_short": make_043_record([("a", "n-us")]),
        "invalid_length_long": make_043_record([("a", "n-us----")]),
        "invalid_length_empty": make_043_record([("a", "")]),
        # Invalid code cases
        "invalid_code": make_043_record([("a", "x-xx---")]),
        "invalid_code_wrong_pattern": make_043_record([("a", "nope123")]),
        # Obsolete geographic area codes
        "obsolete_code": make_043_record([("a", "e-ur-ai")]),  # Armenia (USSR)
        "multiple_obsolete": make_043_record(
            [("a", "e-ur-kz"), ("a", "e-ur-uz")]
        ),  # Kazakhstan, Uzbekistan (USSR)
        # Mixed validity
        "multiple_mixed_validity": make_043_record(
            [("a", "n-us---"), ("a", "x-xx---"), ("a", "e-fr---")]
        ),
        # Other subfields (should be ignored)
        "with_other_subfields": make_043_record(
            [("a", "n-us---"), ("b", "Some other data"), ("c", "More data")]
        ),
        # Comprehensive smoke test
        "comprehensive_smoke": make_043_record(
            [("a", "n-us---"), ("a", "n-us-ny"), ("a", "e-uk---"), ("a", "a-ja---")]
        ),
    }


def test_043_valid_single_code(linter, cases):
    """Single valid geographic code should not warn."""
    record = cases["valid_single_code"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    assert "043: Subfield a" not in warnings


def test_043_valid_multiple_codes(linter, cases):
    """Multiple valid geographic codes should not warn."""
    record = cases["valid_multiple_codes"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    assert "043: Subfield a" not in warnings


def test_043_valid_us_state(linter, cases):
    """Valid US state code should not warn."""
    record = cases["valid_us_state"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    assert "043: Subfield a" not in warnings


def test_043_valid_asia(linter, cases):
    """Valid Asian country code should not warn."""
    record = cases["valid_asia"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    assert "043: Subfield a" not in warnings


def test_043_valid_europe(linter, cases):
    """Valid European country code should not warn."""
    record = cases["valid_europe"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    assert "043: Subfield a" not in warnings


def test_043_invalid_length_short(linter, cases):
    """Code shorter than 7 characters should warn."""
    record = cases["invalid_length_short"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    assert "043: Subfield a must be exactly 7 characters, n-us" in warnings


def test_043_invalid_length_long(linter, cases):
    """Code longer than 7 characters should warn."""
    record = cases["invalid_length_long"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    assert "043: Subfield a must be exactly 7 characters, n-us----" in warnings


def test_043_invalid_length_empty(linter, cases):
    """Empty code should warn."""
    record = cases["invalid_length_empty"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    assert "043: Subfield a must be exactly 7 characters" in warnings


def test_043_invalid_code(linter, cases):
    """Invalid geographic code should warn."""
    record = cases["invalid_code"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    assert "043: Subfield a x-xx---, is not valid" in warnings


def test_043_invalid_code_wrong_pattern(linter, cases):
    """Code with wrong pattern should warn."""
    record = cases["invalid_code_wrong_pattern"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    assert "043: Subfield a nope123, is not valid" in warnings


def test_043_obsolete_code(linter, cases):
    """Obsolete geographic area code should warn about obsolescence."""
    record = cases["obsolete_code"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    assert "043: Subfield a e-ur-ai, may be obsolete" in warnings


def test_043_multiple_obsolete(linter, cases):
    """Multiple obsolete codes should all warn."""
    record = cases["multiple_obsolete"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    assert "043: Subfield a e-ur-kz, may be obsolete" in warnings
    assert "043: Subfield a e-ur-uz, may be obsolete" in warnings


def test_043_multiple_mixed_validity(linter, cases):
    """Multiple codes with mixed validity should warn only about invalid ones."""
    record = cases["multiple_mixed_validity"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    # Valid codes should not warn
    assert "043: Subfield a n-us---" not in warnings
    assert "043: Subfield a e-fr---" not in warnings
    # Invalid code should warn
    assert "043: Subfield a x-xx---, is not valid" in warnings


def test_043_with_other_subfields(linter, cases):
    """Non-'a' subfields should be ignored."""
    record = cases["with_other_subfields"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    # Valid $a should not warn
    assert "043: Subfield a n-us---" not in warnings
    # Other subfields should not cause warnings (they're ignored by check_043)
    assert "043: Subfield b" not in warnings
    assert "043: Subfield c" not in warnings


def test_043_comprehensive_smoke(linter, cases):
    """Comprehensive test with multiple valid codes."""
    record = cases["comprehensive_smoke"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    # All codes are valid, should have no 043 warnings
    assert "043: Subfield a" not in warnings
