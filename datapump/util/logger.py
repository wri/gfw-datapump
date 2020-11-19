import logging
import os


if "ENV" in os.environ:
    ENV: str = os.environ["ENV"]
else:
    ENV = "dev"


def get_logger(name) -> logging.Logger:
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    sh: logging.StreamHandler = logging.StreamHandler()
    sh.setFormatter(formatter)

    logger: logging.Logger = logging.getLogger(name)
    logger.addHandler(sh)
    if ENV != "production":
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    return logger
