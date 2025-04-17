from typing import Dict
import os
import logging
import subprocess

logger: logging.Logger = logging.getLogger(__name__)


class ExtractFormatData:
    def __init__(self, file: str) -> None:
        self.file: str = file
        self.file_data: subprocess.Popen | None = None
        self.results: Dict[str, str] = {}
        self.scan_line_format: str = ""  

    def read_file_data(self) -> None:
        try:
            self.file_data = subprocess.Popen(
                ["mediainfo", self.file],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as spce:
            logger.exception(f"Subprocess Error: {spce}")

    def parse_file_data(self) -> None:
        data_map: Dict[str, str] = {
            "Height": "height",
            "Width": "width",
        }

        self.results = {
            "height": "",
            "width": "",
        }

        try:
            for data in self.file_data.stdout.readlines(): # data: str
                data = data.decode(encoding="utf-8").strip()

                for key, value in data_map.items(): # key: str, value: str
                    if key in data:
                        self.results[value] = (
                            data.split(":")[1].strip().replace(" pixels", "")
                        )

        except UnicodeDecodeError as ude:
            logger.exception(f"Decode Error: {ude}")
        except ValueError as ve:
            logger.exception(f"Value Error: {ve}")
        except AttributeError as ae:
            logger.exception(f"Attibute Error: {ae}")

    def format_identification(self) -> None:
        if self.results["height"] == "576" and self.results["width"] == "720":
            self.scan_line_format = "PAL"

        elif self.results["height"] == "486" and self.results["width"] == "720":
            self.scan_line_format = "NTSC"
