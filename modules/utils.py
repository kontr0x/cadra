from typing import List, Dict, Any

from modules.logging_base import Logging
from models.neo4j import User, Edge, Node
from models.bloodhound import EdgeType
from modules.converters import normalize_operator_values, convert_to_timestamp

logger = Logging().getLogger()


def compare(operator: str, value1: Any, value2: Any) -> bool:
    if operator not in ['==', '!=', '<', '>', '<=', '>=', 'in', 'not in', 'any', 'older_than', 'newer_than', 'notset', 'set', 'startswith', 'endswith']:
        logger.error(f"Invalid operator: {operator}")
        raise ValueError(f"Invalid operator: {operator}")

    try:
        # TODO: Maybe make this nice somehow
        # If one of the values is None and the operator is not '==' or '!=', return False
        if (value1 is None or value2 is None) and operator not in ['==', '!=', 'notset']:
            logger.warning(f"One of the values is None for operator {operator}, returning False")
            return False

        # Normalize the values based on the operator
        value1, value2 = normalize_operator_values(value1, value2, operator)

        # Perform the comparison
        match operator:
            case '==':
                return value1 == value2
            case '!=':
                return value1 != value2
            case '<':
                return value1 < value2
            case '>':
                return value1 > value2
            case '<=':
                return value1 <= value2
            case '>=':
                return value1 >= value2
            case 'in':
                return _in_all(value1, value2)
            case 'not in':
                return not _in_any(value1, value2)
            case 'any':
                return _in_any(value1, value2)
            case 'older_than':
                timestamp = convert_to_timestamp(value2)
                return value1 > timestamp
            case 'newer_than':
                timestamp = convert_to_timestamp(value2)
                return value1 < timestamp
            case 'set':
                if isinstance(value1, list):
                    return value1 != []
                else:
                    return value1 != '' and value1 not in ['null', 'None']
            case 'notset':
                # Assuming 'notset' means the value is None or empty
                possible_values = [None, '', 'null', 'None']
                return value1 in possible_values or value2 in possible_values
            case 'startswith':
                return str(value1).startswith(value2)
            case 'endswith':
                return str(value1).endswith(value2)

    except Exception as e:
        logger.error(f"Comparison failed: {value1} {operator} {value2}. Error: {e}")
        return False


def _in_any(value1: Any, value2: Any) -> bool:
    if isinstance(value1, (list, set)) and isinstance(value2, (list, set)):
        return any(item in value1 for item in value2)
    elif isinstance(value1, str) and isinstance(value2, (list, set)):
        return value1 in value2
    elif isinstance(value1, (list, set)) and isinstance(value2, str):
        return value2 in value1
    elif isinstance(value1, str) and isinstance(value2, str):
        return value1 in value2 or value2 in value1
    else:
        raise ValueError(f"Invalid types for 'any' operator: {type(value1)}, {type(value2)}")


def _in_all(value1: Any, value2: Any) -> bool:
    if isinstance(value1, (list, set)) and isinstance(value2, (list, set)):
        return all(item in value1 for item in value2)
    elif isinstance(value1, str) and isinstance(value2, (list, set)):
        return value1 in value2
    elif isinstance(value1, (list, set)) and isinstance(value2, str):
        return value2 in value1
    else:
        raise ValueError(f"Invalid types for 'all' operator: {type(value1)}, {type(value2)}")
