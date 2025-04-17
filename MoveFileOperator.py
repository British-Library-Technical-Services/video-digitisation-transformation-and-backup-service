from typing import List
import os
import shutil
import logging

logger: logging.Logger = logging.getLogger(__name__)


def get_files_to_move(file: str) -> List[str]:
    files_to_move: List[str] = [file]

    if file.endswith(".mov"):
        frame_md5: str = f"{file}.framemd5"
        mkv_file: str = file.replace(".mov", ".mkv")
        mkv_framemd5: str = f"{mkv_file}.framemd5"

        files_to_move.extend([frame_md5, mkv_file, mkv_framemd5])

    elif file.endswith(".mkv"):
        mkv_framemd5: str = f"{file}.framemd5"
        mkv_md5: str = f"{file}.md5"

        files_to_move.extend([mkv_framemd5, mkv_md5])

    else:
        checksum_file: str = f"{file}.md5"
        files_to_move.append(checksum_file)


def move_files(file_list: List[str], location: str):
    for file in file_list:
        try:
            shutil.move(file, os.path.join(location))
        except FileNotFoundError as fnfe:
            logger.critical(fnfe)
        except shutil.Error as se:
            logger.error(se)


def move_mov_to_quarantine(mov_list: List[str], quarantine_location: str) -> None:
    for file in mov_list:
        try:
            shutil.move(file, quarantine_location)
        except FileNotFoundError as fnfe:
            logger.critical(fnfe)
        except shutil.error as se:
            logger.error(se)


def file_cleanup(file_list: List[str]) -> None:
    for file in file_list:
        try:
            os.remove(file)
        except OSError as e:
            logger.error(e)
