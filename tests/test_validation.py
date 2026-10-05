"""Unit tests for centralized numeric and temporal input validation utilities."""

from datetime import date, datetime, time
import pytest

from autodrop.core.validation import ValidationError, validate_number, validate_temporal


def test_validate_number_integers():
    """Tests integer validation, decimal comma handling, and invalid inputs."""
    # Valid integers
    assert validate_number("42", "Count") == 42
    assert validate_number(100, "Count") == 100
    assert validate_number(" 15 ", "Count") == 15
    assert validate_number("-5", "Count") == -5

    # Optional empty values
    assert validate_number("", "Count", required=False) is None
    assert validate_number(None, "Count", required=False) is None

    # Required missing values
    with pytest.raises(ValidationError) as exc:
        validate_number("", "Count", required=True)
    assert "kitöltése kötelező" in str(exc.value) or "required" in str(exc.value)

    with pytest.raises(ValidationError) as exc:
        validate_number(None, "Count", required=True)
    assert "kitöltése kötelező" in str(exc.value) or "required" in str(exc.value)

    # Rejection of floats when is_float=False
    with pytest.raises(ValidationError) as exc:
        validate_number("42.5", "Count", is_float=False)
    assert "egész szám" in str(exc.value) or "whole number" in str(exc.value)

    with pytest.raises(ValidationError) as exc:
        validate_number("42,5", "Count", is_float=False)
    assert "egész szám" in str(exc.value) or "whole number" in str(exc.value)

    # Non-numeric string
    with pytest.raises(ValidationError) as exc:
        validate_number("abc", "Count", is_float=False)
    assert "egész szám" in str(exc.value) or "whole number" in str(exc.value)


def test_validate_number_floats_and_comma_normalization():
    """Tests float validation, comma decimal conversion, and boundaries."""
    # Standard dot notation
    assert validate_number("47.50", "Latitude", is_float=True) == 47.50

    # European comma notation
    assert validate_number("47,50", "Latitude", is_float=True) == 47.50
    assert validate_number(" 19,05 ", "Longitude", is_float=True) == 19.05

    # Integer parsed as float
    assert validate_number("47", "Latitude", is_float=True) == 47.0

    # Invalid float strings
    with pytest.raises(ValidationError) as exc:
        validate_number("not-a-number", "Latitude", is_float=True)
    assert "érvényes szám" in str(exc.value) or "valid number" in str(exc.value)

    # Min/Max range bounds
    with pytest.raises(ValidationError) as exc:
        validate_number("-1", "Day", min_value=0, max_value=6)
    assert "legalább 0" in str(exc.value) or "at least 0" in str(exc.value)

    with pytest.raises(ValidationError) as exc:
        validate_number("7", "Day", min_value=0, max_value=6)
    assert "legfeljebb 6" in str(exc.value) or "at most 6" in str(exc.value)

    assert validate_number("0", "Day", min_value=0, max_value=6) == 0
    assert validate_number("6", "Day", min_value=0, max_value=6) == 6


def test_validate_temporal_date():
    """Tests ISO date parsing and validation."""
    parsed_date = validate_temporal("2026-09-07", "Date of Birth", target_type="date")
    assert parsed_date == date(2026, 9, 7)

    # Optional empty
    assert validate_temporal("", "Date of Birth", target_type="date", required=False) is None
    assert validate_temporal(None, "Date of Birth", target_type="date", required=False) is None

    # Invalid date formats
    with pytest.raises(ValidationError) as exc:
        validate_temporal("07/09/2026", "Date of Birth", target_type="date")
    assert "YYYY-MM-DD" in str(exc.value) or "ÉÉÉÉ-HH-NN" in str(exc.value)

    with pytest.raises(ValidationError) as exc:
        validate_temporal("invalid-date", "Date of Birth", target_type="date")
    assert "YYYY-MM-DD" in str(exc.value) or "ÉÉÉÉ-HH-NN" in str(exc.value)


def test_validate_temporal_time():
    """Tests time parsing (HH:MM and HH:MM:SS)."""
    assert validate_temporal("18:30", "Start Time", target_type="time") == time(18, 30)
    assert validate_temporal("09:15:45", "Start Time", target_type="time") == time(9, 15, 45)

    with pytest.raises(ValidationError) as exc:
        validate_temporal("25:00", "Start Time", target_type="time")
    assert "HH:MM" in str(exc.value) or "ÓÓ:PP" in str(exc.value)

    with pytest.raises(ValidationError) as exc:
        validate_temporal("invalid-time", "Start Time", target_type="time")
    assert "HH:MM" in str(exc.value) or "ÓÓ:PP" in str(exc.value)


def test_validate_temporal_datetime():
    """Tests ISO datetime parsing."""
    parsed_dt = validate_temporal("2026-09-07T18:30:00", "Event Time", target_type="datetime")
    assert parsed_dt == datetime(2026, 9, 7, 18, 30, 0)

    with pytest.raises(ValidationError) as exc:
        validate_temporal("not-a-datetime", "Event Time", target_type="datetime")
    assert "dátum" in str(exc.value) or "date" in str(exc.value)
