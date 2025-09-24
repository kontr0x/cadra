import os
import json
from typing import Dict, List, Any

from modules.logging_base import Logging
from models.neo4j import Node
from modules.utils import compare

logger = Logging().getLogger()


class RuleEngine:
    def __init__(self):
        self.rules: List[Dict] = []
        self.evaluated_rules: Dict[int, List[Dict]] = {}

    def load_rules_from_directory(self, rules_directory: str) -> None:
        self.rules = []
        if not os.path.exists(rules_directory):
            logger.error(f"Rules directory not found: {rules_directory}")
            raise FileNotFoundError(f"Rules directory not found: {rules_directory}")

        rule_files = [f for f in os.listdir(rules_directory) if f.endswith('.json')]
        logger.debug(f"Loading {len(rule_files)} rules from {rules_directory}")

        for rule_file in rule_files:
            rule_path = os.path.join(rules_directory, rule_file)
            with open(rule_path, 'r') as f:
                try:
                    rule = json.load(f)
                    self.rules.append(rule)
                except json.JSONDecodeError as e:
                    logger.error(f"Error loading rule from {rule_path}: {e}")
                    continue

        logger.info(f"Loaded {len(self.rules)} rules from {rules_directory}")

    def __check_criteria(self, criteria: Dict[str, Any], node: Node) -> Dict[str, Any]:
        property_name = criteria['Property']
        user_property_value = getattr(node, property_name)
        operator = criteria['Operator']
        expected_value = criteria['Value']

        try:
            matched = compare(operator, user_property_value, expected_value)
            # logger.info(f"Criteria check: {property_name} {operator} {expected_value} => {matched}")
            logger.debug(
                f"Comparing {property_name} with value {user_property_value} {operator} {expected_value}, match: {matched}")

        except Exception as e:
            logger.error(f"Error checking criteria '{criteria}': {e}")

        return {
            'match': matched,
            'property': property_name,
            'operator': operator,
            'expected': expected_value,
            'actual': user_property_value
        }

    def __check_criterias(self, criterias: List[Dict[str, Any]], node: Node) -> list[bool]:
        results = []
        for criteria in criterias:
            try:
                logger.debug(f"Checking criteria: {criteria}")
                if isinstance(criteria, list):
                    for sub_criteria in criteria:
                        result = self.__check_criteria(sub_criteria, node)
                        results.append(result['match'])
                else:
                    result = self.__check_criteria(criteria, node)
                    results.append(result['match'])
                logger.debug(f"Criteria '{criteria}' => {any(results)}")

            except AttributeError as e:
                # This can be totally normal if a rule is for multiple object types and a property is missing
                logger.debug(f"Criterias '{criteria}' missing property: {e}")
                results.append(None)

            except Exception as e:
                logger.error(f"Error checking criterias '{criteria}': {e}")
                import traceback
                traceback.print_exc()
                results.append(None)

        return results

    def evaluate_rule(self, rule: Dict, node: Node) -> Dict[str, Any]:
        logger.debug(f"Evaluating rule: {rule.get('Name', 'Unnamed Rule')}")
        result = {
            'rule_name': rule.get('Name', 'Unknown'),
            'metric': rule.get('Metric', 'Unknown'),
            'value': rule.get("Value", "Unknown"),
            'prerequisites_met': False,
            'criteria_met': False,
            'matches': False,
        }

        # Check prerequisite criteria
        prerequisite_criteria: Dict[str, Any] = rule.get('Prerequisite Criteria', {})
        if prerequisite_criteria != {}:
            logger.debug(f"Checking prerequisite criteria(s)")
            prerequisite_criteria_list_matches = []
            for criteria_key, criteria_value in prerequisite_criteria.items():
                logger.debug(f"Checking prerequisite criteria '{criteria_key}'")
                matched = None
                if isinstance(criteria_value, list):
                    matched = any(self.__check_criterias(criteria_value, node))
                elif isinstance(criteria_value, dict):
                    matched = self.__check_criterias([criteria_value], node)[0]
                else:
                    raise ValueError(
                        f"Invalid format for prerequisite criteria: {prerequisite_criteria}")
                logger.debug(f"Prerequisite criteria '{criteria_key}' matched: {matched}")
                prerequisite_criteria_list_matches.append(matched)
            result['prerequisites_met'] = all(prerequisite_criteria_list_matches)
            logger.debug(f"Prerequisite criteria matched: {result['prerequisites_met']}")
        else:
            logger.debug(f"No prerequisite criteria for rule '{result.get('rule_name')}'")
            # If no prerequisites, consider them met
            result['prerequisites_met'] = True

        # Check criteria only if prerequisites are met
        if result['prerequisites_met']:
            criteria: Dict[str, Any] = rule.get('Criteria', {})
            logger.debug(f"Checking main criteria(s)")
            criteria_list_matches = []
            for criteria_key, criteria_value in criteria.items():
                logger.debug(f"Checking criteria '{criteria_key}'")
                matched = None
                if isinstance(criteria_value, list):
                    matched = any(self.__check_criterias(criteria_value, node))
                elif isinstance(criteria_value, dict):
                    matched = self.__check_criterias([criteria_value], node)[0]
                else:
                    raise ValueError(f"Invalid format for criteria: {criteria}")
                logger.debug(f"Criteria '{criteria_key}' matched: {matched}")
                criteria_list_matches.append(matched)
            result['criteria_met'] = any(criteria_list_matches)
            logger.debug(f"Criteria matched: {result['criteria_met']}")

        else:
            logger.debug(f"Skipping criteria check due to unmet prerequisites.")

        result['matches'] = result['prerequisites_met'] and result['criteria_met']
        logger.debug(f"Rule matched: {result['matches']}")

        return result

    def evaluate_all_rules(self, node: Node):
        logger.info(f"Evaluating all rules for node: {node.name} (ID: {node.id})")
        for rule in self.rules:
            result = self.evaluate_rule(rule, node)
            self.evaluated_rules.setdefault(node.id, []).append(result)

    def get_matching_rules(self, node: Node) -> List[Dict[str, Any]]:
        if not self.evaluated_rules.get(node.id):
            self.evaluate_all_rules(node)
        else:
            logger.info(f"Using cached rule evaluations for node: {node.name} (ID: {node.id})")
        return [result for result in self.evaluated_rules.get(node.id, []) if result.get('matches', False)]
