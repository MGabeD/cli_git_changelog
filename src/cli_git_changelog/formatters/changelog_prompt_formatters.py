from typing import Dict, List
from cli_git_changelog.formatters import CHANGELOG_EXAMPLE


def build_file_change_summary_prompt(file_name: str, full_file: str, changes: str) -> str:
    return (
        "You are a release manager. Given the following changes to your given file, "
        "generate a user‑friendly high level changelog grouped by type (e.g., Features, Fixes):\n\n"
        "Be very terse and concise. Only include the most important changes in the changelog."
        f"File changed: {file_name}\n{full_file}\n\nChanges:\n{changes}\n\n Changelog:"
    )


def build_changelog_prompt(changes_log = Dict[str, str]) -> str:
    return (
        "You are a release manager. Given the following changelogs of files, build a comprehensive changelog"
        " for all of the changes in the repo done by this commit. Please include a high level summary of the changes"
        f" in a form mimicking this example: {CHANGELOG_EXAMPLE}"
        "\n".join(f"File changed: {k}\nChanges: {v}" for k, v in changes_log.items()) +
        " Changelog:"
    )


def build_full_commit_batch_changelog_prompt(commits_changelogs: List[str]) -> str:
    return (
        "You are a release manager. Given the following changelogs of files, build a comprehensive changelog"
        " for all of the changes in the repo done by this commit. Please include a high level summary of the changes"
        f" in a form mimicking this example: {CHANGELOG_EXAMPLE}"
        " Join the following sub release change logs into a single release change log, only include the most important changes:"
        "\n".join(f"sub release change log: {v}" for v in commits_changelogs) +
        " Changelog:"
    )