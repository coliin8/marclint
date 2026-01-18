"""Pytest-based checks for 245-specific MarcLint behaviour.

These tests use synthetic MARC records from ``test_245_fixtures.make_245_cases``
to assert that the Python port flags the expected problems.
"""

from pytest import fixture

from pymarc import Record, Field, Subfield

from tests.conftest import create_minimal_record


@fixture
def cases():
    def create_record(fields: list[Field]) -> Record:
        """Generate synthetic MARC records with various 245 problems.

        Returns a dict of (n
        """
        return create_minimal_record(fields)

    cases = {}

    # 1. Missing subfield a, starts with b
    f1 = Field(
        tag="245",
        indicators=["1", "0"],
        subfields=[
            Subfield("b", "Something after a that doesn't exist /"),
            Subfield("c", "Someone."),
        ],
    )
    cases["case1_missing_a_starts_with_b"] = create_record([f1])

    # 2. Wrong first subfield (no $6, starts with $c)
    f2 = Field(
        tag="245",
        indicators=["1", "0"],
        subfields=[
            Subfield("c", "By Someone."),
        ],
    )
    cases["case2_starts_with_c"] = create_record([f2])

    # 3. With $6, but first after $6 is not $a
    f3 = Field(
        tag="245",
        indicators=["1", "0"],
        subfields=[
            Subfield("6", "245-01/$1"),
            Subfield("b", "Subtitle only /"),
            Subfield("c", "Author."),
        ],
    )
    cases["case3_has_6_then_b"] = create_record([f3])

    # 4. Final punctuation missing period
    f4 = Field(
        tag="245",
        indicators=["1", "0"],
        subfields=[
            Subfield("a", "A title without final period"),
        ],
    )
    cases["case4_no_final_period"] = create_record([f4])

    # 5. Final punctuation has question mark
    f5 = Field(
        tag="245",
        indicators=["1", "0"],
        subfields=[
            Subfield("a", "A title with a question mark?"),
        ],
    )
    cases["case5_final_question_mark"] = create_record([f5])

    # 6. $c not preceded by space+slash
    f6 = Field(
        tag="245",
        indicators=["1", "0"],
        subfields=[
            Subfield("a", "A title without slash"),
            Subfield("c", "By Someone."),
        ],
    )
    cases["case6_c_without_slash"] = create_record([f6])

    # 7. $b not preceded by space + colon/semicolon/equals
    f7 = Field(
        tag="245",
        indicators=["1", "0"],
        subfields=[
            Subfield("a", "A title, with comma"),
            Subfield("b", "Subtitle here."),
        ],
    )
    cases["case7_b_with_comma"] = create_record([f7])

    # 8. $h with space before it
    f8 = Field(
        tag="245",
        indicators=["1", "0"],
        subfields=[
            Subfield("a", "A title :"),
            Subfield("h", " [videorecording]"),
        ],
    )
    cases["case8_h_with_space_before"] = create_record([f8])

    # 9. $h without matching square brackets
    f9 = Field(
        tag="245",
        indicators=["1", "0"],
        subfields=[
            Subfield("a", "A title :"),
            Subfield("h", " videorecording"),
        ],
    )
    cases["case9_h_without_brackets"] = create_record([f9])

    # 10. $n not preceded by period
    f10 = Field(
        tag="245",
        indicators=["1", "0"],
        subfields=[
            Subfield("a", "Complete works, part"),
            Subfield("n", "3"),
        ],
    )

    cases["case10_n_without_period"] = create_record([f10])

    # 11. $p after $n but not preceded by comma
    f11 = Field(
        tag="245",
        indicators=["1", "0"],
        subfields=[
            Subfield("a", "Complete works."),
            Subfield("n", "3"),
            Subfield("p", "The title of part"),
        ],
    )
    cases["case11_p_after_n_without_comma"] = create_record([f11])

    # 12. $p without preceding $n and not preceded by period
    f12 = Field(
        tag="245",
        indicators=["1", "0"],
        subfields=[
            Subfield("a", "Complete works"),
            Subfield("p", "The title of part"),
        ],
    )
    cases["case12_p_without_n_and_period"] = create_record([f12])

    # 13. Non-numeric non-filing indicator with article "A"
    f13 = Field(
        tag="245",
        indicators=["1", "a"],
        subfields=[
            Subfield("a", "A title with alpha indicator."),
        ],
    )
    cases["case13_non_numeric_ind2"] = create_record([f13])

    # 14. Indicator 1 non-numeric
    f14 = Field(
        tag="245",
        indicators=["/", "2"],
        subfields=[
            Subfield("a", "A title with alpha indicator."),
        ],
    )
    cases["case14_non_numeric_ind1"] = create_record([f14])

    return cases


