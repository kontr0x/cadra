import re
from typing import Any
from datetime import timedelta

from modules.logging_base import Logging

logger = Logging().getLogger()


def normalize_operator_values(value1: Any, value2: Any, operator: str) -> tuple:
    if operator in ['==', '!=']:
        # For equality, convert value2 to type of value1
        if isinstance(value1, bool):
            value2 = convert_to_bool(value2)
        elif isinstance(value1, int):
            value2 = convert_to_int(value2)
        elif isinstance(value1, str):
            value2 = str(value2)

    elif operator in ['<', '>', '<=', '>=']:
        # For comparison, both should be numbers
        value1 = convert_to_int(value1) if not isinstance(value1, (int, float)) else value1
        value2 = convert_to_int(value2) if not isinstance(value2, (int, float)) else value2

    elif operator in ['in', 'not in']:
        # For membership, ensure value2 is iterable
        if not isinstance(value2, (list, set)):
            value2 = [value2]

    return value1, value2


def convert_to_int(value: Any) -> int:
    if isinstance(value, int):
        return value

    if isinstance(value, str):
        value = value.strip()
        if value.startswith('0x') or value.startswith('0X'):
            return int(value, 16)  # Hexadecimal
        else:
            return int(value)  # Decimal

    if isinstance(value, float):
        return int(value)

    raise ValueError(f"Cannot convert \"{value}\": {type(value)} to integer")


def convert_to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        lower_val = value.lower().strip()
        if lower_val in ('true', '1'):
            return True
        elif lower_val in ('false', '0'):
            return False
        else:
            logger.error(f"Cannot convert string '{value}' to boolean")

    raise ValueError(f"Cannot convert \"{value}\": {type(value)} to boolean")


def convert_to_timestamp(value: str) -> int:
    pattern = r'(\d+)\s*(year|years|month|months|day|days)'
    matches = re.findall(pattern, value)

    total_seconds = 0
    for amount, unit in matches:
        amount = int(amount)
        if unit.startswith('year'):
            total_seconds += timedelta(days=365 * amount).total_seconds()
        elif unit.startswith('month'):
            total_seconds += timedelta(days=30 * amount).total_seconds()
        elif unit.startswith('day'):
            total_seconds += timedelta(days=amount).total_seconds()

    return int(total_seconds)
