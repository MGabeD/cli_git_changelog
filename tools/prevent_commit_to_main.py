#!/usr/bin/env python3
import subprocess
import sys
from cli_git_changelog.utils.logger import get_logger


logger = get_logger(__name__, quiet_mode=False, disable_file_logging=True)


PROTECTED_BRANCHES = ["main", "master"]


def main():
    branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"]).decode().strip()
    if branch in PROTECTED_BRANCHES:
        logger.error(f"You cannot commit directly to '{branch}'. Please use a feature branch and submit a PR.")
        return 1
    logger.info(f"Committing to '{branch}'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
