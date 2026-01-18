"""Pytest-based checks for 880 (Alternate Graphic Representation) field validation.

These tests verify that the Python port correctly handles 880 fields according to
the current implementation in linter.py, which:
- Checks for presence of $6 subfield
- Inherits validation rules from the linked field (first 3 chars of $6)
- Tracks repeatability separately for 880.XXX combinations
"""

from pytest import fixture
from pymarc import Record, Field, Subfield

from tests.conftest import create_minimal_record


@fixture
def cases():
    """Generate synthetic MARC records with various 880 scenarios."""

    def create_record(fields: list[Field]) -> Record:
        """Helper to build a Record from a list of fields."""
        return create_minimal_record(fields)

    cases = {}

    # Case 1: 880 without $6 subfield (should warn)
    f1 = Field(
        tag="880",
        indicators=["1", "0"],
        subfields=[
            Subfield("a", "Title in alternate script"),
        ],
    )
    cases["missing_subfield_6"] = create_record([f1])

    # Case 2: 880 with valid $6 linking to 245
    f2a = Field(
        tag="245",
        indicators=["1", "0"],
        subfields=[
            Subfield("6", "880-01"),
            Subfield("a", "English title."),
        ],
    )
    f2b = Field(
        tag="880",
        indicators=["1", "0"],
        subfields=[
            Subfield("6", "245-01/$1"),
            Subfield("a", "Non-Latin script title."),
        ],
    )
    cases["valid_245_880_pair"] = create_record([f2a, f2b])

    # Case 3: 880 with valid $6 linking to 100
    f3a = Field(
        tag="100",
        indicators=["1", " "],
        subfields=[
            Subfield("6", "880-01"),
            Subfield("a", "Author, Latin."),
        ],
    )
    f3b = Field(
        tag="880",
        indicators=["1", " "],
        subfields=[
            Subfield("6", "100-01/$1"),
            Subfield("a", "Author in alternate script."),
        ],
    )
    cases["valid_100_880_pair"] = create_record([f3a, f3b])

    # Case 4: Multiple 880s linking to different fields (should be allowed)
    f4a = Field(
        tag="245",
        indicators=["1", "0"],
        subfields=[
            Subfield("6", "880-01"),
            Subfield("a", "Title."),
        ],
    )
    f4b = Field(
        tag="880",
        indicators=["1", "0"],
        subfields=[
            Subfield("6", "245-01/$1"),
            Subfield("a", "Title alternate."),
        ],
    )
    f4c = Field(
        tag="100",
        indicators=["1", " "],
        subfields=[
            Subfield("6", "880-02"),
            Subfield("a", "Author."),
        ],
    )
    f4d = Field(
        tag="880",
        indicators=["1", " "],
        subfields=[
            Subfield("6", "100-02/$1"),
            Subfield("a", "Author alternate."),
        ],
    )
    cases["multiple_880s_different_links"] = create_record([f4a, f4b, f4c, f4d])

    # Case 5: Multiple 880s linking to same non-repeatable field (e.g., 245)
    # According to current code, this should warn about non-repeatability
    f5a = Field(
        tag="245",
        indicators=["1", "0"],
        subfields=[
            Subfield("a", "Title."),
        ],
    )
    f5b = Field(
        tag="880",
        indicators=["1", "0"],
        subfields=[
            Subfield("6", "245-01/$1"),
            Subfield("a", "First alternate."),
        ],
    )
    f5c = Field(
        tag="880",
        indicators=["1", "0"],
        subfields=[
            Subfield("6", "245-02/$1"),
            Subfield("a", "Second alternate."),
        ],
    )
    cases["multiple_880s_same_nonrepeatable"] = create_record([f5a, f5b, f5c])

    # Case 6: 880 with $6 linking to repeatable field (e.g., 650)
    f6a = Field(
        tag="650",
        indicators=[" ", "0"],
        subfields=[
            Subfield("6", "880-01"),
            Subfield("a", "Subject heading."),
        ],
    )
    f6b = Field(
        tag="880",
        indicators=[" ", "0"],
        subfields=[
            Subfield("6", "650-01/$1"),
            Subfield("a", "Subject in alternate script."),
        ],
    )
    f6c = Field(
        tag="650",
        indicators=[" ", "0"],
        subfields=[
            Subfield("6", "880-02"),
            Subfield("a", "Another subject."),
        ],
    )
    f6d = Field(
        tag="880",
        indicators=[" ", "0"],
        subfields=[
            Subfield("6", "650-02/$1"),
            Subfield("a", "Another subject alternate."),
        ],
    )
    cases["multiple_880s_repeatable_field"] = create_record([f6a, f6b, f6c, f6d])

    # Case 7: 880 with invalid indicator (inherits 245 rules)
    f7 = Field(
        tag="880",
        indicators=["x", "0"],
        subfields=[
            Subfield("6", "245-01/$1"),
            Subfield("a", "Title with bad indicator."),
        ],
    )
    cases["880_invalid_indicator"] = create_record([f7])

    # Case 8: 880 with invalid subfield (inherits 245 rules)
    f8 = Field(
        tag="880",
        indicators=["1", "0"],
        subfields=[
            Subfield("6", "245-01/$1"),
            Subfield("a", "Title."),
            Subfield("z", "Invalid subfield for 245."),
        ],
    )
    cases["880_invalid_subfield"] = create_record([f8])

    # Case 9: 880 linking to field with no rules defined (should not crash)
    f9 = Field(
        tag="880",
        indicators=["1", "0"],
        subfields=[
            Subfield("6", "999-01/$1"),
            Subfield("a", "Some local field."),
        ],
    )
    cases["880_links_to_undefined_field"] = create_record([f9])

    # Case 10: 880 with malformed $6 (too short)
    f10 = Field(
        tag="880",
        indicators=["1", "0"],
        subfields=[
            Subfield("6", "24"),  # Less than 3 characters
            Subfield("a", "Title."),
        ],
    )
    cases["880_malformed_subfield_6"] = create_record([f10])

    # Case 11: 880 with 245 rules - missing $a (should inherit 245 validation)
    f11 = Field(
        tag="880",
        indicators=["1", "0"],
        subfields=[
            Subfield("6", "245-01/$1"),
            Subfield("b", "Subtitle without title."),
        ],
    )
    cases["880_245_missing_a"] = create_record([f11])

    # Case 12: 880 with 245 rules - valid structure
    f12 = Field(
        tag="880",
        indicators=["1", "0"],
        subfields=[
            Subfield("6", "245-01/$1"),
            Subfield("a", "Title :"),
            Subfield("b", "subtitle /"),
            Subfield("c", "author."),
        ],
    )
    cases["880_245_valid_structure"] = create_record([f12])

    return cases


