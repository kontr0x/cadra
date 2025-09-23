from modules.logging_base import Logging

logger = Logging().getLogger()


def main():
    logger.info("Hello, CADRA!")


if __name__ == "__main__":
    logger.info("Starting CADRA...")
    main()
    logger.info("CADRA finished.")
