from typing import Iterator
import logging
import os
from datetime import datetime
from dotenv import load_dotenv

def setup_logger() -> None:
    load_dotenv()

    try:
        LOGS: str = os.getenv("LOGS")
        if not LOGS:
            os.makedirs(LOGS)
        timestamp: str = datetime.now().strftime("%Y%m%d_%H.%M_log.log")
        log_file: str = os.path.join(LOGS, timestamp)
        
    except OSError as ose:
        print(f"Error: {ose}")
    except ValueError as ve:
        print(f"Environment variable error: {ve}")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s:%(module)s:%(funcName)s:%(levelname)s:%(message)s",
        handlers=[
            logging.FileHandler(log_file)
            ]
    )