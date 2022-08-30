import encodings
import logging
import os
import time
from typing import Optional

from naff import logger_name

class CustomLogger:

    def __init__(self):
        self.formatter = logging.Formatter(
            "%(asctime)s UTC || %(levelname)s || %(message)s"
        )
        self.formatter.converter = time.gmtime

    def make_logger(self, log_name: str):
        logger = logging.getLogger(log_name)
        logger.setLevel((logging.DEBUG))

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(self.formatter)
        console_handler.setLevel(logging.INFO)


        file_handler = MakeFileHandler(
            filename=f"./logs/{log_name}.log",
            encoding="utf-8",
        )
        file_handler.setFormatter(self.formatter)
        file_handler.setLevel(logging.ERROR)

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

class MakeFileHandler(logging.FileHandler):
    def __init__(
        self,
        filename: str,
        mode: str = "a",
        encoding: Optional[str] = None,
        delay: bool = False,
    ):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        logging.FileHandler.__init__(self, filename, mode, encoding, delay)


def init_logging():
    logger = CustomLogger()

    logger.make_logger(logger_name)