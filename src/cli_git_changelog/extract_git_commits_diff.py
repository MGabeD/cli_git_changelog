import subprocess
import sys
from typing import Dict
from cli_git_changelog.utils.logger import get_logger


logger = get_logger(__name__)


METADATA_PREFIXES = ("diff --git", "index ", "@@ ", "+++ ", "--- ")


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


def get_git_commits(n: int, working_directory: str) -> Dict[str, Dict[str, dict]]:
    """
    :param n: Number of commits to get
    :param working_directory: Path in which to run all git commands
    :return: a dict mapping the last n commits to their message and file changes:
    Dict[str (commit_hashes): Dict[str (file_paths): Tuple[str (old_content), str (diff)] && str (desc) : commit message]]:
    """
    commits: Dict[str, Dict[str, dict]] = {}
    log_fmt = "--pretty=format:%H%x01%s"

    try:
        raw = subprocess.check_output(
            ["git", "log", f"-n{n}", log_fmt, "--date=short"],
            cwd=working_directory,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except subprocess.CalledProcessError:
        logger.error("Failed to run git log; are you in a repo?")
        sys.exit(1)

    for line in raw.splitlines():
        if not line.strip():
            continue
        commit_hash, message = line.split("\x01", 1)
        commits[commit_hash] = {"desc": message, "files": {}}

        try:
            files = subprocess.check_output(
                ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", commit_hash],
                cwd=working_directory,
                stderr=subprocess.DEVNULL,
                text=True,
            ).splitlines()
        except subprocess.CalledProcessError:
            files = []

        for fpath in files:
            try:
                old_content = subprocess.check_output(
                    ["git", "show", f"{commit_hash}^:{fpath}"],
                    cwd=working_directory,
                    stderr=subprocess.DEVNULL,
                    text=True,
                )
            except subprocess.CalledProcessError:
                old_content = ""

            try:
                raw_diff = subprocess.check_output(
                    [
                        "git", "diff", "--unified=0", "--no-prefix", "--color=never",
                        f"{commit_hash}^", commit_hash, "--", fpath
                    ],
                    cwd=working_directory,
                    stderr=subprocess.DEVNULL,
                    text=True,
                )
                try:
                    diff = clean_diff(raw_diff)
                except Exception as e:
                    logger.error(f"Failed to clean diff for {fpath}: {e}")
                    diff = raw_diff
            except subprocess.CalledProcessError:
                diff = ""

            commits[commit_hash]["files"][fpath] = (old_content, diff)

    if not commits:
        raise RuntimeError("No commits found.")
    return commits