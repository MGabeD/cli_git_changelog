import argparse
import os
from pathlib import Path

from cli_git_changelog import BASE_MODEL, API_KEY, resolve_component_dirs_path, resolve_project_source
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
    return parser.parse_args()

def main():
    """
    Main entry point for the CLI application.
    """

    args = parse_args()
    # Mutes logging
    if args.quiet:
        os.environ["QUIET_MODE"] = "true"
    
    logger.info(f"API key: {args.api_key}")
    logger.info(f"API key: {API_KEY}")

    api_key = args.api_key or API_KEY
    if not api_key:
        raise ValueError("No API key provided; set --api-key or API_KEY in env")
    model = args.model_override 
    wd = args.wd_override 
    n_commits = args.commits 
    if any(i is None for i in [wd, model, api_key, n_commits]):
        raise ValueError("Missing required arguments")
    # I chose to do this way so I don't pollute my other projects in testing this
    output_dir = Path(args.output_dir) if args.output_dir else resolve_component_dirs_path("changelogs")
    output_dir.mkdir(parents=True, exist_ok=True)
    # No error handling here - they'll all just be dumped and I get no improved signal from catching here
    create_changelog(api_key, model, wd, output_dir, n_commits)

if __name__ == "__main__":
    logger.info("Starting CLI application")
    logger.info(f"resolve_project_source: {resolve_project_source()}")
    main()