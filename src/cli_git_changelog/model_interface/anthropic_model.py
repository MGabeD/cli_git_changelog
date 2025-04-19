import requests
import time
from typing import List
from anthropic import Anthropic, RateLimitError
from cli_git_changelog.model_interface.model_interface import ModelInterface
from cli_git_changelog.utils.logger import get_logger
from typing import Union
from ratelimit import limits, sleep_and_retry


logger = get_logger(__name__)


class AnthropicModel(ModelInterface):
    CALLS = 50
    PERIOD = 60
    MAX_RETRIES = 5

    def __init__(self, api_url: Union[str, None] = None, api_key: Union[str, None] = None, model: Union[str, None] = None) -> None:
        if api_url is not None and len(api_url) > 0:
            logger.warning(f"Anthropic API is auto interfered, overriding api_url: {api_url}")
            self.api_url = api_url
        else:
            self.api_url = "https://api.anthropic.com/v1/messages"
        if api_key is None:
            raise ValueError("API Key is required")
        self.api_key = api_key
        if model is None:
            self.model = "claude-3-5-sonnet-latest"
        else:
            self.model = model
        self.client = Anthropic(api_key=self.api_key)


    def call_model(self, prompt: str, temperature: float = 0.5, max_tokens: int = 4096) -> str:
        base_wait = 20  # seconds
        for attempt in range(self.MAX_RETRIES):
            try:
                return self.call_model_with_rate_limit(prompt, temperature, max_tokens)
            except RateLimitError:
                wait_time = base_wait * (attempt + 1)
                logger.warn(f"Rate limit hit (attempt {attempt + 1}/{self.MAX_RETRIES}). Sleeping for {wait_time}s...")
                time.sleep(wait_time)
            except Exception as e:
                err_msg = str(e).lower()
                if "rate" in err_msg and "limit" in err_msg:
                    wait_time = base_wait * (attempt + 1)
                    logger.warn(f"Rate limit-like error: {e} (attempt {attempt + 1}/{self.MAX_RETRIES}). Sleeping for {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise

        raise RuntimeError("Exceeded max retries due to rate limiting.")


    # Now even if I choose poor worker controls I can still handle not being rate limited
    @sleep_and_retry
    @limits(calls=CALLS, period=PERIOD)
    def call_model_with_rate_limit(self, prompt: str, temperature: float = 0.5, max_tokens: int = 4096) -> str:
        if temperature is None:
            temperature = 0.5
        if max_tokens is None or max_tokens == 0:
            max_tokens = 4096
        try:
            response = self.client.messages.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            res = "".join(block.text for block in response.content if hasattr(block, "text")).strip()
            if not res:
                raise Exception(f"Anthropic request failed: {res}")
            return res
        
        except RateLimitError as e:
            logger.warn(f"Anthropic rate limit hit: {e}")
            raise
        
        except Exception as e:
            logger.warn(f"Anthropic request failed: {e}")
            logger.warn("Falling back to raw HTTP request.")
            try:
                headers = {
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                }

                body = {
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                }

                try:
                    resp = requests.post(self.api_url, headers=headers, json=body, timeout=30)
                    resp.raise_for_status()
                except requests.exceptions.RequestException as e:
                    logger.error(f"Anthropic fallback HTTP request failed: {e}")
                    raise RuntimeError(f"Anthropic fallback HTTP request failed: {e}")

                data = resp.json()
                if "content" in data and isinstance(data["content"], List):
                    return "".join(block.get("text", "") for block in data["content"]).strip()

                logger.error(f"Unexpected API response: {data}")
                return None
            except Exception as e:
                logger.error(f"Anthropic request failed: {e}")
                return None