import argparse
import time
import os
from pathlib import Path
from dotenv import load_dotenv
from cli_git_changelog import BASE_MODEL, API_KEY, reload_env_vars



# ----------------------------------------------------------------------------------------------------
# MARK: CLI APPLICATION
# ----------------------------------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate an AI‑powered, hierarchical changelog for the last N Git commits."
    )
    parser.add_argument("-n", "--commits", type=int, default=1,
                        help="Number of commits to summarize")
    parser.add_argument("--wd-override", type=str, default=os.getcwd(),
                        help="Working directory to run git commands in")
    parser.add_argument("--model-override", type=str, default=BASE_MODEL,
                        help="Override which Claude model to call")
    parser.add_argument("--api-key", type=str,
                        help="Override API key (otherwise from env)")
    parser.add_argument("-o", "--output-dir", type=str,
                        help="Base output directory for changelog files")
    parser.add_argument("--quiet", action="store_true",
                        help="Quiet mode, no terminal logging")
    parser.add_argument("--dotenv-path", type=str,
                        help="Path to the .env file")
    parser.add_argument("--disable-concurency", action="store_true",
                        help="Disable concurency")
    
    # Create a subparser for concurrency-related arguments
    concurrency_group = parser.add_argument_group('Concurrency Options')
    concurrency_group.add_argument("--max-workers-per-commit", type=int,
                        help="Max workers per commit (only available when concurrency is enabled)")
    concurrency_group.add_argument("--max-commit-workers", type=int,
                        help="Max commit workers (only available when concurrency is enabled)")
    
    args = parser.parse_args()
    
    # Validate that worker arguments are only used when concurrency is enabled
    if args.disable_concurency and (args.max_workers_per_commit or args.max_commit_workers):
        parser.error("Worker-related arguments can only be set when concurrency is enabled (--disable-concurency is not set)")
    
    return args


def main():
    """
    Main entry point for the CLI application.
    """

    args = parse_args()
    # Mutes logging
    if args.quiet:
        os.environ["QUIET_MODE"] = "true"

    concurrency = not args.disable_concurency
    if concurrency:
        max_workers_per_commit = args.max_workers_per_commit or 5
        max_commit_workers = args.max_commit_workers or 2
    else:
        # This is truely unneccesary but I'm keeping it here for now just in case I change the downstream logic at some point
        max_workers_per_commit = 1
        max_commit_workers = 1

    wd = args.wd_override 
    dotenv_path = Path(args.dotenv_path or wd + "/.env")
    if args.dotenv_path is not None:
        load_dotenv(dotenv_path)
        reload_env_vars()
        api_key = args.api_key or os.getenv("API_KEY")
    else:
        api_key = args.api_key or API_KEY
    if not api_key:
        raise ValueError("No API key provided; set --api-key or API_KEY in env")
    model = args.model_override 
    n_commits = args.commits 
    if any(i is None for i in [wd, model, api_key, n_commits]):
        raise ValueError("Missing required arguments")

    # local import and configuration of logger to enable --quiet taget properly grab the env var
    from cli_git_changelog.utils.logger import get_logger
    logger = get_logger(__name__) 


    output_dir = Path(args.output_dir) if args.output_dir else Path(wd + "/changelogs")
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Outputing to directory: {output_dir}")

    # local import in order to have env vars properly loaded internally for the changelog module
    from cli_git_changelog.generate_changelog import create_changelog

    start_time = time.time()
    create_changelog(api_key, model, wd, output_dir, n_commits, concurrency, max_workers_per_commit, max_commit_workers)
    end_time = time.time()
    logger.info(f"Time taken: {end_time - start_time} seconds")

if __name__ == "__main__":
    main()