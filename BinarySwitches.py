from typing import List


def framemd5_switches(file: str) -> List[str]:
    framemd5_switches: List[str] = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "fatal",
        "-i",
        file,
        "-f",
        "framemd5",
        # "-an", ## switch to exclude generating audio stream md5s
        "-y",
        f"{file}.framemd5",
    ]
    return framemd5_switches


def transcode_to_mkv_switches(file: str, colour_data: str) -> List[str]:
    output_file: str = file.replace(".mov", ".mkv")
    transcode_to_mkv_switches: List[str] = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "fatal",
        "-i",
        file,
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

    return transcode_to_mkv_switches
