from rich import print
import time


def progress_bar(current, total, bar_length=20):
    current += 1
    percent = round(float(current) * 100 / total, 1)
    arrow = "-" * int(percent / 100 * bar_length - 1) + ">"
    spaces = " " * (bar_length - len(arrow))
    # if not current == total:
    print(
        f"[bold yellow]Processing: [{arrow}{spaces}] {percent}% [{current}/{total}][/bold yellow]",
        end="\r",
    )

def progress_complete(total):
    print(f"[bold green]Complete: [------------------->] 100 % [{total}/{total}]   [/bold green]")


# # Test the progress bar
# for i in range(101):
#     time.sleep(0.1)
#     progress_bar(i, 100)
