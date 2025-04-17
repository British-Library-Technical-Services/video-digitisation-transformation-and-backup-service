from typing import Tuple, List
import os
from dotenv import load_dotenv
from datetime import datetime
import logging
import glob
from rich import print
from tqdm import tqdm

import LoggingConfig
from ChecksumOperator import generate_framemd5, validate_framemd5, file_checksum_generate, write_checksum_to_file, file_checksum_verify
from FileAttributesOperator import ExtractFormatData
from FileTranscodeOperator import FileTranscoder
from MoveFileOperator import get_files_to_move, move_files, move_mov_to_quarantine, file_cleanup
import TextBillboards

def initialise_service() -> Tuple[logging.Logger, str, str, str]:
    load_dotenv()
    LoggingConfig.setup_logger()
    logger: logging.Logger = logging.getLogger(__name__)

    try:
        STAGING_DIR: str = os.getenv("STAGING_AREA")
        BACKUP_DIR: str = os.getenv("BACKUP_STORE")
        QUARANTINE: str = os.getenv("QUARANTINE")

    except ValueError as ve:
        logger.error(f"Environment variable error: {ve}")
        
    return logger, STAGING_DIR, BACKUP_DIR, QUARANTINE

def format_attributes(file: str) -> str:
    format_data: ExtractFormatData = ExtractFormatData(file)
    format_data.read_file_data()
    format_data.parse_file_data()
    format_data.format_identification()

    return format_data.scan_line_format

def transcode_to_mkv(file: str, video_standard: str) -> None:
    mov_to_mkv_transcoder: FileTranscoder = FileTranscoder(file=file, format=video_standard)
    mov_to_mkv_transcoder.colour_data_definition()
    mov_to_mkv_transcoder.transcode_mov_to_mvk()


def run_mov_file_service(file: str, backup_location: str, quarantine_location: str) -> None:
    generate_framemd5(file=file)
    video_format: str = format_attributes(file=file)
    transcode_to_mkv(file=file, video_standard=video_format)
    verified_framemd5: bool = validate_framemd5(file=file)

    move_list: List[str] = get_files_to_move(file=file)

    if not verified_framemd5:
        move_files(file_list=move_list, location=quarantine_location)
    else:
        mov_file: str = move_list[0]
        mov_framemd5: str = move_list[1]
        mkv_file: str = move_list[2]

        mkv_checksum: str = file_checksum_generate(file=mkv_file)
        write_checksum_to_file(file=mkv_file, file_checksum=mkv_checksum)
        mkv_move_list: List[str] = get_files_to_move(file=mkv_file)
        move_files(file_list=mkv_move_list, location=backup_location)

        mkv_file: str = os.path.join(backup_location, os.path.basename(mkv_file))
        mkv_verified_checksum: bool = file_checksum_verify(file=mkv_file, file_checksum=mkv_checksum)
        
        if not mkv_verified_checksum:
            failed_file_list: List[str] = get_files_to_move(file=mkv_file)
            move_files(file_list=failed_file_list, location=quarantine_location)
            move_mov_to_quarantine(mov_list=[mov_file, mov_framemd5], quarantine_location=quarantine_location)
        else:
            # file_cleanup(file_list=[mov_file, mov_framemd5])
            pass


def run_avi_file_service(file: str, backup_location: str, quarantine_location: str) -> None:
    avi_checksum: str = file_checksum_generate(file=file)
    write_checksum_to_file(file=file, file_checksum=avi_checksum)
    move_list: List[str] = get_files_to_move(file=file)
    move_files(file_list=move_list, location=backup_location)
    avi_file: str = os.path.join(backup_location, os.path.basename(file))
    avi_verified_checksum: bool = file_checksum_verify(file=avi_file, file_checksum=avi_checksum)
    
    if not avi_verified_checksum:
        failed_file_list: List[str] = get_files_to_move(file=avi_file)
        move_files(file_list=failed_file_list, location=quarantine_location)
    else:
        pass    

def main():
    logger, staging_area, backup_location, quarantine_location = initialise_service()

    print(TextBillboards.startup_message)

    MOV_FILES: List[str] = glob.glob(os.path.join(staging_area, "*.mov"))
    AVI_FILES: List[str] = glob.glob(os.path.join(staging_area, "*.avi"))

    if not MOV_FILES:
        print(TextBillboards.mov_exit_message)
    else:
        mov_file: str
        for mov_file in tqdm(MOV_FILES, desc="Processing MOV files"):
            run_mov_file_service(file=mov_file, backup_location=backup_location, quarantine_location=quarantine_location)

    if not AVI_FILES:
        print(TextBillboards.avi_exit_message)
    else:
        avi_file: str
        for avi_file in tqdm(AVI_FILES, desc="Processing AVI files"):
            run_avi_file_service(file=avi_file, backup_location=backup_location, quarantine_location=quarantine_location)


if __name__ == "__main__":
    main()