def test_245_cases_smoke(linter, cases):
    """Each synthetic 245 record should be processed without crashing."""
    for name, record in cases.items():
        linter.check_record(record)
        # Basic assertion: we at least produce a list of warnings
        assert isinstance(linter.warnings(), list)


def test_245_indicator_and_structure_examples(linter, cases):
    """Spot-check a few cases for specific expected warnings."""

    # Case 1: missing $a, starts with $b
    rec = cases["case1_missing_a_starts_with_b"]
    linter.check_record(rec)
    w = "\n".join(linter.warnings())
    assert "245: Must have a subfield _a." in w
    assert "245: First subfield must be _a, but it is _b" in w

    # Case 2: missing $a, starts with $c
    rec = cases["case2_starts_with_c"]
    linter.check_record(rec)
    w = "\n".join(linter.warnings())
    assert "245: Must have a subfield _a." in w
    assert "245: First subfield must be _a, but it is _c" in w

    # Case 3: has $6, but first after $6 is $b
    linter.check_record(cases["case3_has_6_then_b"])
    w = "\n".join(linter.warnings())
    assert "245: Must have a subfield _a." in w
    assert "245: First subfield after subfield _6 must be _a, but it is _b" in w
    assert (
        "245: Subfield _b should be preceded by space-colon, space-semicolon, or space-equals sign."
        in w
    )

    # Case 4: no final period
    linter.check_record(cases["case4_no_final_period"])
    w = "\n".join(linter.warnings())
    assert "245: Must end with . (period)." in w

    # Case 5: final question mark
    linter.check_record(cases["case5_final_question_mark"])
    w = "\n".join(linter.warnings())
    assert (
        "245: MARC21 allows ? or ! as final punctuation but LCRI 1.0C, Nov. 2003 (LCPS 1.7.1 for RDA records), requires period."
        in w
    )
    assert "245: First word, a, may be an article, check 2nd indicator (0)." in w

    # Case 6: $c without preceding space-slash
    linter.check_record(cases["case6_c_without_slash"])
    w = "\n".join(linter.warnings())
    assert "245: Subfield _c must be preceded by /" in w
    assert "245: First word, a, may be an article, check 2nd indicator (0)." in w

    # Case 7: $b with comma instead of space-colon
    linter.check_record(cases["case7_b_with_comma"])
    w = "\n".join(linter.warnings())
    assert "Subfield _b should be preceded by space-colon" in w

    # Case 8: $h with space before it
    linter.check_record(cases["case8_h_with_space_before"])
    w = "\n".join(linter.warnings())
    assert "245: Must end with . (period)." in w
    assert "245: Subfield _h must have matching square brackets, h." in w
    assert "245: First word, a, may be an article, check 2nd indicator (0)." in w

    # Case 9: $h without brackets
    linter.check_record(cases["case9_h_without_brackets"])
    w = "\n".join(linter.warnings())
    assert "245: Must end with . (period)." in w
    assert "245: Subfield _h must have matching square brackets, h." in w
    assert "245: First word, a, may be an article, check 2nd indicator (0)." in w

    # Case 10: $n without preceding period
    linter.check_record(cases["case10_n_without_period"])
    w = "\n".join(linter.warnings())
    assert "Subfield _n must be preceded by ." in w
    assert "Subfield _n should be preceded by space-comma" not in w
    assert "Subfield _p should be preceded by space-comma" not in w

    # Case 11: $p after $n but without preceding comma
    linter.check_record(cases["case11_p_after_n_without_comma"])
    w = "\n".join(linter.warnings())
    assert "Subfield _p must be preceded by ," in w
    assert "Subfield _p must be preceded by ." not in w
    assert "Subfield _n must be preceded by ." not in w

    # Case 12: $p without preceding $n and without preceding period
    linter.check_record(cases["case12_p_without_n_and_period"])
    w = "\n".join(linter.warnings())
    assert "Subfield _p must be preceded by ." in w
    assert "Subfield _p must be preceded by ," not in w
    assert "Subfield _n must be preceded by ." not in w
    assert "Subfield _n should be preceded by space-comma" not in w

    # Case 13: non-numeric non-filing indicator
    linter.check_record(cases["case13_non_numeric_ind2"])
    w = "\n".join(linter.warnings())
    assert "Non-filing indicator is non-numeric" in w

    # Case 14: non-numeric non-filing indicator
    linter.check_record(cases["case14_non_numeric_ind1"])
    w = "\n".join(linter.warnings())
    assert '245: Indicator 1 must be 0 or 1 but it\'s "/"' in w
