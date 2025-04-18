from abc import abstractmethod
from typing import Protocol, runtime_checkable, Union

@runtime_checkable
class ModelInterface(Protocol):
    """Interface for model calls that must be implemented by any model provider."""

    @abstractmethod
    def __init__(self, api_url: Union[str, None] = None, api_key: Union[str, None] = None, model: Union[str, None] = None) -> None:
        """
        Initialize the model interface with required credentials and configuration.
        
        Args:
            API_URL: The base URL for the model API.
            API_KEY: The authentication key for accessing the model.
            MODEL: Identifier or name of the model to use.
        """
        ...

    @abstractmethod
    def call_model(self, prompt: str, temperature: Union[float, None] = 0.5, max_tokens: Union[int, None] = 4096) -> Union[str, None]:
        """
        Call the model with the given parameters.
        
        Args:
            prompt: The input prompt to send to the model
            temperature: Controls randomness in the output (0.0 to 1.0)
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            The model's response as a string
        """
        ...

