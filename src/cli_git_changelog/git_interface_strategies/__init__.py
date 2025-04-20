from pathlib import Path
from typing import Dict
from cli_git_changelog.git_interface_strategies.extract_git_commits_diff import get_git_commits_diff
from cli_git_changelog.git_interface_strategies.extract_git_batch_diff import get_git_batch_diff


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


def get_git_history_configured(n: int, working_directory: str, commit_strategy: bool = False) -> Dict[str, Dict[str, dict]]:
    if commit_strategy:
        return get_git_commits_diff(n, working_directory, clean_diff, reject_file_types)
    else:
        return get_git_batch_diff(n, working_directory, clean_diff, reject_file_types)

