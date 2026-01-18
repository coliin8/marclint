"""Tests for MARC leader validation."""

from pytest import fixture
from pymarc import Record, Field, Subfield


@fixture
def make_record():
    """Factory to create records with custom leaders."""

    def _make(
        leader: str = "00000nam a2200000 i 4500",
        include_required: bool = True,
    ) -> Record:
        r = Record()
        r.leader = leader
        if include_required:
            r.add_field(Field(tag="001", data="test001"))
            r.add_field(
                Field(tag="008", data="240101s2024    xxu           000 0 eng d")
            )
            r.add_field(
                Field(
                    tag="245",
                    indicators=["0", "0"],
                    subfields=[Subfield("a", "Test title.")],
                )
            )
        return r

    return _make


class TestLeaderValidation:
    """Tests for check_leader method."""

    def test_valid_leader(self, linter, make_record):
        """Valid leader should produce no warnings."""
        record = make_record(leader="00000nam a2200000 i 4500")
        linter.check_record(record)
        leader_warnings = [w for w in linter._warnings if w.field == "LDR"]
        assert len(leader_warnings) == 0

    def test_short_leader(self, linter, make_record):
        """Leader shorter than 24 characters should warn."""
        record = make_record(leader="00000nam a22", include_required=False)
        linter.check_record(record)
        leader_warnings = [w for w in linter._warnings if w.field == "LDR"]
        assert len(leader_warnings) == 1
        assert "must be 24 characters" in leader_warnings[0].message

    def test_invalid_record_status(self, linter, make_record):
        """Invalid record status (position 05) should warn."""
        # Position 05 is 'x' which is invalid
        record = make_record(leader="00000xam a2200000 i 4500")
        linter.check_record(record)
        leader_warnings = [w for w in linter._warnings if w.field == "LDR"]
        assert any("record status" in w.message.lower() for w in leader_warnings)

    def test_invalid_type_of_record(self, linter, make_record):
        """Invalid type of record (position 06) should warn."""
        # Position 06 is 'x' which is invalid
        record = make_record(leader="00000nxm a2200000 i 4500")
        linter.check_record(record)
        leader_warnings = [w for w in linter._warnings if w.field == "LDR"]
        assert any("type of record" in w.message.lower() for w in leader_warnings)

    def test_invalid_bibliographic_level(self, linter, make_record):
        """Invalid bibliographic level (position 07) should warn."""
        # Position 07 is 'x' which is invalid
        record = make_record(leader="00000nax a2200000 i 4500")
        linter.check_record(record)
        leader_warnings = [w for w in linter._warnings if w.field == "LDR"]
        assert any("bibliographic level" in w.message.lower() for w in leader_warnings)

    def test_invalid_type_of_control(self, linter, make_record):
        """Invalid type of control (position 08) should warn."""
        # Position 08 is 'x' which is invalid
        record = make_record(leader="00000namxa2200000 i 4500")
        linter.check_record(record)
        leader_warnings = [w for w in linter._warnings if w.field == "LDR"]
        assert any("type of control" in w.message.lower() for w in leader_warnings)

    def test_invalid_encoding_level(self, linter, make_record):
        """Invalid encoding level (position 17) should warn."""
        # Position 17 is 'x' which is invalid
        record = make_record(leader="00000nam a2200000xi 4500")
        linter.check_record(record)
        leader_warnings = [w for w in linter._warnings if w.field == "LDR"]
        assert any("encoding level" in w.message.lower() for w in leader_warnings)

    def test_valid_record_statuses(self, linter, make_record):
        """All valid record status values should pass."""
        valid_statuses = ["a", "c", "d", "n", "p"]
        for status in valid_statuses:
            leader = f"00000{status}am a2200000 i 4500"
            record = make_record(leader=leader)
            linter.check_record(record)
            leader_warnings = [w for w in linter._warnings if w.field == "LDR"]
            status_warnings = [
                w for w in leader_warnings if "record status" in w.message.lower()
            ]
            assert len(status_warnings) == 0, f"Status '{status}' should be valid"

    def test_valid_types_of_record(self, linter, make_record):
        """All valid type of record values should pass."""
        valid_types = [
            "a",
            "c",
            "d",
            "e",
            "f",
            "g",
            "i",
            "j",
            "k",
            "m",
            "o",
            "p",
            "r",
            "t",
        ]
        for rec_type in valid_types:
            leader = f"00000n{rec_type}m a2200000 i 4500"
            record = make_record(leader=leader)
            linter.check_record(record)
            leader_warnings = [w for w in linter._warnings if w.field == "LDR"]
            type_warnings = [
                w for w in leader_warnings if "type of record" in w.message.lower()
            ]
            assert len(type_warnings) == 0, f"Type '{rec_type}' should be valid"
