"""Tests for MarcWarning structured warning class."""

import json

from marc_lint.warning import MarcWarning


def test_warning_basic_creation():
    """Test creating a basic MarcWarning."""
    warning = MarcWarning(field="245", message="Must end with . (period).")

    assert warning.field == "245"
    assert warning.message == "Must end with . (period)."
    assert warning.subfield is None
    assert warning.position is None


def test_warning_with_subfield():
    """Test MarcWarning with subfield."""
    warning = MarcWarning(field="020", message="has bad checksum.", subfield="a")

    assert warning.field == "020"
    assert warning.message == "has bad checksum."
    assert warning.subfield == "a"
    assert warning.position is None


def test_warning_with_position():
    """Test MarcWarning with position for repeating fields."""
    warning = MarcWarning(field="020", message="Field is not repeatable.", position=1)

    assert warning.field == "020"
    assert warning.message == "Field is not repeatable."
    assert warning.subfield is None
    assert warning.position == 1


def test_warning_with_subfield_and_position():
    """Test MarcWarning with both subfield and position."""
    warning = MarcWarning(
        field="020", message="has bad checksum, 123456789X.", subfield="a", position=2
    )

    assert warning.field == "020"
    assert warning.message == "has bad checksum, 123456789X."
    assert warning.subfield == "a"
    assert warning.position == 2


def test_warning_str_field_only():
    """Test string representation for field-level error."""
    warning = MarcWarning(field="245", message="Must end with . (period).")
    assert str(warning) == "245: Must end with . (period)."


def test_warning_str_with_subfield():
    """Test string representation with subfield."""
    warning = MarcWarning(field="020", message="has bad checksum.", subfield="a")
    assert str(warning) == "020: Subfield a has bad checksum."


def test_warning_str_with_position():
    """Test string representation with position (1-indexed display)."""
    warning = MarcWarning(field="020", message="Field is not repeatable.", position=1)
    # Position 1 (0-based) should display as [2] (1-based)
    assert str(warning) == "020[2]: Field is not repeatable."


def test_warning_str_with_position_zero():
    """Test string representation with position 0."""
    warning = MarcWarning(field="020", message="Invalid field.", position=0)
    # Position 0 (0-based) should display as [1] (1-based)
    assert str(warning) == "020[1]: Invalid field."


def test_warning_str_with_subfield_and_position():
    """Test string representation with both subfield and position."""
    warning = MarcWarning(
        field="020", message="has bad checksum, 123456789X.", subfield="a", position=1
    )
    assert str(warning) == "020[2]: Subfield a has bad checksum, 123456789X."


def test_warning_to_dict_basic():
    """Test to_dict for basic warning."""
    warning = MarcWarning(field="245", message="Must end with . (period).")
    result = warning.to_dict()

    assert result == {
        "field": "245",
        "message": "Must end with . (period).",
        "subfield": None,
        "position": None,
    }


def test_warning_to_dict_with_subfield():
    """Test to_dict with subfield."""
    warning = MarcWarning(field="020", message="has bad checksum.", subfield="a")
    result = warning.to_dict()

    assert result == {
        "field": "020",
        "message": "has bad checksum.",
        "subfield": "a",
        "position": None,
    }


def test_warning_to_dict_with_position():
    """Test to_dict with position."""
    warning = MarcWarning(field="020", message="Field is not repeatable.", position=1)
    result = warning.to_dict()

    assert result == {
        "field": "020",
        "message": "Field is not repeatable.",
        "subfield": None,
        "position": 1,
    }


def test_warning_to_dict_complete():
    """Test to_dict with all fields."""
    warning = MarcWarning(
        field="020", message="has bad checksum, 123456789X.", subfield="a", position=2
    )
    result = warning.to_dict()

    assert result == {
        "field": "020",
        "message": "has bad checksum, 123456789X.",
        "subfield": "a",
        "position": 2,
    }