def test_880_missing_subfield_6(linter, cases):
    """880 without $6 should produce a warning."""
    record = cases["missing_subfield_6"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    assert "880[1]: No subfield 6." in warnings


def test_880_valid_245_pair(linter, cases):
    """Valid 880 linked to 245 should not produce 880-specific warnings."""
    record = cases["valid_245_880_pair"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    # Should not warn about missing $6
    assert "880: No subfield 6." not in warnings
    # May have 245-specific warnings, but no 880 structural issues


def test_880_valid_100_pair(linter, cases):
    """Valid 880 linked to 100 should not produce 880-specific warnings."""
    record = cases["valid_100_880_pair"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    assert "880: No subfield 6." not in warnings


def test_880_multiple_different_links(linter, cases):
    """Multiple 880s linking to different fields should be allowed."""
    record = cases["multiple_880s_different_links"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    # Should not warn about 880 missing $6
    assert "880: No subfield 6." not in warnings
    # Multiple 880s with different linked fields should not cause repeatability warnings


def test_880_multiple_same_nonrepeatable(linter, cases):
    """Multiple 880s linking to same non-repeatable field should warn."""
    record = cases["multiple_880s_same_nonrepeatable"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    # Should warn about non-repeatability for 245
    assert "245[2]: Field is not repeatable." in warnings


def test_880_multiple_repeatable_field(linter, cases):
    """Multiple 880s linking to repeatable field should be allowed."""
    record = cases["multiple_880s_repeatable_field"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    # Should not warn about repeatability for 650
    assert "650: Field is not repeatable." not in warnings


def test_880_invalid_indicator(linter, cases):
    """880 with invalid indicator should inherit validation from linked field."""
    record = cases["880_invalid_indicator"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    # Should validate indicators according to 245 rules
    assert "245: Indicator 1 must be" in warnings


def test_880_invalid_subfield(linter, cases):
    """880 with invalid subfield should inherit validation from linked field."""
    record = cases["880_invalid_subfield"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    # Should warn about invalid subfield _z for 245
    assert "245: Subfield _z is not allowed." in warnings


def test_880_links_to_undefined_field(linter, cases):
    """880 linking to field with no rules should not crash."""
    record = cases["880_links_to_undefined_field"]
    linter.check_record(record)
    # Should complete without crashing
    warnings = linter.warnings()
    assert isinstance(warnings, list)


def test_880_malformed_subfield_6(linter, cases):
    """880 with malformed $6 (too short) should handle gracefully."""
    record = cases["880_malformed_subfield_6"]
    linter.check_record(record)
    warnings = linter.warnings()
    # Should complete without crashing, may not apply linked field rules
    assert isinstance(warnings, list)


def test_880_245_missing_a(linter, cases):
    """880 linked to 245 should inherit 245's requirement for $a."""
    record = cases["880_245_missing_a"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    # Should apply 245-specific check_245 validation
    assert "245: Must have a subfield _a." in warnings


def test_880_245_valid_structure(linter, cases):
    """880 with valid 245 structure should pass validation."""
    record = cases["880_245_valid_structure"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    # Should not produce structural warnings
    assert "880: No subfield 6." not in warnings
    # Note: May have punctuation warnings from 245 checks, depending on content


def test_880_comprehensive_smoke(linter, cases):
    """All 880 test cases should process without crashing."""
    for name, record in cases.items():
        linter.clear_warnings()
        linter.check_record(record)
        # Basic assertion: we get a list of warnings
        assert isinstance(linter.warnings(), list)
