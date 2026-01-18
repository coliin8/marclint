"""Tests for multi-record processing and record identification."""

from pytest import fixture
from pymarc import Record, Field, Subfield

from marc_lint import RecordResult


@fixture
def make_record():
    """Factory to create records with optional 001 field."""

    def _make(
        control_number: str | None = None,
        title: str = "Test title.",
        has_error: bool = False,
    ) -> Record:
        r = Record()
        r.leader = "00000nam a2200000 i 4500"
        if control_number:
            r.add_field(Field(tag="001", data=control_number))
        r.add_field(Field(tag="008", data="240101s2024    xxu           000 0 eng d"))

        # Optionally create an error (missing period)
        title_text = title if not has_error else title.rstrip(".")
        r.add_field(
            Field(
                tag="245",
                indicators=["0", "0"],
                subfields=[Subfield("a", title_text)],
            )
        )
        return r

    return _make


class TestRecordResult:
    """Tests for RecordResult class."""

    def test_record_result_creation(self):
        """RecordResult should store record ID and warnings."""
        from marc_lint.warning import MarcWarning

        warnings = [MarcWarning(field="245", message="Test error")]
        result = RecordResult(record_id="12345", warnings=warnings)

        assert result.record_id == "12345"
        assert len(result.warnings) == 1
        assert result.warnings[0].message == "Test error"

    def test_record_result_is_valid(self):
        """is_valid should return True when no warnings."""
        result = RecordResult(record_id="12345", warnings=[])
        assert result.is_valid is True

    def test_record_result_is_not_valid(self):
        """is_valid should return False when warnings exist."""
        from marc_lint.warning import MarcWarning

        warnings = [MarcWarning(field="245", message="Test error")]
        result = RecordResult(record_id="12345", warnings=warnings)
        assert result.is_valid is False

    def test_record_result_repr(self):
        """RecordResult repr should be informative."""
        from marc_lint.warning import MarcWarning

        warnings = [MarcWarning(field="245", message="Test error")]
        result = RecordResult(record_id="12345", warnings=warnings)
        repr_str = repr(result)
        assert "12345" in repr_str
        assert "1" in repr_str  # warning count


class TestCheckRecords:
    """Tests for check_records multi-record method."""

    def test_check_single_record(self, linter, make_record):
        """check_records should work with a single record."""
        record = make_record(control_number="rec001")
        results = linter.check_records([record])

        assert len(results) == 1
        assert results[0].record_id == "rec001"

    def test_check_multiple_records(self, linter, make_record):
        """check_records should process multiple records."""
        records = [
            make_record(control_number="rec001"),
            make_record(control_number="rec002"),
            make_record(control_number="rec003"),
        ]
        results = linter.check_records(records)

        assert len(results) == 3
        assert results[0].record_id == "rec001"
        assert results[1].record_id == "rec002"
        assert results[2].record_id == "rec003"

    def test_check_records_tracks_errors_per_record(self, linter, make_record):
        """Errors should be associated with correct records."""
        records = [
            make_record(control_number="good001", has_error=False),
            make_record(control_number="bad001", has_error=True),
            make_record(control_number="good002", has_error=False),
        ]
        results = linter.check_records(records)

        assert results[0].is_valid  # good001
        assert not results[1].is_valid  # bad001
        assert results[2].is_valid  # good002

        # Verify the error is on the right record
        assert results[1].record_id == "bad001"
        assert any("245" in w.field for w in results[1].warnings)

    def test_check_records_without_001(self, linter, make_record):
        """Records without 001 should use index as ID when specified."""
        records = [
            make_record(control_number=None),  # No 001
            make_record(control_number=None),
        ]
        results = linter.check_records(records, use_index_as_id=True)

        assert len(results) == 2
        assert results[0].record_id == "0"
        assert results[1].record_id == "1"

    def test_check_records_mixed_with_without_001(self, linter, make_record):
        """Mix of records with and without 001 fields."""
        records = [
            make_record(control_number="has001"),
            make_record(control_number=None),
            make_record(control_number="also_has001"),
        ]
        results = linter.check_records(records, use_index_as_id=True)

        assert results[0].record_id == "has001"
        assert results[1].record_id == "1"  # Index when no 001
        assert results[2].record_id == "also_has001"

    def test_check_records_returns_record_reference(self, linter, make_record):
        """RecordResult should contain reference to original record."""
        record = make_record(control_number="test001")
        results = linter.check_records([record])

        assert results[0].record is record

    def test_check_records_empty_list(self, linter):
        """Empty list should return empty results."""
        results = linter.check_records([])
        assert len(results) == 0


class TestWarningRecordId:
    """Tests for record_id in MarcWarning."""

    def test_warning_includes_record_id(self, linter, make_record):
        """Warnings should include record_id when provided."""
        record = make_record(control_number="test123", has_error=True)
        warnings = linter.check_record(record)

        # Find the 245 warning
        title_warnings = [w for w in warnings if w.field == "245"]
        assert len(title_warnings) > 0
        assert title_warnings[0].record_id == "test123"

    def test_warning_str_with_record_id(self):
        """Warning string should include record ID."""
        from marc_lint.warning import MarcWarning

        warning = MarcWarning(
            field="245",
            message="Must end with . (period).",
            record_id="ctrl12345",
        )
        warning_str = str(warning)
        assert "Record ctrl12345" in warning_str
        assert "245" in warning_str

    def test_warning_to_dict_includes_record_id(self):
        """to_dict should include record_id."""
        from marc_lint.warning import MarcWarning

        warning = MarcWarning(
            field="245",
            message="Test error",
            record_id="rec001",
        )
        result = warning.to_dict()

        assert result["record_id"] == "rec001"

    def test_check_record_with_explicit_record_id(self, linter, make_record):
        """check_record should accept explicit record_id parameter."""
        record = make_record(control_number="field001", has_error=True)
        # Override with explicit record_id
        warnings = linter.check_record(record, record_id="explicit_id")

        title_warnings = [w for w in warnings if w.field == "245"]
        assert title_warnings[0].record_id == "explicit_id"

    def test_check_record_returns_warnings(self, linter, make_record):
        """check_record should return list of warnings."""
        record = make_record(control_number="test001", has_error=True)
        warnings = linter.check_record(record)

        assert isinstance(warnings, list)
        assert len(warnings) > 0
        assert all(hasattr(w, "field") for w in warnings)
