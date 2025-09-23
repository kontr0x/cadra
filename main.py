import argparse
import json
import neo4j

from modules.logging_base import Logging
from models.neo4j import Path, UserPaths, User

logger = Logging().getLogger()


def get_direct_user_paths(session, username) -> list[neo4j.Record]:
    result = session.run("MATCH p=(n: User {name: $username})-[r]->() RETURN p", username=username)
    return list(result)


def get_user(session, username) -> neo4j.Record:
    result = session.run("MATCH (n: User {name: $username}) RETURN n LIMIT 1", username=username)
    return result.single()[0] if result.single() is not None else None


def main(neo4j_uri: str, neo4j_user: str, neo4j_password: str, name: str):
    logger.debug(f"Initializing neo4j driver...")
    driver = neo4j.GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    logger.debug(f"Neo4j driver initialized")

    with driver.session() as session:
        # Example query to verify connection
        result = session.run("RETURN 1 AS number")
        for record in result:
            if record["number"] == 1:
                logger.debug("Successfully connected to Neo4j database.")
            else:
                logger.error("Failed to connect to Neo4j database.")

        logger.debug(f"Fetching direct user paths for user: {name}")
        paths = get_direct_user_paths(session, name)

        user_paths: UserPaths
        user: User
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
                user = None

        print(user)
        if paths:
            for path in user_paths.paths:
                print(path)


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
         name=args.name
         )
    logger.info("CADRA finished.")
