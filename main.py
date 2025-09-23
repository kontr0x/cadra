import argparse
import json
import neo4j

from modules.attribute_assessment import assess_user_attributes
from modules.logging_base import Logging
from modules.neo4j_utils import vertify_connection
from models.neo4j import Path, UserPaths, User
from modules.rule_engine import RuleEngine
from modules.permission_assessment import assess_permissions

logger = Logging().getLogger()


def get_direct_user_paths(session: neo4j.Session, username: str) -> list[neo4j.Record]:
    result = session.run("MATCH p=(n: User {name: $username})-[r]->() RETURN p", username=username)
    return list(result)


def get_user(session: neo4j.Session, username: str) -> neo4j.Record:
    result = session.run(
        "MATCH (n: User {name: $username}) RETURN n LIMIT 1", username=username).single()
    if result is None:
        return None
    return result[0]


def main(neo4j_uri: str, neo4j_user: str, neo4j_password: str, name: str, attributes_rules_dir_path: str,
         permission_rules_dir_path: str, event_monitoring_config: dict):
    logger.debug(f"Initializing neo4j driver...")
    driver = neo4j.GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    logger.debug(f"Neo4j driver initialized")

    attribute_rule_engine = RuleEngine()
    attribute_rule_engine.load_rules_from_directory(attributes_rules_dir_path)

    user_paths: UserPaths
    user: User

    with driver.session() as session:
        if not vertify_connection(session):
            logger.error("Could not connect to Neo4j database. Please check your configuration.")
            return

        logger.debug(f"Fetching direct user paths for user: {name}")
        paths = get_direct_user_paths(session, name)

        if paths:
            logger.info(f"Direct paths for user {name}:")
            user_paths = UserPaths(paths)
            user = user_paths.user
        else:
            user = get_user(session, name)
            if user:
                logger.info(f"User {name} found but has no direct paths.")
                user = User(user)
            else:
                logger.error(f"User {name} not found in the database.")
                return

    logger.debug(f"User object: {user}")
    adass_score = assess_user_attributes(user, attribute_rule_engine)
    logger.info(f"Attribute Assessment: {adass_score}")

    if paths:
        cadra_score = assess_permissions(
            user_paths.paths, permission_rules_dir_path, attribute_rule_engine, adass_score, event_monitoring_config)
        logger.info(f"CADRA Score: {cadra_score}")
    else:
        logger.info("User has no direct paths, skipping permission assessment.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="CADRA - A tool for assessing risks inside Active Directory environments")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("name", type=str,
                        help="The name of the user to analyze")

    args = parser.parse_args()

    # Read configuration from config file
    try:
        with open("config.json", "r") as config_file:
            config = json.load(config_file)
            neo4j_config = config.get("Neo4jConfig", {})
            rules_config = config.get("RulesConfig", {})
            event_monitoring_config = config.get("EventMonitoringConfig", {})
    except FileNotFoundError:
        raise Exception("Configuration file 'config.json' not found.")
    except json.JSONDecodeError:
        raise Exception("Error decoding 'config.json'. Please ensure it is valid JSON.")

    if args.verbose:
        Logging().set_console_log_level("DEBUG")

    logger.info("Starting CADRA...")
    main(neo4j_uri=neo4j_config.get("uri"),
         neo4j_user=neo4j_config.get("user"),
         neo4j_password=neo4j_config.get("password"),
         name=args.name,
         attributes_rules_dir_path=rules_config.get(
             "attributes_rules_dir_path", "rules/attributes"),
         permission_rules_dir_path=rules_config.get(
             "permissions_rules_dir_path", "rules/permissions"),
         event_monitoring_config=event_monitoring_config
         )
    logger.info("CADRA finished.")
