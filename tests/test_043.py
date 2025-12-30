"""Unit tests for check_043 (Geographic Area Code validation)."""

import pytest
from pymarc import Record, Field, Subfield


@pytest.fixture
def cases():
    """Test cases for 043 field validation."""
    return {
        # Valid cases
        "valid_single_code": Record(
            force_utf8=True,
            leader="00000nam  2200000   4500",
            fields=[
                Field(
                    tag="043",
                    indicators=[" ", " "],
                    subfields=[Subfield(code="a", value="n-us---")],
                )
            ],
        ),
        "valid_multiple_codes": Record(
            force_utf8=True,
            leader="00000nam  2200000   4500",
            fields=[
                Field(
                    tag="043",
                    indicators=[" ", " "],
                    subfields=[
                        Subfield(code="a", value="n-us---"),
                        Subfield(code="a", value="e-uk---"),
                    ],
                )
            ],
        ),
        "valid_us_state": Record(
            force_utf8=True,
            leader="00000nam  2200000   4500",
            fields=[
                Field(
                    tag="043",
                    indicators=[" ", " "],
                    subfields=[Subfield(code="a", value="n-us-ca")],
                )
            ],
        ),
        "valid_asia": Record(
            force_utf8=True,
            leader="00000nam  2200000   4500",
            fields=[
                Field(
                    tag="043",
                    indicators=[" ", " "],
                    subfields=[Subfield(code="a", value="a-ja---")],
                )
            ],
        ),
        "valid_europe": Record(
            force_utf8=True,
            leader="00000nam  2200000   4500",
            fields=[
                Field(
                    tag="043",
                    indicators=[" ", " "],
                    subfields=[Subfield(code="a", value="e-fr---")],
                )
            ],
        ),
        # Invalid length cases
        "invalid_length_short": Record(
            force_utf8=True,
            leader="00000nam  2200000   4500",
            fields=[
                Field(
                    tag="043",
                    indicators=[" ", " "],
                    subfields=[Subfield(code="a", value="n-us")],
                )
            ],
        ),
        "invalid_length_long": Record(
            force_utf8=True,
            leader="00000nam  2200000   4500",
            fields=[
                Field(
                    tag="043",
                    indicators=[" ", " "],
                    subfields=[Subfield(code="a", value="n-us----")],
                )
            ],
        ),
        "invalid_length_empty": Record(
            force_utf8=True,
            leader="00000nam  2200000   4500",
            fields=[
                Field(
                    tag="043",
                    indicators=[" ", " "],
                    subfields=[Subfield(code="a", value="")],
                )
            ],
        ),
        # Invalid code cases
        "invalid_code": Record(
            force_utf8=True,
            leader="00000nam  2200000   4500",
            fields=[
                Field(
                    tag="043",
                    indicators=[" ", " "],
                    subfields=[Subfield(code="a", value="x-xx---")],
                )
            ],
        ),
        "invalid_code_wrong_pattern": Record(
            force_utf8=True,
            leader="00000nam  2200000   4500",
            fields=[
                Field(
                    tag="043",
                    indicators=[" ", " "],
                    subfields=[Subfield(code="a", value="nope123")],
                )
            ],
        ),
        # Obsolete geographic area code (e.g., Soviet republics)
        "obsolete_code": Record(
            force_utf8=True,
            leader="00000nam  2200000   4500",
            fields=[
                Field(
                    tag="043",
                    indicators=[" ", " "],
                    subfields=[
                        Subfield(code="a", value="e-ur-ai")
                    ],  # Armenia (USSR), obsolete
                )
            ],
        ),
        # Multiple obsolete codes
        "multiple_obsolete": Record(
            force_utf8=True,
            leader="00000nam  2200000   4500",
            fields=[
                Field(
                    tag="043",
                    indicators=[" ", " "],
                    subfields=[
                        Subfield(
                            code="a", value="e-ur-kz"
                        ),  # Kazakhstan (USSR), obsolete
                        Subfield(
                            code="a", value="e-ur-uz"
                        ),  # Uzbekistan (USSR), obsolete
                    ],
                )
            ],
        ),
        # Multiple subfields mixed validity
        "multiple_mixed_validity": Record(
            force_utf8=True,
            leader="00000nam  2200000   4500",
            fields=[
                Field(
                    tag="043",
                    indicators=[" ", " "],
                    subfields=[
                        Subfield(code="a", value="n-us---"),  # Valid
                        Subfield(code="a", value="x-xx---"),  # Invalid
                        Subfield(code="a", value="e-fr---"),  # Valid
                    ],
                )
            ],
        ),
        # Other subfields (should be ignored by check_043)
        "with_other_subfields": Record(
            force_utf8=True,
            leader="00000nam  2200000   4500",
            fields=[
                Field(
                    tag="043",
                    indicators=[" ", " "],
                    subfields=[
                        Subfield(code="a", value="n-us---"),
                        Subfield(code="b", value="Some other data"),  # Ignored
                        Subfield(code="c", value="More data"),  # Ignored
                    ],
                )
            ],
        ),
        # Comprehensive smoke test
        "comprehensive_smoke": Record(
            force_utf8=True,
            leader="00000nam  2200000   4500",
            fields=[
                Field(
                    tag="043",
                    indicators=[" ", " "],
                    subfields=[
                        Subfield(code="a", value="n-us---"),
                        Subfield(code="a", value="n-us-ny"),
                        Subfield(code="a", value="e-uk---"),
                        Subfield(code="a", value="a-ja---"),
                    ],
                )
            ],
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
    # All codes are valid, should only see the 245 warning
    assert "043: Subfield a" not in warnings
    assert "245: No 245 tag" in warnings
