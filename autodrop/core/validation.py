"""Centralized validation utilities for numeric and temporal form inputs."""

from datetime import date, datetime, time
from typing import Any, Optional, Union
from autodrop.core.i18n import _


class ValidationError(Exception):
    """Exception raised when user input validation fails.

    Attributes:
        field_name: The name or label of the field that failed validation.
        message: A user-friendly error message describing the validation failure.
    """

    def __init__(self, field_name: str, message: str):
        self.field_name = field_name
        self.message = message
        super().__init__(message)


def validate_number(
    value: Any,
    field_name: str,
    is_float: bool = False,
    min_value: Optional[Union[int, float]] = None,
    max_value: Optional[Union[int, float]] = None,
    required: bool = True,
) -> Optional[Union[int, float]]:
    """Validates and parses a numeric string or value.

    Normalizes decimal comma separators (e.g. '47,50' -> '47.50'). If is_float is False,
    enforces strict integer representation (rejects decimals).

    Args:
        value: The raw input string or numeric value.
        field_name: Human-readable field name used in error messages.
        is_float: True to parse as float, False to parse strictly as integer.
        min_value: Optional minimum acceptable value (inclusive).
        max_value: Optional maximum acceptable value (inclusive).
        required: Whether the field is required (True) or optional (False).

    Returns:
        Optional[Union[int, float]]: Parsed integer or float, or None if optional and empty.

    Raises:
        ValidationError: If the input is invalid, missing when required, or out of range.
    """
    if value is None:
        if required:
            raise ValidationError(field_name, _("'{field}' is required.").format(field=field_name))
        return None

    str_val = str(value).strip()
    if not str_val:
        if required:
            raise ValidationError(field_name, _("'{field}' is required.").format(field=field_name))
        return None

    # Replace Hungarian / European decimal comma with decimal point
    normalized = str_val.replace(",", ".")

    if is_float:
        try:
            num = float(normalized)
        except ValueError:
            raise ValidationError(
                field_name,
                _("'{field}' must be a valid number.").format(field=field_name),
            )
    else:
        # Strictly check for integers (reject decimal points)
        try:
            if "." in normalized:
                raise ValueError()
            num = int(normalized)
        except ValueError:
            raise ValidationError(
                field_name,
                _("'{field}' must be a valid whole number.").format(field=field_name),
            )

    if min_value is not None and num < min_value:
        raise ValidationError(
            field_name,
            _("'{field}' must be at least {min_val}.").format(field=field_name, min_val=min_value),
        )

    if max_value is not None and num > max_value:
        raise ValidationError(
            field_name,
            _("'{field}' must be at most {max_val}.").format(field=field_name, max_val=max_value),
        )

    return num


def validate_temporal(
    value: Any,
    field_name: str,
    target_type: str = "date",
    required: bool = True,
) -> Optional[Union[date, time, datetime]]:
    """Validates and parses a date, time, or datetime string in ISO format.

    Args:
        value: The raw string value.
        field_name: Human-readable field name used in error messages.
        target_type: One of 'date', 'time', or 'datetime'.
        required: Whether the field is required (True) or optional (False).

    Returns:
        Optional[Union[date, time, datetime]]: The parsed temporal object, or None if optional and empty.

    Raises:
        ValidationError: If parsing fails or value is missing when required.
    """
    if value is None:
        if required:
            raise ValidationError(field_name, _("'{field}' is required.").format(field=field_name))
        return None

    str_val = str(value).strip()
    if not str_val:
        if required:
            raise ValidationError(field_name, _("'{field}' is required.").format(field=field_name))
        return None

    if target_type == "date":
        try:
            return date.fromisoformat(str_val)
        except ValueError:
            raise ValidationError(
                field_name,
                _("'{field}' must be a valid date in YYYY-MM-DD format.").format(field=field_name),
            )
    elif target_type == "time":
        try:
            # Handles HH:MM or HH:MM:SS
            parts = [int(p) for p in str_val.split(":")]
            if len(parts) == 2:
                return time(hour=parts[0], minute=parts[1])
            elif len(parts) == 3:
                return time(hour=parts[0], minute=parts[1], second=parts[2])
            raise ValueError()
        except Exception:
            raise ValidationError(
                field_name,
                _("'{field}' must be a valid time in HH:MM format.").format(field=field_name),
            )
    elif target_type == "datetime":
        try:
            return datetime.fromisoformat(str_val)
        except ValueError:
            raise ValidationError(
                field_name,
                _("'{field}' must be a valid date and time.").format(field=field_name),
            )
    else:
        raise ValueError(f"Unsupported target_type: {target_type}")
