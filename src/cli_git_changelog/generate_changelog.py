import os
from typing import Dict, List, Union
from cli_git_changelog.utils.logger import get_logger
from pathlib import Path
from datetime import datetime
from cli_git_changelog.extract_git_commits_diff import get_git_commits
from cli_git_changelog import BASE_URL
from cli_git_changelog.model_interface.model_interface import ModelInterface
from cli_git_changelog.formatters.changelog_prompt_formatters import build_file_change_summary_prompt, build_changelog_prompt, build_full_commit_batch_changelog_prompt
from cli_git_changelog.model_interface import get_model


logger = get_logger(__name__)


API_ENDPOINT = os.getenv("API_ENDPOINT", '')
API_URL = f"{BASE_URL}{API_ENDPOINT}"


def _lines(diff: str) -> int:
    """Count non‑blank lines in an already‑stripped diff."""
    return sum(1 for ln in diff.splitlines() if ln.strip())


def build_file_change_prompts(commit: dict) -> List[str]:
    prompts = []
    carry_over = [[],[]]
    for f, (old, diff) in commit['files'].items():
        if _lines(diff) < 5:
            continue
        if _lines(diff) < 10:
            carry_over[0].append(f)
            carry_over[1].append(diff)
            if sum(_lines(i) for i in carry_over[1]) > 1000:
                prompts.append(build_file_change_summary_prompt("\n".join(carry_over[0]), "\n".join(carry_over[1]), ""))
                carry_over = [[],[]]
            continue
        prompts.append(build_file_change_summary_prompt(f, old, diff))
    return prompts


def call_ai(
    model: ModelInterface,
    prompt: str,
    max_tokens: int = 4096,
    temperature: float = 0.5,
) -> str:
    try:
        res = model.call_model(prompt=prompt, max_tokens=max_tokens, temperature=temperature)
        if res is None:
            raise RuntimeError(f"Failed to get summary of {prompt}")
        return res
    except Exception as e:
        logger.error(f"Failed to get summary of {prompt}: {e}")
        return None


def configure_output_dirs(output_dir: Path):
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%dT%H%M%S")
    base_out = output_dir / ts
    commits_out = base_out / "commits"
    batch_out = base_out / "batch"
    commits_out.mkdir(parents=True, exist_ok=True)
    batch_out.mkdir(parents=True, exist_ok=True)
    return commits_out, batch_out


def create_commit_changelog(LLM_model: ModelInterface, commits_out: Union[str, Path], info: dict, sha: str):
    file_prompts = build_file_change_prompts(info)
    file_summaries: Dict[str, str] = {}
    file_paths = list(info["files"].keys())

    for idx, prompt in enumerate(file_prompts):
        summary = call_ai(LLM_model, prompt)
        if summary is not None:
            file_summaries[file_paths[idx]] = summary
            logger.info(f"File {file_paths[idx]} summary: {summary}")

    commit_prompt = build_changelog_prompt(file_summaries)
    commit_summary = call_ai(LLM_model, commit_prompt)
    if commit_summary is not None:
        (commits_out / f"{sha}.md").write_text(commit_summary)
        logger.info(f"Wrote {sha} to {commits_out / f'{sha}.md'}")
        return commit_summary
    return None


def create_changelog(api_key: str, model: str, working_directory: str, output_dir: Path, n_commits: int):
    try:
        commits = get_git_commits(n_commits, working_directory)
    except RuntimeError as e:
        logger.error(f"Error fetching commits: {e}")
        raise RuntimeError(f"Error fetching commits: {e}")

    commits_out, batch_out = configure_output_dirs(output_dir)
    commit_summaries: List[str] = []
    foo = API_URL
    logger.info(f"API_URL: {API_URL}")
    shas = list(commits.keys())
    LLM_model = get_model(api_url=API_URL, api_key=api_key, model=model)
    for sha in shas:
        info = commits[sha]
        commit_summary = create_commit_changelog(LLM_model, commits_out, info, sha)
        if commit_summary is not None:
            commit_summaries.append(commit_summary)

    first_sha, last_sha = shas[0], shas[-1]
    batch_prompt = build_full_commit_batch_changelog_prompt(commit_summaries)
    batch_summary = call_ai(LLM_model, batch_prompt, max_tokens=8192)

    batch_file = batch_out / f"{first_sha}-{last_sha}.md"
    batch_file.write_text(batch_summary)
    logger.info(f"Wrote {len(shas)} per‑commit files to {commits_out}")
    logger.info(f"Wrote batch summary to {batch_file}")
