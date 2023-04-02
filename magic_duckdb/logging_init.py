import logging
from typing import Optional

logger = None


def init_logging(logfile: Optional[str] = None) -> logging.Logger:
    global logger
    if logger is None:
        logger = logging.getLogger("magic_duckdb")
        logger.setLevel(logging.INFO)

        if logfile is not None:
            file_handler = logging.FileHandler(logfile)
            file_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )

            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger
