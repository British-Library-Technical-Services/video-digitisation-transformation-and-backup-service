from typing import Dict
import os
import logging
import subprocess

from BinarySwitches import transcode_to_mkv_switches

logger = logging.getLogger(__name__)

class FileTranscoder:
    def __init__(self, file: str, format: str) -> None:
        self.file: str = file
        self.format: str = format
        self.colour_data: Dict[str, str] = {}

    def colour_data_definition(self) -> None:
        if self.format == "PAL":
            self.colour_data = {
                "color_primaries": "bt470bg",
                "color_trc": "bt709",
                "colorspace": "bt470bg",
            }

        elif self.format == "NTSC":
            self.colour_data = {
                "color_primaries": "smpte170m",
                "color_trc": "bt709",
                "colorspace": "smpte170m",
            }

    def transcode_mov_to_mvk(self) -> None:
        try:
            subprocess.run(
                transcode_to_mkv_switches(self.file, self.colour_data)
            )
        except subprocess.CalledProcessError as spce:
            logger.exception(f"Subprocess Error: {spce}")