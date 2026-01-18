"""Unit tests for article validation in various title fields (130, 240, 440, 630, 730, 830)."""

import pytest
from pymarc import Record, Field, Subfield

from marc_lint.linter import MarcLint


def make_008(lang: str = "eng") -> Field:
    """Create an 008 field with the specified language code at positions 35-37.

    The 008 field is 40 characters. Language is at positions 35-37 (0-indexed).
    """
    # Positions: 00-05 date, 06 type, 07-10 date1, 11-14 date2, 15-17 country,
    # 18-34 material specific, 35-37 language, 38 modified, 39 cat source
    data = "230101s2023    xxu           000 0 " + lang + " d"
    return Field(tag="008", data=data)


@pytest.fixture
def linter():
    """Provide a fresh MarcLint instance for each test."""
    return MarcLint()


@pytest.fixture
def cases():
    """Test cases for article validation in different title fields."""
    return {
        # 130 - Main Entry-Uniform Title (indicator 1)
        "130_valid_with_article": Record(
            force_utf8=True,
            leader="00000nam  2200000   4500",
            fields=[
                make_008("eng"),
                Field(
                    tag="130",
                    indicators=["4", " "],  # Correct for "The "
                    subfields=[Subfield(code="a", value="The great book.")],
                ),
                Field(
                    tag="245",
                    indicators=["1", "0"],
                    subfields=[Subfield(code="a", value="Title.")],
                ),
            ],
        ),
        "130_invalid_indicator": Record(
            force_utf8=True,
            leader="00000nam  2200000   4500",
            fields=[
                make_008("eng"),
                Field(
                    tag="130",
                    indicators=["0", " "],  # Should be 4 for "The "
                    subfields=[Subfield(code="a", value="The great book.")],
                ),
                Field(
                    tag="245",
                    indicators=["1", "0"],
                    subfields=[Subfield(code="a", value="Title.")],
                ),
            ],
        ),
        "130_valid_no_article": Record(
            force_utf8=True,
            leader="00000nam  2200000   4500",
            fields=[
                make_008("eng"),
                Field(
                    tag="130",
                    indicators=["0", " "],  # Correct for no article
                    subfields=[Subfield(code="a", value="Great book.")],
                ),
                Field(
                    tag="245",
                    indicators=["1", "0"],
                    subfields=[Subfield(code="a", value="Title.")],
                ),
            ],
        ),
        # 240 - Uniform Title (indicator 2)
        "240_valid_with_article": Record(
            force_utf8=True,
            leader="00000nam  2200000   4500",
            fields=[
                make_008("eng"),
                Field(
                    tag="245",
                    indicators=["1", "0"],
                    subfields=[Subfield(code="a", value="Title.")],
                ),
                Field(
                    tag="240",
                    indicators=["1", "4"],  # Correct for "The "
                    subfields=[Subfield(code="a", value="The original title.")],
                ),
            ],
        ),
        "240_invalid_indicator": Record(
            force_utf8=True,
            leader="00000nam  2200000   4500",
            fields=[
                make_008("eng"),
                Field(
                    tag="245",
                    indicators=["1", "0"],
                    subfields=[Subfield(code="a", value="Title.")],
                ),
                Field(
                    tag="240",
                    indicators=["1", "0"],  # Should be 4 for "The "
                    subfields=[Subfield(code="a", value="The original title.")],
                ),
            ],
        ),
        # Note: 440 is obsolete and not in field rules, so it won't be validated
        # 630 - Subject Added Entry-Uniform Title (indicator 1)
        "630_valid_with_article": Record(
            force_utf8=True,
            leader="00000nam  2200000   4500",
            fields=[
                make_008("eng"),
                Field(
                    tag="245",
                    indicators=["1", "0"],
                    subfields=[Subfield(code="a", value="Title.")],
                ),
                Field(
                    tag="630",
                    indicators=["4", "0"],  # Correct for "The "
                    subfields=[Subfield(code="a", value="The Bible.")],
                ),
            ],
        ),
        "630_invalid_indicator": Record(
            force_utf8=True,
            leader="00000nam  2200000   4500",
            fields=[
                make_008("eng"),
                Field(
                    tag="245",
                    indicators=["1", "0"],
                    subfields=[Subfield(code="a", value="Title.")],
                ),
                Field(
                    tag="630",
                    indicators=["0", "0"],  # Should be 4 for "The "
                    subfields=[Subfield(code="a", value="The Bible.")],
                ),
            ],
        ),
        # 730 - Added Entry-Uniform Title (indicator 1)
        "730_valid_with_article": Record(
            force_utf8=True,
            leader="00000nam  2200000   4500",
            fields=[
                make_008("ger"),  # German for "Das"
                Field(
                    tag="245",
                    indicators=["1", "0"],
                    subfields=[Subfield(code="a", value="Title.")],
                ),
                Field(
                    tag="730",
                    indicators=["4", " "],  # Correct for "Das "
                    subfields=[Subfield(code="a", value="Das Kapital.")],
                ),
            ],
        ),
        "730_invalid_indicator": Record(
            force_utf8=True,
            leader="00000nam  2200000   4500",
            fields=[
                make_008("ger"),  # German for "Das"
                Field(
                    tag="245",
                    indicators=["1", "0"],
                    subfields=[Subfield(code="a", value="Title.")],
                ),
                Field(
                    tag="730",
                    indicators=["0", " "],  # Should be 4 for "Das "
                    subfields=[Subfield(code="a", value="Das Kapital.")],
                ),
            ],
        ),
        # 830 - Series Added Entry-Uniform Title (indicator 2)
        "830_valid_with_article": Record(
            force_utf8=True,
            leader="00000nam  2200000   4500",
            fields=[
                make_008("fre"),  # French for "Le"
                Field(
                    tag="245",
                    indicators=["1", "0"],
                    subfields=[Subfield(code="a", value="Title.")],
                ),
                Field(
                    tag="830",
                    indicators=[" ", "3"],  # Correct for "Le "
                    subfields=[Subfield(code="a", value="Le series.")],
                ),
            ],
        ),
        "830_invalid_indicator": Record(
            force_utf8=True,
            leader="00000nam  2200000   4500",
            fields=[
                make_008("fre"),  # French for "Le"
                Field(
                    tag="245",
                    indicators=["1", "0"],
                    subfields=[Subfield(code="a", value="Title.")],
                ),
                Field(
                    tag="830",
                    indicators=[" ", "0"],  # Should be 3 for "Le "
                    subfields=[Subfield(code="a", value="Le series.")],
                ),
            ],
        ),
        # Multiple language articles
        "multiple_language_articles": Record(
            force_utf8=True,
            leader="00000nam  2200000   4500",
            fields=[
                make_008("spa"),  # Spanish - covers "La" and "Los"
                Field(
                    tag="245",
                    indicators=["1", "3"],  # Correct for "La "
                    subfields=[Subfield(code="a", value="La vida es bella.")],
                ),
                Field(
                    tag="730",
                    indicators=["4", " "],  # Correct for "Los "
                    subfields=[Subfield(code="a", value="Los miserables.")],
                ),
                Field(
                    tag="830",
                    indicators=[" ", "5"],  # Correct for "Eine " - but won't match spa
                    subfields=[Subfield(code="a", value="Eine kleine series.")],
                ),
            ],
        ),
        # No article should have indicator 0
        "no_article_indicator_nonzero": Record(
            force_utf8=True,
            leader="00000nam  2200000   4500",
            fields=[
                make_008("eng"),
                Field(
                    tag="245",
                    indicators=["1", "0"],
                    subfields=[Subfield(code="a", value="Title.")],
                ),
                Field(
                    tag="730",
                    indicators=["4", " "],  # Should be 0 for no article
                    subfields=[Subfield(code="a", value="Book of hours.")],
                ),
            ],
        ),
        # Comprehensive test
        "comprehensive_all_fields": Record(
            force_utf8=True,
            leader="00000nam  2200000   4500",
            fields=[
                make_008("eng"),  # English for "The"
                Field(
                    tag="130",
                    indicators=["4", " "],
                    subfields=[Subfield(code="a", value="The works.")],
                ),
                Field(
                    tag="240",
                    indicators=["1", "4"],  # "Los " = 4 chars - but won't match eng
                    subfields=[Subfield(code="a", value="Los cuentos.")],
                ),
                Field(
                    tag="245",
                    indicators=["1", "4"],
                    subfields=[Subfield(code="a", value="The complete stories.")],
                ),
                Field(
                    tag="630",
                    indicators=["4", "0"],
                    subfields=[Subfield(code="a", value="The Koran.")],
                ),
                Field(
                    tag="730",
                    indicators=["3", " "],  # "Le " - but won't match eng
                    subfields=[Subfield(code="a", value="Le morte d'Arthur.")],
                ),
                Field(
                    tag="830",
                    indicators=[" ", "4"],
                    subfields=[Subfield(code="a", value="The classics series.")],
                ),
            ],
        ),
        # Language not in ARTICLES - should not judge indicator
        # "Die" is an article in German, but this record is Japanese
        # We should NOT warn regardless of indicator value
        "language_not_in_articles_nonzero_indicator": Record(
            force_utf8=True,
            leader="00000nam  2200000   4500",
            fields=[
                make_008("jpn"),  # Japanese - not in any article's language list
                Field(
                    tag="245",
                    indicators=["1", "4"],  # Non-zero indicator, but shouldn't warn
                    subfields=[Subfield(code="a", value="Die Hard.")],
                ),
            ],
        ),
        "language_not_in_articles_zero_indicator": Record(
            force_utf8=True,
            leader="00000nam  2200000   4500",
            fields=[
                make_008("jpn"),  # Japanese - not in any article's language list
                Field(
                    tag="245",
                    indicators=["1", "0"],  # Zero indicator, shouldn't warn either
                    subfields=[Subfield(code="a", value="Die Hard.")],
                ),
            ],
        ),
        # Article word in different language record - "Die" is German article
        # but record is English, so should not be treated as article
        "article_word_different_language": Record(
            force_utf8=True,
            leader="00000nam  2200000   4500",
            fields=[
                make_008("eng"),  # English - "die" is not an English article
                Field(
                    tag="245",
                    indicators=[
                        "1",
                        "0",
                    ],  # Zero is correct - "Die" isn't article in English
                    subfields=[Subfield(code="a", value="Die Hard.")],
                ),
            ],
        ),
        "article_word_different_language_wrong_indicator": Record(
            force_utf8=True,
            leader="00000nam  2200000   4500",
            fields=[
                make_008("eng"),  # English - "die" is not an English article
                Field(
                    tag="245",
                    indicators=[
                        "1",
                        "4",
                    ],  # Non-zero but "Die" isn't article in English
                    subfields=[Subfield(code="a", value="Die Hard.")],
                ),
            ],
        ),
    }


