import os
from concurrent.futures import ThreadPoolExecutor, as_completed
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


def call_model(
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


def configure_output_dirs(output_dir: Path, disable_commit_writing: bool = False, disable_batch_writing: bool = False):
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%dT%H%M%S")
    base_out = output_dir / ts
    commits_out = base_out / "commits"
    batch_out = base_out / "batch"
    if not disable_commit_writing:
        commits_out.mkdir(parents=True, exist_ok=True)
    if not disable_batch_writing:
        batch_out.mkdir(parents=True, exist_ok=True)
    return commits_out, batch_out


def create_commit_changelog(LLM_model: ModelInterface, commits_out: Union[str, Path], info: dict, sha: str, concurrency: bool = False, max_workers_per_commit: int = 5, disable_commit_writing: bool = False):
    file_prompts = build_file_change_prompts(info)
    file_summaries: Dict[str, str] = {}
    file_paths = list(info["files"].keys())

    if concurrency:
        with ThreadPoolExecutor(max_workers=max_workers_per_commit) as executor:
            futures = {
                executor.submit(call_model, LLM_model, prompt): idx
                for idx, prompt in enumerate(file_prompts)
            }
            for future in as_completed(futures):
                idx = futures[future]
                try:
                    summary = future.result()
                    if summary is not None:
                        file_summaries[file_paths[idx]] = summary
                        logger.info(f"File {file_paths[idx]} summary: {summary}")
                except Exception as e:
                    logger.error(f"Failed to summarize {file_paths[idx]}: {e}")
    else:
        for idx, prompt in enumerate(file_prompts):
            summary = call_model(LLM_model, prompt)
            if summary is not None:
                file_summaries[file_paths[idx]] = summary
                logger.info(f"File {file_paths[idx]} summary: {summary}")

    commit_prompt = build_changelog_prompt(file_summaries)
    commit_summary = call_model(LLM_model, commit_prompt)
    if commit_summary is not None:
        if not disable_commit_writing:
            (commits_out / f"{sha}.md").write_text(commit_summary)
            logger.info(f"Wrote {sha} to {commits_out / f'{sha}.md'}")
        return commit_summary

    return None


def create_changelog(api_key: str, model: str, working_directory: str, output_dir: Path, n_commits: int, concurrency: bool, max_workers_per_commit: int, max_commit_workers: int, disable_commit_writing: bool = False, disable_batch_writing: bool = False, batch_output_override: Union[str, Path, None] = None):
    try:
        commits = get_git_commits(n_commits, working_directory)
    except RuntimeError as e:
        logger.error(f"Error fetching commits: {e}")
        raise RuntimeError(f"Error fetching commits: {e}")

    commits_out, batch_out = configure_output_dirs(output_dir, disable_commit_writing, disable_batch_writing)

    commit_summaries: List[str] = []
    shas = list(commits.keys())
    LLM_model = get_model(api_url=API_URL, api_key=api_key, model=model)
    if concurrency:
        logger.warning(f"Running with concurrency: Max workers per commit: {max_workers_per_commit} & Max commit workers: {max_commit_workers}")
        with ThreadPoolExecutor(max_workers=max_commit_workers) as executor:
            future_to_sha = {
                executor.submit(create_commit_changelog, LLM_model, commits_out, commits[sha], sha, concurrency, max_workers_per_commit, disable_commit_writing): sha
                for sha in shas
            }
            for future in as_completed(future_to_sha):
                sha = future_to_sha[future]
                try:
                    commit_summary = future.result()
                    if commit_summary is not None:
                        commit_summaries.append(commit_summary)
                except Exception as e:
                    logger.error(f"Error creating commit summary for {sha}: {e}")
    else:
        for sha in shas:
            info = commits[sha]
            commit_summary = create_commit_changelog(LLM_model, commits_out, info, sha, disable_commit_writing)
            if commit_summary is not None:
                commit_summaries.append(commit_summary)

    if not disable_batch_writing:
        first_sha, last_sha = shas[0], shas[-1]
        batch_prompt = build_full_commit_batch_changelog_prompt(commit_summaries)
        batch_summary = call_model(LLM_model, batch_prompt, max_tokens=8192)
        if batch_output_override is None:
            batch_file = batch_out / f"{first_sha}-{last_sha}.md"
            batch_file.write_text(batch_summary)
        else:
            try:
                Path(batch_output_override).write_text(batch_summary)
            except Exception as e:
                logger.error(f"Error writing batch file: {e}")
                raise RuntimeError(f"Error writing batch file: {e}")
        logger.info(f"Wrote {len(shas)} per‑commit files to {commits_out}")
        logger.info(f"Wrote batch summary to {batch_file}")
    else:
        logger.warning("Batch writing is disabled, skipping batch file creation and model call")
