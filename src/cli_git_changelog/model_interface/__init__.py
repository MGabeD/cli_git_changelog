from typing import Union
from cli_git_changelog.model_interface.anthropic_model import AnthropicModel
from cli_git_changelog.model_interface.model_interface import ModelInterface


model_map = {
    "claude": AnthropicModel,
}


def classify_model_name(model: str) -> str:
    model_name = model.lower()
    if "claude" in model_name:
        return "claude"
    return model_name


def get_model(api_url: Union[str, None] = None, api_key: Union[str, None] = None, model: Union[str, None] = None) -> ModelInterface:
    if model is None:
        raise ValueError("Model is required")
    map_model_name = classify_model_name(model)
    if map_model_name in model_map:
        return model_map[map_model_name](api_url, api_key, model)
    
    raise ValueError(f"Unsupported model: {model}")