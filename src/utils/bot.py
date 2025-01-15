"""api call"""
import time
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Dict, List, Tuple, Union

from loguru import logger
import openai
from openai import ChatCompletion, OpenAI

TOKEN_USAGE_VAR = ContextVar(
    "token_usage",
    default={
        "completion_tokens": 0,
        "prompt_tokens": 0,
        "total_tokens": 0,
        "OAI": 0,
    },
)


@contextmanager
def get_openai_tokens():
    TOKEN_USAGE_VAR.set({"completion_tokens": 0, "prompt_tokens": 0, "total_tokens": 0, "OAI": 0})
    yield TOKEN_USAGE_VAR
    TOKEN_USAGE_VAR.set({"completion_tokens": 0, "prompt_tokens": 0, "total_tokens": 0, "OAI": 0})


class AICall:
    def __init__(
        self,
        model: str,
        api_key: str,
        api_type: str = "open_ai",
        api_base: str = "https://api.openai.com/v1",
        temperature: float = 0.0,
        model_type: str = "chat_completion",
        max_tokens: int = 512,
        timeout: int = 60,
        retry_limits: int = 5,
        stop_words: Union[str, List[str]] = None,
    ) -> None:
        self.model = model
        self.api_key = api_key
        self.api_type = api_type if api_type else "open_ai"
        self.api_base = api_base if api_base else "https://api.openai.com/v1"
        self.temperature = temperature
        self.model_type = model_type
        self.retry_limits = retry_limits
        self.timeout = timeout
        self.stop_words = stop_words
        self.max_tokens = max_tokens

        if (self.api_type) and (self.api_type not in {"open_ai", "azure"}):
            raise ValueError(
                f"Only open_ai/azure API are supported, while got {api_type}."
            )

        model_type = "chat_completion" if "chat" in model_type else model_type
        if model_type not in {"chat_completion", "completion"}:
            raise ValueError(
                f"Only chat_completion and completion types are supported, while got {model_type}"
            )
        
        self.client = OpenAI(api_key=self.api_key, base_url=self.api_base)

    def call(
            self,
            user_prompt: Union[str, list],
            sys_prompt: str="You are a helpful assistent.",
            max_tokens: int = None,
            temperature: float = None
            ) -> str:
        errors = [
            openai.Timeout,
            openai.APIError,
            openai.APIConnectionError,
            openai.RateLimitError,
        ]
        temperature = temperature if (temperature is not None) else self.temperature
        max_tokens = max_tokens if (max_tokens is not None) else self.max_tokens
        retry = False
        success = False
        sleep_time = 2
        for _ in range(self.retry_limits):
            try:
                if self.model_type.startswith("chat"):
                    prompt = [
                            {
                                "role": "system",
                                "content": sys_prompt
                            }
                        ]
                    if isinstance(user_prompt, str):
                        prompt.append(
                            {
                                "role": "user",
                                "content": user_prompt
                            }
                        )
                    else:
                        prompt.extend(user_prompt)
                    result = self._chat_completion(prompt, max_tokens, temperature)
                else:
                    prompt = f"{sys_prompt} {user_prompt}"
                    result = self._completion(prompt, max_tokens, temperature)
                if result[0]:  # content is not None
                    success = True
                    break
            except Exception as e:
                logger.error(e)
                for err in errors:
                    if isinstance(e, err):
                        retry = True
                        break
                if retry:
                    result = "Something went wrong, please retry.", {}
                    time.sleep(sleep_time)
                    sleep_time = min(1.5 * sleep_time, 10)
                else:
                    raise e

        # token usage update
        _prev_usuage = TOKEN_USAGE_VAR.get()
        _total_usuage = {
            k: _prev_usuage.get(k, 0) + getattr(result[1], k, 0)
            for k in _prev_usuage.keys()
            if "token" in k
        }
        _total_usuage["OAI"] = _prev_usuage.get("OAI", 0) + 1
        TOKEN_USAGE_VAR.set(_total_usuage)
        
        if not success:
            reply = "Something went wrong, please retry."
        else:
            reply = result[0]
        return reply


    def _chat_completion(self, msgs: List, max_tokens: int, temperature: float) -> Tuple[str, Dict]:
        kwargs = {
            "model": self.model,
            "messages": msgs,
            "temperature": temperature,
            "timeout": self.timeout,
            "max_tokens": max_tokens,
        }
        if self.api_type != "open_ai":
            kwargs["engine"] = self.model
        if self.stop_words:
            kwargs["stop"] = self.stop_words
        resp = self.client.chat.completions.create(**kwargs)
        print(resp)
        content = resp.choices[0].message.content
        usage = resp.usage
        return content, usage

    def _completion(self, prompt: str, max_tokens: int, temperature: float) -> Tuple[str, Dict]:
        kwargs = {
            "model": self.model,
            "prompt": prompt,
            "temperature": temperature,
            "timeout": self.timeout,
            "max_tokens": max_tokens,
        }
        if self.api_type != "open_ai":
            kwargs["engine"] = self.model
        if self.stop_words:
            kwargs["stop"] = self.stop_words
        resp = self.client.completions.create(**kwargs)
        content = resp.choices[0].text
        usage = resp.usage

        return content, usage


__all__ = ["AICall", "get_openai_tokens"]


if __name__ == "__main__":

    # personal OpenAI key
    personal_api_key = "sk-zk226cfbfd412c556205a3a5d139989e93b677b729db741d"
    llm = AICall(
        model="gpt-3.5-turbo-instruct", api_key=personal_api_key, api_base='https://api.zhizengzeng.com/v1/', model_type="completion"
    )

    prompt_msgs = "Which city is the capital of the US?"

    print("OpenAI: ", llm.call(prompt_msgs, temperature=0.0))