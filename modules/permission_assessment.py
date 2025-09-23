from modules.logging_base import Logging
from models.neo4j import Node, Path
import os
import json
from modules.rule_engine import RuleEngine

QV_TO_DEZ_MAPPING = {
    'Very High': 5,
    'High': 4,
    'Medium': 3,
    'Low': 2,
    'Very Low': 1
}

DEZ_TO_QV_MAPPING = {v: k for k, v in QV_TO_DEZ_MAPPING.items()}

logger = Logging().getLogger()


def assess_permissions(paths: list[Path], permission_rules_dir_path: str, attribute_rule_engine: RuleEngine,
                       adass_score: float, event_monitoring_config: dict) -> int:
    # Load all rules from directory
    rules = {}
    for filename in os.listdir(permission_rules_dir_path):
        if filename.endswith(".json"):
            with open(os.path.join(permission_rules_dir_path, filename), 'r') as f:
                try:
                    rule = json.load(f)
                    rules.update({rule['Name']: rule})
                    logger.debug(f"Loaded {len(rules)} permission assessment rules from {filename}")
                except json.JSONDecodeError as e:
                    raise RuntimeError(f"Error loading rules from {permission_rules_dir_path}: {e}")

    highest_scoring_assessment = ()
    for path in paths:
        logger.debug(f"Assessing permissions for path: {path}")
        if path.relationship.type in rules.keys():
            permission_likelihood = _assess_permission_likelihood(
                path, rules, adass_score, event_monitoring_config)
            logger.debug(f"Path likelihood: {permission_likelihood}")
            permission_impact = _assess_permission_impact(path, rules, attribute_rule_engine)
            logger.debug(f"Path impact: {permission_impact}")
            if highest_scoring_assessment == () or \
                    permission_likelihood > highest_scoring_assessment[1] and permission_impact >= highest_scoring_assessment[2]:
                highest_scoring_assessment = (path, permission_likelihood, permission_impact)

        else:
            logger.warning(
                f"No matching permission assessment rule for relationship type '{path.relationship.type}' in path: {path}")

    if highest_scoring_assessment == ():
        logger.info("No paths with assessable permissions found.")
        return 0

    hs_path = highest_scoring_assessment[0]
    hs_likelihood = highest_scoring_assessment[1]
    hs_impact = highest_scoring_assessment[2]

    qualitative_likelihood = _semi_qualitative_to_qualitative_dezimal(hs_likelihood)
    risk = qualitative_likelihood * hs_impact

    qualitative_risk = _semi_qualitative_to_qualitative_dezimal(risk)
    logger.info(
        f"Highest Permission Impact Path: {hs_path} with score {risk} => {qualitative_risk} : {DEZ_TO_QV_MAPPING[qualitative_risk]}")

    return qualitative_risk


def _assess_permission_likelihood(path: Path, permission_rules: dict, adass_score: float, event_monitoring_config: dict) -> float:
    logger.debug(f"Assessing likelihood")

    # Determine Threat Initiation from ADASS score
    if adass_score >= 9:
        threat_initiation = 5
    elif adass_score >= 7:
        threat_initiation = 4
    elif adass_score >= 4:
        threat_initiation = 3
    elif adass_score > 0:
        threat_initiation = 2
    else:
        threat_initiation = 1

    events = permission_rules[path.relationship.type].get('Events')
    predisposing_conditions = permission_rules[path.relationship.type].get(
        'Predisposing Conditions')

    for event_id in events:
        for event, monitored in event_monitoring_config.items():
            if event == event_id and monitored == True:
                predisposing_conditions = predisposing_conditions * -1
                break

    threat_occurrence = permission_rules[path.relationship.type].get('Threat Occurrence')
    likelihood = (threat_initiation * threat_occurrence) + predisposing_conditions

    logger.debug(
        f"likelihood = ({threat_initiation} * {threat_occurrence}) + {predisposing_conditions} = {likelihood}")
    return likelihood


def _assess_permission_impact(path: Path, permission_rules: dict, rule_engine: RuleEngine) -> int:
    logger.debug(f"Assessing impact")
    traversable_edge = permission_rules[path.relationship.type].get('Traversable', False)
    # Reevaluate all rules, this is necessary because the RuleEngine caches previous evaluations for convenience
    rule_engine.evaluate_all_rules(path.end_node)
    matching_rules = rule_engine.get_matching_rules(path.end_node)
    logger.debug(f"Matching Rules: {[rule['rule_name'] for rule in matching_rules]}")
    impact_rules = {
        'Very High': ['Tier Zero Object'],
        'High': ['Tier One Object'],
        'Medium': ['Privileged Account', 'Service Account'],
    }
    for qualitative_value, rules in impact_rules.items():
        if any(rule in [r['rule_name'] for r in matching_rules] for rule in rules):
            return QV_TO_DEZ_MAPPING[qualitative_value] if traversable_edge else QV_TO_DEZ_MAPPING['Very Low']
        elif traversable_edge:
            return QV_TO_DEZ_MAPPING['Low']
        else:
            return QV_TO_DEZ_MAPPING['Very Low']


def _semi_qualitative_to_qualitative_dezimal(value: int) -> int:
    if value >= 20:
        return QV_TO_DEZ_MAPPING['Very High']
    elif value >= 15:
        return QV_TO_DEZ_MAPPING['High']
    elif value >= 10:
        return QV_TO_DEZ_MAPPING['Medium']
    elif value >= 5:
        return QV_TO_DEZ_MAPPING['Low']
    else:
        return QV_TO_DEZ_MAPPING['Very Low']
