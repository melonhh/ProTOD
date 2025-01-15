import os

from src.utils.bot import AICall
from src.utils.tools import num_tokens_from_string


class DialogueHistory:
    def __init__(
            self,
            human_prefix: str = "user",
            assistant_prefix: str = "assistant",
            enable_llm_shorten: bool = False,
            max_dialogue_tokens: int = None,
            shorten_strategy: str = "cut",  # [cut, pure_both, pure_user],
            shorten_bot: AICall = None
    ):
        self.human_prefix = human_prefix
        self.assistant_prefix = assistant_prefix
        self.enable_llm_shorten = enable_llm_shorten
        self.max_dialogue_tokens = max_dialogue_tokens
        if self.max_dialogue_tokens:
            if shorten_strategy not in {"cut", "pure_both", "pure_user"}:
                raise ValueError(
                    f"Except `shortening_strategy` to be 'cut', 'pure_both' or 'pure_user, "
                    f"while got `{shorten_strategy}`, "
                )
            self.shorten_strategy = shorten_strategy
            if self.enable_llm_shorten:
                self._shorten_bot = shorten_bot
            else:
                self._shorten_bot = None
        self._shortened_dialogue_history: str = ""
        self._shortened_dialogue_turn: int = 0
        self.memory = []

    def clear(self) -> None:
        self._shortened_dialogue_history: str = ""
        self._shortened_dialogue_turn: int = 0
        self.memory = []

    def get(self) -> str:
        info = ""
        for m in self.memory[self._shortened_dialogue_turn:]:
            info += f"{m['role']}: {m['content']} \n"
        return self._shortened_dialogue_history + "\n" + info

    def append(self, role: str, message: str) -> None:
        assert role in {
            self.human_prefix,
            self.assistant_prefix
        }, f"role must be '{self.human_prefix}' or '{self.assistant_prefix}'"
        self.memory.append({"role": role, "content": message})
        if self.enable_llm_shorten:
            self.shorten()

    def shorten(self) -> None:
        total_dialogue = self.get()
        total_tokens = num_tokens_from_string(total_dialogue)
        if (self.max_dialogue_tokens is not None) and (total_tokens > self.max_dialogue_tokens):
            if self._shorten_bot:
                # TODO pure_both use LLM to purify the dialogues
                if self.shorten_strategy == "pure_both":
                    sys_prompt = (f"You are a helpful assistant to summarize conversation history "
                                  f"and make it shorter. The output should be like:"
                                  f"\n{self.human_prefix}: xxxx\n{self.assistant_prefix}: xxx. ")
                    user_prompt = (f"Please help me to shorten the conversational history below. "
                                   f"\n{total_dialogue}")
                # TODO pure_user
                else:
                    sys_prompt = ""
                    user_prompt = ""
                output = self._shorten_bot.call(
                    sys_prompt=sys_prompt,
                    user_prompt=user_prompt,
                    max_tokens=self.max_dialogue_tokens
                )
            else:
                # directly cut earlier dialogues
                dialogues = [f"{m['role']}: {m['content']}" for m in self.memory]
                _dialogue_str = "\n".join(dialogues)
                while num_tokens_from_string(_dialogue_str) > self.max_dialogue_tokens:
                    dialogues = dialogues[2:]
                    _dialogue_str = "\n".join(dialogues)
                output = _dialogue_str

            self._shortened_dialogue_history = output
            self._shortened_dialogue_turn = len(self.memory)
