from typing import List, Iterator, BinaryIO, TextIO
import os
import hashlib
import glob
import logging
import subprocess
import difflib

from BinarySwitches import framemd5_switches

logger: logging.Logger = logging.getLogger(__name__)


# class ChecksumService:
#     def __init__(self, file: str) -> None:
#         self.file: str = file
#         self.file_checksum: str = ""
#         self.file_copy: str = ""
#         self.verified_status: bool = False
#         self.failed_files: list[str] = []
#         self.framemd5_verified_status: bool = False

def generate_framemd5(file: str) -> None:
    try:
        subprocess.run(framemd5_switches(file))
    except subprocess.CalledProcessError as spce:
        logger.exception(f"Subprocess Error: {spce}")
    except FileNotFoundError as fnfe:
        logger.exception(f"File not found: {fnfe}")

def validate_framemd5(file: str) -> bool:
    mkv_framemd5: str = file.replace(".mov", ".mkv.framemd5")
    mov_framemd5: str = f"{file}.framemd5"
    framemd5_verified_status: bool = False

    try:
        with open(mkv_framemd5, encoding="utf-8") as f1, open(  # f1: TextIO
            mov_framemd5, encoding="utf-8"
        ) as f2:  # f2: TextIO
            mvk_data: List[str] = f1.readlines()
            mov_data: List[str] = f2.readlines()

        diff: Iterator[str] = difflib.unified_diff(mvk_data, mov_data)
        differences: List[str] = list(diff)

    except (FileNotFoundError, IOError) as e:
        logger.exception(f"Failed to open framemd5 files: {e}")

    if not differences:
        framemd5_verified_status = True
    else:
        logger.critical(
            f"ERROR: {mov_framemd5} does not match {mkv_framemd5}. Moving files to quaratine folder"
        )

    return framemd5_verified_status

def file_checksum_generate(file: str) -> str:
    file_hash: hash = hashlib.md5()
    try:
        with open(file, "rb") as f:  # f: BinaryIO
            while chunk := f.read(8192):  # chunk: bytes
                file_hash.update(chunk)
            file_checksum: str = file_hash.hexdigest()

        return file_checksum
    
    except FileNotFoundError as fnfe:
        logger.exception(f"File not found: {fnfe}")
    except IOError as ioe:
        logger.exception(f"IO Error: {ioe}")

def write_checksum_to_file(file: str, file_checksum: str) -> None:
    md5_file_name: str = f"{file}.md5"
    try:
        with open(md5_file_name, "w") as md5_file:  # md5_file: BinaryIO
            md5_file.write(f"{file_checksum} *{os.path.basename(file)}")
    
    except FileNotFoundError as fnfe:
        logger.exception(f"File not found: {fnfe}")
    except IOError as ioe:
        logger.exception(f"IO Error: {ioe}")

def file_checksum_verify(file: str, file_checksum: str) -> bool:
    md5_file_name: str = f"{file}.md5"
    verified_status: bool = False

    try:
        with open(md5_file_name, "r") as md5_file:  # md5_file: TextIO
            md5_string: str = md5_file.read(32)
            if file_checksum == md5_string:
                verified_status = True
                logger.info(f"Checksum verified for {file}. Moving files to backup location")
            else:
                logger.critical(
                    f"ERROR: {file} checksum failed to verify. Moving files to quarantine folder"
                )
        return verified_status

    except FileNotFoundError as fnfe:
        logger.exception(f"File not found: {fnfe}")
    except IOError as ioe:
        logger.exception(f"IO Error: {ioe}")
