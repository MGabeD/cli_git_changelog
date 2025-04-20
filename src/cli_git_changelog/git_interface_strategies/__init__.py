from pathlib import Path
from typing import Dict
from cli_git_changelog.git_interface_strategies.extract_git_commits_diff import get_git_commits_diff
from cli_git_changelog.git_interface_strategies.extract_git_batch_diff import get_git_batch_diff
from cli_git_changelog.utils.logger import get_logger
import functools
import subprocess


logger = get_logger(__name__)


METADATA_PREFIXES = ("diff --git", "index ", "@@ ", "+++ ", "--- ")
REJECT_FILE_TYPES = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp", ".mp4", ".mp3", ".wav", ".ogg", ".webm", ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".json", ".txt")


def clean_diff(raw: str) -> str:
    cleaned = []
    for ln in raw.splitlines():
        # keep the actual additions / deletions / context lines
        if ln.startswith(METADATA_PREFIXES):
            continue
        # Git sometimes adds this sentinel line:
        if ln == r"\ No newline at end of file":
            continue
        cleaned.append(ln)
    return "\n".join(cleaned)


def reject_file_types(file_path: str) -> bool:
    return Path(file_path).suffix.lower() in REJECT_FILE_TYPES


def clamp_commits_to_branch_depth(func):
    @functools.wraps(func)
    def wrapper(n: int, working_directory: str, *args, **kwargs):
        try:
            total_commits = int(subprocess.check_output(
                ["git", "rev-list", "--count", "HEAD"],
                cwd=working_directory
            ).decode().strip())

            if n > total_commits:
                logger.warn(
                    f"Requested {n} commits, but branch only has {total_commits}. "
                    f"Reducing to {total_commits}."
                )
                n = total_commits

        except subprocess.CalledProcessError:
            logger.error("Failed to count commits — are you in a Git repo?")
            raise

        return func(n, working_directory, *args, **kwargs)

    return wrapper


@clamp_commits_to_branch_depth
def get_git_history_configured(n: int, working_directory: str, commit_strategy: bool = False) -> Dict[str, Dict[str, dict]]:
    if commit_strategy:
        logger.info("Using commit strategy")
        return get_git_commits_diff(n, working_directory, clean_diff, reject_file_types)
    else:
        logger.info("Using batch strategy")
        # Batch strategy is using git indexing which id 0 indexed while the looping in the function is 1 indexed 
        # This is a design issue and will need ot be fixed if I want to expand this but since it is only 2 
        # strategies right now it isn't worth the refactor yet
        return get_git_batch_diff(n-1, working_directory, clean_diff, reject_file_types)
