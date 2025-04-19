from typing import Union
from cli_git_changelog.model_interface.anthropic_model import AnthropicModel
from cli_git_changelog.model_interface.model_interface import ModelInterface
from cli_git_changelog.utils.logger import get_logger


logger = get_logger(__name__)


model_map = {
    "claude": AnthropicModel,
}


def classify_model_name(model: str) -> str:
    """
    Classify the model name to a standard format. For example: claude-3-5-xxxx -> claude (its the same interface)
    """
    model_name = model.lower()
    if "claude" in model_name:
        return "claude"
    return model_name


def get_model(api_url: Union[str, None] = None, api_key: Union[str, None] = None, model: Union[str, None] = None) -> ModelInterface:
    """
    Get the model interface for the given model name. If the model name is not supported, raise an error.
    """
    if model is None:
        raise ValueError("Model is required")
    map_model_name = classify_model_name(model)
    if map_model_name in model_map:
        return model_map[map_model_name](api_url, api_key, model)
    logger.error(f"Unsupported model: {model}")
    raise ValueError(f"Unsupported model: {model}")