# 130 Tests
def test_130_valid_with_article(linter, cases):
    """130 with correct non-filing indicator for article should not warn."""
    record = cases["130_valid_with_article"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    assert (
        "130:" not in warnings
        or "130:" in warnings
        and "article" not in warnings.lower()
    )


def test_130_invalid_indicator(linter, cases):
    """130 with incorrect non-filing indicator should warn."""
    record = cases["130_invalid_indicator"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    assert (
        "130: First word, the, may be an article, check 1st indicator (0)" in warnings
    )


def test_130_valid_no_article(linter, cases):
    """130 without article and indicator 0 should not warn."""
    record = cases["130_valid_no_article"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    assert (
        "130:" not in warnings
        or "130:" in warnings
        and "article" not in warnings.lower()
    )


# 240 Tests
def test_240_valid_with_article(linter, cases):
    """240 with correct non-filing indicator for article should not warn."""
    record = cases["240_valid_with_article"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    assert (
        "240:" not in warnings
        or "240:" in warnings
        and "article" not in warnings.lower()
    )


def test_240_invalid_indicator(linter, cases):
    """240 with incorrect non-filing indicator should warn."""
    record = cases["240_invalid_indicator"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    assert (
        "240: First word, the, may be an article, check 2nd indicator (0)" in warnings
    )


# 630 Tests
def test_630_valid_with_article(linter, cases):
    """630 with correct non-filing indicator for article should not warn."""
    record = cases["630_valid_with_article"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    assert (
        "630:" not in warnings
        or "630:" in warnings
        and "article" not in warnings.lower()
    )


def test_630_invalid_indicator(linter, cases):
    """630 with incorrect non-filing indicator should warn."""
    record = cases["630_invalid_indicator"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    assert (
        "630: First word, the, may be an article, check 1st indicator (0)" in warnings
    )


# 730 Tests
def test_730_valid_with_article(linter, cases):
    """730 with correct non-filing indicator for article should not warn."""
    record = cases["730_valid_with_article"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    assert (
        "730:" not in warnings
        or "730:" in warnings
        and "article" not in warnings.lower()
    )


def test_730_invalid_indicator(linter, cases):
    """730 with incorrect non-filing indicator should warn."""
    record = cases["730_invalid_indicator"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    assert (
        "730: First word, das, may be an article, check 1st indicator (0)" in warnings
    )


# 830 Tests
def test_830_valid_with_article(linter, cases):
    """830 with correct non-filing indicator for article should not warn."""
    record = cases["830_valid_with_article"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    assert (
        "830:" not in warnings
        or "830:" in warnings
        and "article" not in warnings.lower()
    )


def test_830_invalid_indicator(linter, cases):
    """830 with incorrect non-filing indicator should warn."""
    record = cases["830_invalid_indicator"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    assert "830: First word, le, may be an article, check 2nd indicator (0)" in warnings


# Multiple language tests
def test_multiple_language_articles(linter, cases):
    """Multiple fields with different language articles should validate correctly."""
    record = cases["multiple_language_articles"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    # All indicators are correct, should not have article warnings
    assert "may be an article" not in warnings


def test_no_article_indicator_nonzero(linter, cases):
    """Field without article but non-zero indicator should warn."""
    record = cases["no_article_indicator_nonzero"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    assert (
        "730: First word, book, does not appear to be an article, check 1st indicator (4)"
        in warnings
    )


def test_comprehensive_all_fields(linter, cases):
    """Comprehensive test with all article fields correctly set."""
    record = cases["comprehensive_all_fields"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    # All fields have correct indicators
    assert "may be an article" not in warnings


# Language not in ARTICLES tests - should not make judgments
def test_language_not_in_articles_nonzero_indicator(linter, cases):
    """Record with language not in ARTICLES should not warn about article indicators.

    'Die' is a German article, but this record is Japanese. Since Japanese
    is not in any article's language list, we should not judge the indicator.
    """
    record = cases["language_not_in_articles_nonzero_indicator"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    # Should NOT warn about "die" being an article or indicator being wrong
    assert "article" not in warnings.lower()
    assert "die" not in warnings.lower()


def test_language_not_in_articles_zero_indicator(linter, cases):
    """Record with language not in ARTICLES and zero indicator should not warn."""
    record = cases["language_not_in_articles_zero_indicator"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    # Should NOT warn - we don't judge when language isn't in ARTICLES
    assert "article" not in warnings.lower()
    assert "die" not in warnings.lower()


def test_article_word_different_language(linter, cases):
    """Article word in a language where it's NOT an article should not warn.

    'Die' is a German article but this is an English record.
    Indicator 0 is correct because 'die' is not an English article.
    """
    record = cases["article_word_different_language"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    # Should NOT warn - "die" is not an article in English
    assert "article" not in warnings.lower()


def test_article_word_different_language_wrong_indicator(linter, cases):
    """Article word with wrong indicator in a language where it's NOT an article.

    'Die' is a German article but this is an English record with indicator 4.
    Should warn that 'die' does not appear to be an article (in English).
    """
    record = cases["article_word_different_language_wrong_indicator"]
    linter.check_record(record)
    warnings = "\n".join(linter.warnings())
    # SHOULD warn that indicator should be 0 since "die" is not an English article
    assert "does not appear to be an article" in warnings
