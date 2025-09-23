# Active Directory Attribute Scoring System (ADASS)

from math import ceil
from typing import Dict
from enum import Enum

from modules.logging_base import Logging

METRIC_KEYS = {
    "S": "Scope",
    "AC": "Access Complexity",
    "PR": "Privileges Required",
    "C": "Confidentiality",
    "I": "Integrity",
    "A": "Availability"
}

MANDATORY_METRICS = ["C", "I", "A"]

logger = Logging().getLogger()


class Metric:
    def __init__(self, key: str, values: Dict[str, float]):
        self.key: str = key
        self.label: str = METRIC_KEYS.get(key)
        self.values: Dict[str, float] = values


class ADASSMetrics(Enum):
    SCOPE = Metric("S", {
        "C": 1,  # Changed
        "U": 0   # Unchanged
    })
    ACCESS_COMPLEXITY = Metric("AC", {
        "NA": 0.61,  # Not available,
        "L": 0.77,   # Low
        "H": 0.44    # High
    })
    PRIVILEGES_REQUIRED = Metric("PR", {
        "NA": 0.58,  # Not available
        "NA_S": 0.67,  # Not available (Scope Changed)
        "L": 0.62,   # Low
        "L_S": 0.68,  # Low (Scope Changed)
        "H": 0.27,   # High
        "H_S": 0.50  # High (Scope Changed)
    })
    CONFIDENTIALITY = Metric("C", {
        "L": 0.22,  # Low
        "H": 0.56   # High
    })
    INTEGRITY = Metric("I", {
        "L": 0.22,  # Low
        "H": 0.56   # High
    })
    AVAILABILITY = Metric("A", {
        "N": 0,  # None
        "L": 0.22,  # Low
        "H": 0.56   # High
    })


class ADASS:

    def __init__(self, metrics: str):
        logger.debug(f"Initializing ADASS with metrics: {metrics}")
        # Metrics look like "S:C/C:H/I:H/A:H"
        self._metrics_str: str = metrics
        self.metrics: Dict[str, str] = self._decode_metrics()

    def _decode_metrics(self) -> Dict[str, str]:
        metrics_dict = {}
        try:
            metric_parts = self._metrics_str.split('/')

            # Check for mandatory metrics
            for mandatory in MANDATORY_METRICS:
                supplied_metrics = [part.split(':')[0].upper()
                                    for part in metric_parts if ':' in part]
                if not any(metric_key.startswith(mandatory) for metric_key in supplied_metrics):
                    raise ValueError(f"Mandatory metric '{mandatory}' is missing.")

            # Pre-process metrics
            for part in metric_parts:
                if ':' in part:
                    key, value = part.split(':', 1)
                    if key in METRIC_KEYS:
                        label = str(METRIC_KEYS[key]).upper()
                        metric = ADASSMetrics.__members__.get(label.replace(" ", "_")).value
                        possible_values: Metric = metric.values.keys()
                        if value in possible_values:
                            metrics_dict[key] = value
                else:
                    logger.warning(f"Invalid metric format: {part}")

            # Check if non-mandatory metrics are supplied, if not assign defaults
            for key in METRIC_KEYS.keys():
                if key not in metrics_dict.keys():
                    if key == "S":
                        metrics_dict[key] = "U"  # Default to Unchanged
                    elif key == "AC" or key == "PR":
                        metrics_dict[key] = "NA"  # Default to Not Available
                    else:
                        # This should not happen as all keys in and out of METRIC_KEYS are processed
                        raise RuntimeError(
                            f"This should not happen, somehow missed mandatory metric {key}")

            # Post-process metrics
            # If score changed, check if any metrics have _S variants, if so, use them
            if metrics_dict.get("S") == "C":
                for key in metrics_dict.keys():
                    label = str(METRIC_KEYS[key]).upper()
                    metric = ADASSMetrics.__members__.get(label.replace(" ", "_")).value
                    possible_values: Metric = metric.values.keys()
                    if f"{metrics_dict[key]}_S" in possible_values:
                        metrics_dict[key] = f"{metrics_dict[key]}_S"

        except Exception as e:
            logger.error(f"Error decoding metrics '{self.metrics}': {e}")
        return metrics_dict

    def _calculate_isc(self) -> float:
        ics_base: float = 1 - \
            ((1 - ADASSMetrics.CONFIDENTIALITY.value.values[self.metrics.get("C")]) *
             (1 - ADASSMetrics.INTEGRITY.value.values[self.metrics.get("I")]) *
             (1 - ADASSMetrics.AVAILABILITY.value.values[self.metrics.get("A")]))
        logger.debug(f"ICS Base: {ics_base}")
        if self.metrics.get("S") == "C":
            return 7.52 * (ics_base - 0.029) - 3.25 * ((ics_base - 0.02) ** 15)
        else:
            return 6.42 * ics_base

    def _calculate_exploitability(self) -> float:
        exploitability: float = 5.94 * \
            (ADASSMetrics.ACCESS_COMPLEXITY.value.values[self.metrics.get("AC")] *
             ADASSMetrics.PRIVILEGES_REQUIRED.value.values[self.metrics.get("PR")])
        return exploitability

    def calculate_score(self) -> float:
        isc = self._calculate_isc()
        logger.debug(f"ISC: {isc}")
        exploitability = self._calculate_exploitability()
        logger.debug(f"Exploitability: {exploitability}")

        if self.metrics.get("S") == "C":
            score = _round_up(min(1.08 * (isc + exploitability), 10))
        else:
            score = _round_up(min(isc + exploitability, 10))

        logger.debug(f"ADASS Score: {score}")
        return score


def _round_up(value: float, decimals: int = 1) -> float:
    multiplier = 10 ** decimals
    return ceil(value * multiplier) / multiplier
