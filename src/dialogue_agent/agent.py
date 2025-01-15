import os
import time
import logging
from typing import Dict

from langchain_core.language_models.chat_models import BaseChatModel

from src.dialogue_agent.memory.history import DialogueHistory
from src.utils.bot import get_openai_tokens

logger = logging.getLogger(__name__)


class DialogueAgent:
    def __init__(
            self,
            human_prefix: str = "user",
            assistant_prefix: str = "assistant",
            enable_llm_shorten: bool = False,
            shorten_strategy: str = "pure_both",
            reply_style: str = "detailed",
            max_dialogue_tokens: int = 1024,
            backbone_bot: BaseChatModel = None,
            shorten_bot: BaseChatModel = None,
            **kwargs,
    ):
        self.human_prefix = human_prefix
        self.assistant_prefix = assistant_prefix
        self.enable_llm_shorten = enable_llm_shorten
        assert shorten_strategy in {
            "cut",
            "pure_both",
            "pure_user"
        }, f"`shorten_strategy` should be `cut`, `pure_both` or `pure_user`, while got {shorten_strategy}"
        self.shorten_strategy = shorten_strategy
        assert reply_style in {
            "concise",
            "detailed",
        }, f"`reply_style` should be `concise` or `detailed`, while got {reply_style}`"
        self.reply_style = reply_style
        assert backbone_bot is not None, "backbond_bot should not be None"
        self.backbone_bot = backbone_bot
        # Dialogue history module
        self.history = DialogueHistory(
            human_prefix=self.human_prefix,
            assistant_prefix=self.assistant_prefix,
            enable_llm_shorten=self.enable_llm_shorten,
            shorten_strategy=self.shorten_strategy,
            max_dialogue_tokens=max_dialogue_tokens,
            shorten_bot=shorten_bot,
        )

        self.kwargs = kwargs

    def set_style(self, style: str):
        assert style in {
            "concise",
            "detailed"
        }, f"`reply_style` should be `concise` or `detailed`, while got {style}`"
        self.reply_style = style
        logger.debug(f"`reply_style` set to `{style}`")

    def clear(self):
        self.history.clear()
        logger.debug(f"`history` cleared")

    def run(self, inputs: Dict[str, str]) -> str:
        self.history.append(self.human_prefix, inputs['input'])
        result = self.backbone_bot.call(
            sys_prompt="",
            user_prompt=self.history.memory
        )
        return str(result)

    def run_gr(self, state):
        text = state[-1][0]
        logger.debug(
            f"\nProcessing run_gr, Input text: {text}\nCurrent state: {state}\n"
        )
        try:
            tic = time.time()
            with get_openai_tokens() as cb:
                response = self.run({"input": text.strip()})
                logger.debug(cb.get())
            toc = time.time()
            logger.debug(f"Time collapsed: {toc - tic:.2f}s")
        except Exception as e:
            logger.debug(f"Here is the exception: {e}")
            response = "Something went wrong, please try again."
        state[-1][-1] = response
        return state, state
