"""实用工具"""
import tiktoken
from langgraph.prebuilt import ToolNode
from langchain_core.runnables import RunnableLambda
from langchain_core.messages.tool import ToolMessage


def num_tokens_from_string(string: str, encoding_name: str = "davinci") -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.encoding_for_model(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


def handle_tool_error(state) -> dict:
    error = state.get("error")
    tool_calls = state["messages"][-1].tool_calls
    return {
        "messages": [
            ToolMessage(
                content=f"Error: {repr(error)}\n please fix your mistatkes.",
                tool_call_id=tc["id"]
            )
            for tc in tool_calls
        ]
    }


def create_tool_node_with_fallback(tools: list) -> dict:
    return ToolNode(tools).with_fallbacks(
        [RunnableLambda(handle_tool_error)], exception_key="error"
    )
    

def _print_event(event: dict, _printed: set, max_length=1500):
    current_state = event.get("dialogue_state")
    if current_state:
        print(f"Currently in: {current_state[-1]}")
    message = event.get("messages")
    if message:
        if isinstance(message, list):
            message = message[-1]
        if message.id not in _printed:
            msg_repr = message.pretty_repr(html=True)
            if len(msg_repr) > max_length:
                msg_repr = msg_repr[:max_length] + "...(truncated)"
            print(msg_repr)
            _printed.add(message.id)
            

def format_prompt(args_dict, prompt):
    for k,v in args_dict.items():
        prompt = prompt.replace(f"{{{k}}}", str(v))
    return prompt