def test_warning_json_serialization():
    """Test that to_dict output can be JSON serialized."""
    warning = MarcWarning(
        field="020", message="has bad checksum.", subfield="a", position=1
    )

    # Should not raise an exception
    json_str = json.dumps(warning.to_dict())

    # Verify it can be parsed back
    parsed = json.loads(json_str)
    assert parsed["field"] == "020"
    assert parsed["message"] == "has bad checksum."
    assert parsed["subfield"] == "a"
    assert parsed["position"] == 1


def test_warning_list_json_serialization():
    """Test JSON serialization of multiple warnings."""
    warnings = [
        MarcWarning(field="020", message="bad checksum.", subfield="a"),
        MarcWarning(field="245", message="Must end with period."),
        MarcWarning(field="022", message="invalid ISSN.", subfield="a", position=1),
    ]

    warnings_dict = [w.to_dict() for w in warnings]
    json_str = json.dumps(warnings_dict, indent=2)

    parsed = json.loads(json_str)
    assert len(parsed) == 3
    assert parsed[0]["field"] == "020"
    assert parsed[1]["field"] == "245"
    assert parsed[2]["field"] == "022"
    assert parsed[2]["position"] == 1


def test_warning_equality():
    """Test that two warnings with same data are equal (dataclass feature)."""
    warning1 = MarcWarning(
        field="020", message="has bad checksum.", subfield="a", position=1
    )
    warning2 = MarcWarning(
        field="020", message="has bad checksum.", subfield="a", position=1
    )

    assert warning1 == warning2


def test_warning_inequality():
    """Test that different warnings are not equal."""
    warning1 = MarcWarning(field="020", message="bad checksum.", subfield="a")
    warning2 = MarcWarning(field="245", message="bad checksum.", subfield="a")

    assert warning1 != warning2


def test_warning_with_empty_message():
    """Test warning with empty message."""
    warning = MarcWarning(field="020", message="")
    assert str(warning) == "020: "
    assert warning.to_dict()["message"] == ""


def test_warning_with_special_characters():
    """Test warning with special characters in message."""
    warning = MarcWarning(
        field="245", message='Message with "quotes" and \n newline.', subfield="a"
    )

    assert "quotes" in warning.message
    assert "\n" in warning.message
    result = warning.to_dict()
    assert result["message"] == 'Message with "quotes" and \n newline.'


def test_warning_repr():
    """Test that dataclass generates a useful repr."""
    warning = MarcWarning(field="020", message="test", subfield="a", position=1)

    repr_str = repr(warning)
    assert "MarcWarning" in repr_str
    assert "field='020'" in repr_str
    assert "message='test'" in repr_str
    assert "subfield='a'" in repr_str
    assert "position=1" in repr_str


def test_warning_string_format_consistency():
    """Test that string format is consistent across similar warnings."""
    # All these should have consistent formatting
    warning1 = MarcWarning(field="020", message="error 1", subfield="a")
    warning2 = MarcWarning(field="022", message="error 2", subfield="z")
    warning3 = MarcWarning(field="245", message="error 3", subfield="b")

    # All should follow "FIELD: Subfield CODE message" pattern
    assert str(warning1) == "020: Subfield a error 1"
    assert str(warning2) == "022: Subfield z error 2"
    assert str(warning3) == "245: Subfield b error 3"


def test_warning_position_display_offset():
    """Test that position is correctly offset for display (0-based to 1-based)."""
    # Test multiple positions to verify the offset
    for i in range(5):
        warning = MarcWarning(field="020", message="test", position=i)
        expected = f"020[{i + 1}]: test"
        assert str(warning) == expected


def test_warning_dataclass_immutability():
    """Test that warnings can be modified (dataclass default behavior)."""
    warning = MarcWarning(field="020", message="original")

    # Dataclasses are mutable by default unless frozen=True
    warning.message = "modified"
    assert warning.message == "modified"


def test_warning_dict_keys_present():
    """Test that to_dict always includes all keys."""
    warning = MarcWarning(field="020", message="test")
    result = warning.to_dict()

    # All keys should be present
    assert "field" in result
    assert "message" in result
    assert "subfield" in result
    assert "position" in result
