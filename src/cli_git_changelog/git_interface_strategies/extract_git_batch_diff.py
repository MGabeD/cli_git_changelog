import subprocess
from typing import Dict, Callable
from cli_git_changelog.utils.logger import get_logger


logger = get_logger(__name__)


def get_git_batch_diff(n: int, working_directory: str, clean_protocol: Callable[[str],str], reject_file_types: Callable[[str],bool]) -> Dict[str, Dict[str, dict]]:
    """
    Return a single entry keyed by the diff‑range (e.g. 'HEAD~3..HEAD') containing:
      - 'desc': concatenated commit subjects in the range
      - 'files': {file_path: (old_content_from_HEAD~n, cleaned_diff)}
    """
    range_spec = f"HEAD~{n}..HEAD"
    commits: Dict[str, Dict[str, dict]] = {range_spec: {"desc": "", "files": {}}}

    # Collect subjects for all commits in the range
    try:
        subjects = subprocess.check_output(
            ["git", "log", "--pretty=%s", range_spec],
            cwd=working_directory,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip().splitlines()
        commits[range_spec]["desc"] = "\n".join(subjects) if subjects else "(no commit messages)"
    except subprocess.CalledProcessError:
        logger.error("Failed to retrieve commit messages; are you in a git repo?")
        raise RuntimeError("Failed to retrieve commit messages; are you in a git repo?")

    # List affected files once for the whole range
    try:
        files = subprocess.check_output(
            ["git", "diff", "--name-only", range_spec],
            cwd=working_directory,
            stderr=subprocess.DEVNULL,
            text=True,
        ).splitlines()
    except subprocess.CalledProcessError:
        logger.error("Failed to list files changed in the batch diff.")
        raise RuntimeError("Failed to list files changed in the batch diff.")

    for fpath in files:
        if reject_file_types(fpath):
            continue

        # File content at the start of the range
        try:
            old_content = subprocess.check_output(
                ["git", "show", f"HEAD~{n}:{fpath}"],
                cwd=working_directory,
                stderr=subprocess.DEVNULL,
                text=True,
            )
        except subprocess.CalledProcessError:
            old_content = ""

        # Full diff for this file over the range
        try:
            raw_diff = subprocess.check_output(
                [
                    "git", "diff", "--unified=0", "--no-prefix", "--color=never",
                    f"HEAD~{n}", "HEAD", "--", fpath
                ],
                cwd=working_directory,
                stderr=subprocess.DEVNULL,
                text=True,
            )
            diff = clean_protocol(raw_diff)
        except subprocess.CalledProcessError:
            diff = ""

        commits[range_spec]["files"][fpath] = (old_content, diff)

    if not commits[range_spec]["files"]:
        raise RuntimeError("No changes found in the specified range.")
    return commits