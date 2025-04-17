startup_message: str = """[bold magenta][u]This is the File Backup Service for Offline Video Preservation[/u][/bold magenta]

This service is [bold]scheduled to run every day at 8pm[/bold] via Windows Task Scheduler.  

The following processes will run:

1. [bold][u]MOV > FFV1 file transformation and backup service[/u][/bold]
    * FrameMD5 checksums generated for the 10-bit MOV files
    * Preservation FFV1 MKV files transcoded from the MOV files with frameMD5 checksums
    * The MOV and MKV frameMD5 checksums validated against each other
    * The MKV and their frameMD5 files moved up to [bold]_backup_storage[/bold] for offline preservation
    * The MOV files deleted from the [bold]staging_area[/bold]
    * Any failed files will move to the _quarantine folder for inspection

2. [bold][u]AVI file backup service[/u][/bold]
    * AVI files moved to the _backup_storage folder for offline preservation
    * Checksum files generated/validated for the AVI files
    * Any failed files will move to the _quarantine folder for inspection


[bold red]PLEASE DO NOT CLOSE THIS WINDOW UNTIL COMPLETE[/bold red]\n"""

mov_exit_message: str = "There are no MOV files in the staging area.  The [bold] MOV > FFV1 file transformation service will exit[/bold]."

avi_exit_message: str = "There are no AVI files in the staging area.  The [bold] AVI file backup service[/bold] will exit."

complete_message: str = (
    "[bold magenta]Processing complete[/bold magenta].  Press any key to exit"
)
