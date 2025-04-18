from pathlib import Path
from cli_git_changelog.utils.path_sourcing import resolve_highest_level_occurance_in_path, ensure_path_is_dir_or_create
import os


PROJECT_NAME = "cli_git_changelog"


def resolve_project_source() -> Path:
    """
    Resolve the project source directory.
    """
    return resolve_highest_level_occurance_in_path(Path(__file__).resolve(), PROJECT_NAME)


@ensure_path_is_dir_or_create
def resolve_component_dirs_path(component_name: str) -> Path:
    """
    Resolves the path to the directory containing the component's subdirectories.
    :param component_name: (str): The name of the component.
    :return: (Path): The path to the component's subdirectories.
    """
    return resolve_project_source() / component_name

# ----------------------------------------------------------------------------------------------------
# MARK: ENVIRONMENT VARIABLES - Management
# ----------------------------------------------------------------------------------------------------

# Concept - as this is the init of the application we want to just be able to run the dir and have it work
# So we need to load the .env file from the project root - this will manage it for the project

# DOTENV_PATH = resolve_project_source() / ".env"

# MARK: Now that the package is being installed in other projects it should use the .env 
# file at the current working directory

# load_dotenv(DOTENV_PATH)


API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL", "")
BASE_MODEL = os.getenv("BASE_MODEL", "claude-3-5-sonnet-latest")

def reload_env_vars():
    global BASE_URL, BASE_MODEL, API_KEY
    BASE_URL = os.getenv("BASE_URL", "")
    BASE_MODEL = os.getenv("BASE_MODEL", "claude-3-5-sonnet-latest")
    API_KEY = os.getenv("API_KEY")

