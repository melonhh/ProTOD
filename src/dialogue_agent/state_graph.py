"""StateGraph"""
from typing import Annotated, List, TypedDict

from langgraph.graph.message import AnyMessage, add_messages


class State(TypedDict):
    messages: Annotated[List[AnyMessage], add_messages]
    