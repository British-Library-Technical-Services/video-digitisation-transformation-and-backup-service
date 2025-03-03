import os
import glob
import sys
import subprocess
import difflib
from dotenv import load_dotenv
import time
from datetime import datetime, timedelta
import shutil
import logging
from rich import print
from rich.prompt import Prompt

import messagingOperations as mo

from progressBar import progress_bar, progress_complete
from checksumoperations import ChecksumService

load_dotenv()

LOGS = os.getenv("LOGS")

logTS = datetime.now().strftime("%Y%m%d_%H.%M_log.log")
ROOT_LOCATION = os.getenv("LOGS")
log = os.path.join(LOGS, logTS)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    "%(asctime)s:%(module)s:%(funcName)s:%(levelname)s:%(message)s"
)
file_handler = logging.FileHandler(log)
# termainal_handler = logging.StreamHandler()

file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
# logger.addHandler(termainal_handler)


class VideoBackupService:
    def __init__(self):
        self.STAGING_AREA = os.getenv("STAGING_AREA")
        self.QUARANTINE = os.getenv("QUARANTINE")
        self.BACKUP_STORE = os.getenv("BACKUP_STORE")

        self.files_processed = []
        self.files_with_errors = {}

        self.SOURCE_MOV_FILES = glob.glob(self.STAGING_AREA + "/*.mov")
        self.SOURCE_AVI_FILES = glob.glob(self.STAGING_AREA + "/*.avi")

        self.cs = ChecksumService()

    def record_file_errors(self, file, error):
        if file in self.files_with_errors:
            self.files_with_errors[file].append(error)
        else:
            self.files_with_errors[file] = [error]

    def generate_framemd5(self, input_file):
        logger.info(f"Generating framemd5 for {os.path.basename(input_file)}")
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    "fatal",
                    "-i",
                    input_file,
                    "-f",
                    "framemd5",
                    # "-an", ## switch to exclude generating audio stream md5s
                    f"{input_file}.framemd5",
                ]
            )

        except Exception as e:
            logger.exception(f"Error: {e}")
            self.record_file_errors(input_file, e)

    def get_video_data(self, input_file):
        logger.info(f"Getting video data for {os.path.basename(input_file)}")
        try:
            file_data = subprocess.Popen(
                ["mediainfo", input_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
        except Exception as e:
            logger.exception(f"Error: {e}")
            self.record_file_errors(input_file, e)
            return

        data_map = {
            "Height": "height",
            "Width": "width",
        }

        results = {
            "height": "",
            "width": "",
        }

        for data in file_data.stdout.readlines():
            data = data.decode(encoding="utf-8").strip()

            for key, value in data_map.items():
                if key in data:
                    results[value] = data.split(":")[1].strip().replace(" pixels", "")

        if results["height"] == "576" and results["width"] == "720":
            format = "PAL"

        elif results["height"] == "486" and results["width"] == "720":
            format = "NTSC"

        logger.info(f"{os.path.basename(input_file)} format: {format}")
        return format

    def ffmpeg_transcode_to_ffv1(self, input_file, format):
        logger.info(f"Transcoding {os.path.basename(input_file)} to FFV1")
        if format == "PAL":
            colour_data = {
                "color_primaries": "bt470bg",
                "color_trc": "bt709",
                "colorspace": "bt470bg",
            }
        elif format == "NTSC":
            colour_data = {
                "color_primaries": "smpte170m",
                "color_trc": "bt709",
                "colorspace": "smpte170m",
            }
        else:
            logger.warning("File not PAL or NSTC format")
            return

        output_file = input_file.replace(".mov", ".mkv")

        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    "fatal",
                    "-i",
                    input_file,
                    "-map",
                    "0",
                    "-dn",
                    "-c:v",
                    "ffv1",
                    "-level",
                    "3",
                    "-g",
                    "1",
                    "-color_primaries",
                    colour_data["color_primaries"],
                    "-color_trc",
                    colour_data["color_trc"],
                    "-colorspace",
                    colour_data["colorspace"],
                    "-color_range",
                    "1",
                    "-slicecrc",
                    "1",
                    "-slices",
                    "24",
                    "-c:a",
                    "copy",
                    "-y",
                    output_file,
                    "-f",
                    "framemd5",
                    # "-an", ## switch to exclude generating audio stream md5s
                    f"{output_file}.framemd5",
                ]
            )
        except Exception as e:
            logger.exception(f"Error: {e}")
            self.record_file_errors(input_file, e)

    def validate_framemd5(self, input_file):

        mkv_file = input_file.replace(".mov", ".mkv")

        logger.info(
            f"Validating framemd5 {os.path.basename(mkv_file)} against {os.path.basename(input_file)}"
        )

        mkv_framemd5 = input_file.replace(".mov", ".mkv.framemd5")
        mov_framemd5 = f"{input_file}.framemd5"

        location = ""

        mkv_move = os.path.join(location, os.path.basename(mkv_file))
        mov_move = os.path.join(location, os.path.basename(input_file))

        try:
            with open(mkv_framemd5, encoding="utf-8") as f1, open(
                mov_framemd5, encoding="utf-8"
            ) as f2:
                mvk_data = f1.readlines()
                mov_data = f2.readlines()

            diff = difflib.unified_diff(mvk_data, mov_data)
            differences = list(diff)

            if differences:
                logger.critical(
                    f"Validation failed for {os.path.basename(mkv_file)}, moving files to quarantine"
                )
                self.record_file_errors(input_file, differences)

                location = self.QUARANTINE
                mkv_move = os.path.join(location, os.path.basename(mkv_file))
                mov_move = os.path.join(location, os.path.basename(input_file))

                shutil.move(input_file, mov_move)
                shutil.move(mov_framemd5, mov_move + ".framemd5")
                shutil.move(mkv_file, mkv_move)
                shutil.move(mkv_framemd5, mkv_move + ".framemd5")

            else:
                logger.info(
                    f"Validation passed for {os.path.basename(mkv_file)}, moving file to backup store"
                )

                location = self.BACKUP_STORE
                mkv_move = os.path.join(location, os.path.basename(mkv_file))
                mov_move = os.path.join(location, os.path.basename(input_file))

                shutil.move(mkv_file, mkv_move)
                shutil.move(mkv_framemd5, mkv_move + ".framemd5")
                os.remove(input_file)
                os.remove(mov_framemd5)
                logger.info(
                    f"{os.path.basename(input_file)} and {os.path.basename(mov_framemd5)} deleted)"
                )
                self.files_processed.append(os.path.basename(mkv_file))

        except Exception as e:
            logger.exception(f"Error: {e}")
            self.record_file_errors(input_file, e)

    def run_mov_backup_service(self):
        print("[bold]MOV > FFV1 file transformation and backup service[/bold]")
        if len(self.SOURCE_MOV_FILES) == 0:
            print(mo.mov_exit_message)
            return
        else:
            start_time = time.time()
            logger.info(f"{len(self.SOURCE_MOV_FILES)} MOV files will be processed")
            print(
                f"[bold]{len(self.SOURCE_MOV_FILES)}[/bold] file(s) in the staging area will be processed"
            )

            for index, file in enumerate(self.SOURCE_MOV_FILES):
                progress_bar(index, len(self.SOURCE_MOV_FILES))

                self.generate_framemd5(file)
                formattype = self.get_video_data(file)
                self.ffmpeg_transcode_to_ffv1(file, formattype)
                self.validate_framemd5(file)

            progress_complete(len(self.SOURCE_MOV_FILES))

            end_time = time.time() - start_time
            elapsed_time = timedelta(seconds=end_time)

            print(
                f"[bold green]Files successfully processed[/bold green]: {len(self.files_processed)}"
            )
            if len(self.files_with_errors) > 0:
                print(
                    f"[bold red]Files with errors:[/bold red] {len(self.files_with_errors)}, see log for details"
                )
            else:
                pass

            logger.info(f"Total time taken: {elapsed_time}")
            print(f"Total time taken: {elapsed_time}")

            # print(mo.complete_message)

    def run_avi_backup_service(self):
        print("\n[bold]AVI file backup service[/bold]")
        if len(self.SOURCE_AVI_FILES) == 0:
            print(mo.avi_exit_message)
            return
        else:
            start_time = time.time()
            logger.info(f"{len(self.SOURCE_AVI_FILES)} AVI files will be processed")
            print(
                f"[bold]{len(self.SOURCE_AVI_FILES)}[/bold] file(s) in the staging area will be processed"
            )

            for index, file in enumerate(self.SOURCE_AVI_FILES):
                progress_bar(index, len(self.SOURCE_AVI_FILES))
                checksum_file = f"{file}.md5"

                if not os.path.exists(checksum_file):
                    logger.warning(f"checksum file does not exist for {file}")
                    logger.info(f"generating md5 checksum for {file}")
                    self.cs.file_checksum_generate(file)
                    self.cs.write_checksum_to_file(file, checksum_file)

                location = self.BACKUP_STORE
                avi_file_backup = os.path.join(location, os.path.basename(file))

                logger.info(f"moving {file} to {self.BACKUP_STORE}")
                shutil.move(file, avi_file_backup)
                shutil.move(checksum_file, avi_file_backup + ".md5")

                logger.info(f"verifying checksum for {avi_file_backup}")
                self.cs.file_checksum_generate(avi_file_backup)
                self.cs.file_checksum_verify(avi_file_backup)

                if self.cs.verified_status:
                    logger.info(f"{avi_file_backup} checksum verified")
                    pass
                else:
                    logger.critical(
                        f"{avi_file_backup} checkum failed, moving to {self.QUARANTINE}"
                    )
                    location = self.QUARANTINE
                    avi_file_quarantine = os.path.join(location, os.path.basename(file))
                    shutil.move(avi_file_backup, avi_file_quarantine)
                    shutil.move(avi_file_backup + ".md5", avi_file_quarantine + ".md5")

            progress_complete(len(self.SOURCE_AVI_FILES))

            end_time = time.time() - start_time
            elapsed_time = timedelta(seconds=end_time)

            if self.cs.failed_files != []:
                print(
                    f"[bold red]AVI file backup has {len(self.cs.failed_files)} Failed files[/bold red]. See {self.QUARANTINE}"
                )
            else:
                print(
                    f"[bold green]All AVI files successfully copied to backup[/bold green]"
                )

            logger.info(f"Total time taken: {elapsed_time}")
            print(f"Total time taken: {elapsed_time}")


def main():
    vbs = VideoBackupService()

    print(mo.startup_message)
    vbs.run_mov_backup_service()
    vbs.run_avi_backup_service()

    Prompt.ask(mo.complete_message)

if __name__ == "__main__":
    main()
