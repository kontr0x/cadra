from typing import Dict

from models.neo4j import User
from modules.rule_engine import RuleEngine
from modules.logging_base import Logging
from modules.adass import ADASS

logger = Logging().getLogger()


def assess_user_attributes(user: User, rule_engine: RuleEngine) -> float:

    # Evaluate the user's attributes against the loaded rules
    matching_rules = rule_engine.get_matching_rules(user)
    logger.info(f"Matching Rules: {[rule['rule_name'] for rule in matching_rules]}")

    adass_metrics_dict: Dict[str, str] = {}
    for rule in matching_rules:
        if rule['metric'] in adass_metrics_dict and adass_metrics_dict[rule['metric']] != rule['value']:
            adass_metrics_dict[rule['metric']] = rule['value']
            logger.warning(
                f"Overwriting ADASS metric {rule['metric']} from {adass_metrics_dict[rule['metric']]} to {rule['value']}")
        else:
            adass_metrics_dict[rule['metric']] = rule['value']

    adass_string_parts = [f"{key}:{value}" for key, value in adass_metrics_dict.items()]

    # CIA rules
    matching_rule_names = [rule['rule_name'] for rule in matching_rules]
    # Confidentiality
    high_confidentiality_rules = ['Tier Zero Object']
    low_confidentiality_rules = ['Service Account']
    adass_string_parts.append(_check_cia_rules(matching_rule_names, "C",
                              high_confidentiality_rules, low_confidentiality_rules, "L"))
    # Integrity
    high_integrity_rules = ['Tier Zero Object']
    low_integrity_rules = ['Service Account']
    adass_string_parts.append(_check_cia_rules(matching_rule_names, "I",
                              high_integrity_rules, low_integrity_rules, "L"))
    # Availability
    high_availability_rules = ['Tier Zero Object']
    low_availability_rules = ['Service Account']
    adass_string_parts.append(_check_cia_rules(matching_rule_names, "A",
                              high_availability_rules, low_availability_rules, "N"))

    logger.debug(f"ADASS String: {'/'.join(adass_string_parts)}")
    score = ADASS("/".join(adass_string_parts)).calculate_score()

    return score


def _check_cia_rules(matching_rule_names: list[str], metric: str,
                     high_rules: list[str], low_rules: list[str], default_value: str) -> str:
    if any(rule in matching_rule_names for rule in high_rules):
        return f"{metric}:H"
    elif any(rule in matching_rule_names for rule in low_rules):
        return f"{metric}:L"
    else:
        return f"{metric}:{default_value}"
