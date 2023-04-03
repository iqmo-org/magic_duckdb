import logging


def log_to_file(logfile: str):
    logger = logging.getLogger("magic_duckdb")
    logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler(logfile)
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
