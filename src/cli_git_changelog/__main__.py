import argparse
import time
import os
from pathlib import Path
from dotenv import load_dotenv
from cli_git_changelog import BASE_MODEL, API_KEY, reload_env_vars
from cli_git_changelog.generate_changelog import create_changelog
from cli_git_changelog.utils.logger import get_logger


logger = get_logger(__name__)


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
    return parser.parse_args()

def main():
    """
    Main entry point for the CLI application.
    """

    args = parse_args()
    # Mutes logging
    if args.quiet:
        os.environ["QUIET_MODE"] = "true"

    concurrency = not args.disable_concurency
    wd = args.wd_override 
    dotenv_path = Path(args.dotenv_path or wd + "/.env")
    load_dotenv(dotenv_path)
    reload_env_vars()

    api_key = args.api_key or API_KEY
    if not api_key:
        raise ValueError("No API key provided; set --api-key or API_KEY in env")
    model = args.model_override 
    n_commits = args.commits 
    if any(i is None for i in [wd, model, api_key, n_commits]):
        raise ValueError("Missing required arguments")
    # I chose to do this way so I don't pollute my other projects in testing this
    # output_dir = Path(args.output_dir) if args.output_dir else resolve_component_dirs_path("changelogs")

    # Changing this to a real module I can use in other projects so time to move past this to wherever someone is in their terminal
    output_dir = Path(args.output_dir) if args.output_dir else Path(wd + "/changelogs")
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Outputing to directory: {output_dir}")

    # No error handling here - they'll all just be dumped and I get no improved signal from catching here
    start_time = time.time()
    create_changelog(api_key, model, wd, output_dir, n_commits, concurrency)
    end_time = time.time()
    logger.info(f"Time taken: {end_time - start_time} seconds")

if __name__ == "__main__":
    main()