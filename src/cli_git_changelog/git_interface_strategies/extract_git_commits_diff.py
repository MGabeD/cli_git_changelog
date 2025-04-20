import subprocess
from typing import Dict, Callable
from cli_git_changelog.utils.logger import get_logger


logger = get_logger(__name__)


def get_git_commits_diff(n: int, working_directory: str, clean_protocol: Callable[[str],str], reject_file_types: Callable[[str],bool]) -> Dict[str, Dict[str, dict]]:
    """
    :param n: Number of commits to get
    :param working_directory: Path in which to run all git commands
    :param clean_protocol: Function to clean the diff protocol
    :param reject_file_types: Function to reject file types
    :return: a dict mapping the last n commits to their message and file changes:
    Dict[str (commit_hashes): Dict[str (file_paths): Tuple[str (old_content), str (diff)] && str (desc) : commit message]]:
    """
    commits: Dict[str, Dict[str, dict]] = {}
    log_fmt = "--pretty=format:%H%x01%s"

    try:
        raw = subprocess.check_output(
            ["git", "log", f"-n{n}", log_fmt],
            cwd=working_directory,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except subprocess.CalledProcessError:
        logger.error("Failed to run git log; are you in a repo?")
        raise RuntimeError("Failed to run git log; are you in a repo?")

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
            if reject_file_types(fpath):
                continue

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
                    diff = clean_protocol(raw_diff)
                except Exception as e:
                    logger.error(f"Failed to clean diff for {fpath}: {e}")
                    diff = raw_diff
            except subprocess.CalledProcessError:
                diff = ""

            commits[commit_hash]["files"][fpath] = (old_content, diff)

    if not commits:
        raise RuntimeError("No commits found.")
    return commits