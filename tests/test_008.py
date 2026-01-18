"""Tests for 008 control field validation."""

from pytest import fixture
from pymarc import Record, Field, Subfield


@fixture
def make_record():
    """Factory to create records with custom 008 fields."""

    def _make(field_008_data: str) -> Record:
        r = Record()
        r.leader = "00000nam a2200000 i 4500"
        r.add_field(Field(tag="001", data="test001"))
        r.add_field(Field(tag="008", data=field_008_data))
        r.add_field(
            Field(
                tag="245",
                indicators=["0", "0"],
                subfields=[Subfield("a", "Test title.")],
            )
        )
        return r

    return _make


class TestField008Validation:
    """Tests for check_008 method."""

    def test_valid_008(self, linter, make_record):
        """Valid 008 field should produce no 008 warnings."""
        # Standard valid 008
        record = make_record("240101s2024    xxu           000 0 eng d")
        linter.check_record(record)
        field_008_warnings = [w for w in linter._warnings if w.field == "008"]
        assert len(field_008_warnings) == 0

    def test_short_008(self, linter, make_record):
        """008 field shorter than 40 characters should warn."""
        record = make_record("240101s2024")  # Too short
        linter.check_record(record)
        field_008_warnings = [w for w in linter._warnings if w.field == "008"]
        assert len(field_008_warnings) >= 1
        assert any("40 characters" in w.message for w in field_008_warnings)

    def test_invalid_type_of_date(self, linter, make_record):
        """Invalid type of date at position 06 should warn."""
        # 'x' is not a valid type of date
        record = make_record("240101x2024    xxu           000 0 eng d")
        linter.check_record(record)
        field_008_warnings = [w for w in linter._warnings if w.field == "008"]
        assert any("type of date" in w.message.lower() for w in field_008_warnings)

    def test_valid_types_of_date(self, linter, make_record):
        """All valid type of date values should pass."""
        valid_types = [
            "b",
            "c",
            "d",
            "e",
            "i",
            "k",
            "m",
            "n",
            "p",
            "q",
            "r",
            "s",
            "t",
            "u",
            "|",
        ]
        for date_type in valid_types:
            data = f"240101{date_type}2024    xxu           000 0 eng d"
            record = make_record(data)
            linter.check_record(record)
            field_008_warnings = [w for w in linter._warnings if w.field == "008"]
            type_warnings = [
                w for w in field_008_warnings if "type of date" in w.message.lower()
            ]
            assert len(type_warnings) == 0, f"Date type '{date_type}' should be valid"

    def test_invalid_date1(self, linter, make_record):
        """Invalid Date 1 at positions 07-10 should warn."""
        # 'abcd' is not a valid date
        record = make_record("240101sabcd    xxu           000 0 eng d")
        linter.check_record(record)
        field_008_warnings = [w for w in linter._warnings if w.field == "008"]
        assert any("Date 1" in w.message for w in field_008_warnings)

    def test_valid_date_formats(self, linter, make_record):
        """Valid date formats should pass."""
        valid_dates = ["2024", "19uu", "199u", "    ", "||||", "uuuu"]
        for date in valid_dates:
            # Positions 07-10 (Date 1)
            data = f"240101s{date}    xxu           000 0 eng d"
            record = make_record(data)
            linter.check_record(record)
            field_008_warnings = [w for w in linter._warnings if w.field == "008"]
            date_warnings = [w for w in field_008_warnings if "Date 1" in w.message]
            assert len(date_warnings) == 0, f"Date '{date}' should be valid"

    def test_invalid_country_code(self, linter, make_record):
        """Invalid country code at positions 15-17 should warn."""
        # 'zzz' is not a valid country code
        record = make_record("240101s2024    zzz           000 0 eng d")
        linter.check_record(record)
        field_008_warnings = [w for w in linter._warnings if w.field == "008"]
        assert any("country code" in w.message.lower() for w in field_008_warnings)

    def test_valid_country_code(self, linter, make_record):
        """Valid country code should pass."""
        record = make_record("240101s2024    nyu           000 0 eng d")
        linter.check_record(record)
        field_008_warnings = [w for w in linter._warnings if w.field == "008"]
        country_warnings = [
            w for w in field_008_warnings if "country code" in w.message.lower()
        ]
        assert len(country_warnings) == 0

    def test_obsolete_country_code(self, linter, make_record):
        """Obsolete country code should warn as obsolete."""
        # 'cs ' is obsolete (Czechoslovakia)
        record = make_record("240101s2024    cs            000 0 eng d")
        linter.check_record(record)
        field_008_warnings = [w for w in linter._warnings if w.field == "008"]
        obsolete_warnings = [
            w
            for w in field_008_warnings
            if "obsolete" in w.message.lower() and "country" in w.message.lower()
        ]
        assert len(obsolete_warnings) == 1

    def test_invalid_language_code(self, linter, make_record):
        """Invalid language code at positions 35-37 should warn."""
        # 'zzz' is not a valid language code
        record = make_record("240101s2024    xxu           000 0 zzz d")
        linter.check_record(record)
        field_008_warnings = [w for w in linter._warnings if w.field == "008"]
        assert any("language code" in w.message.lower() for w in field_008_warnings)

    def test_valid_language_code(self, linter, make_record):
        """Valid language code should pass."""
        record = make_record("240101s2024    xxu           000 0 fre d")
        linter.check_record(record)
        field_008_warnings = [w for w in linter._warnings if w.field == "008"]
        lang_warnings = [
            w for w in field_008_warnings if "language code" in w.message.lower()
        ]
        assert len(lang_warnings) == 0

    def test_obsolete_language_code(self, linter, make_record):
        """Obsolete language code should warn as obsolete."""
        # 'esk' is obsolete (Eskimo)
        record = make_record("240101s2024    xxu           000 0 esk d")
        linter.check_record(record)
        field_008_warnings = [w for w in linter._warnings if w.field == "008"]
        obsolete_warnings = [
            w
            for w in field_008_warnings
            if "obsolete" in w.message.lower() and "language" in w.message.lower()
        ]
        assert len(obsolete_warnings) == 1

    def test_invalid_modified_record(self, linter, make_record):
        """Invalid modified record indicator at position 38 should warn."""
        # 'z' is not valid for modified record
        record = make_record("240101s2024    xxu           000 0 engzd")
        linter.check_record(record)
        field_008_warnings = [w for w in linter._warnings if w.field == "008"]
        assert any("modified record" in w.message.lower() for w in field_008_warnings)

    def test_invalid_cataloging_source(self, linter, make_record):
        """Invalid cataloging source at position 39 should warn."""
        # 'z' is not valid for cataloging source
        record = make_record("240101s2024    xxu           000 0 eng z")
        linter.check_record(record)
        field_008_warnings = [w for w in linter._warnings if w.field == "008"]
        assert any("cataloging source" in w.message.lower() for w in field_008_warnings)

    def test_blanks_allowed(self, linter, make_record):
        """Blanks should be allowed for country/language no attempt to code."""
        # Using blanks and | for no attempt to code
        record = make_record("240101s2024    |||           000 0 ||| d")
        linter.check_record(record)
        field_008_warnings = [w for w in linter._warnings if w.field == "008"]
        # Should not warn about invalid country or language when using |
        country_lang_warnings = [
            w
            for w in field_008_warnings
            if "country" in w.message.lower() or "language" in w.message.lower()
        ]
        assert len(country_lang_warnings) == 0
