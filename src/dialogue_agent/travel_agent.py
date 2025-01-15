"""zero-shot travel agent"""
import logging
import time
from typing import Literal
from langchain_core.messages import HumanMessage
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END, START, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

from src.dialogue_agent.state_graph import State
from src.tools.travel import handle_booking, search_stay
from src.utils.tools import create_tool_node_with_fallback


log = logging.getLogger(__name__)


class Assistant:
    def __init__(self, runnable: Runnable):
        self.runnable = runnable

    def __call__(self, state: State, config: RunnableConfig = None):
        while True:
            result = self.runnable.invoke(state)
            if not result.tool_calls and (
                not result.content
                or isinstance(result.content, list)
                and not result.content[0].get('text')
            ):
                messages = state["messages"] + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages}
            else:
                break
        return {"messages": result}


# Define the function that determines whether to continue or not
def should_continue(state: MessagesState) -> Literal["tools", END]:
    messages = state['messages']
    last_message = messages[-1]
    # If the LLM makes a tool call, then we route to the "tools" node
    if last_message.tool_calls:
        return "tools"
    # Otherwise, we stop (reply to the user)
    return END


def build_graph(llm):  
    primary_assistant_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "你是一个旅游行程规划智能客服，你可以帮助用户查询旅游信息，例如旅游线路、景点介绍、酒店预订等。你可以回答用户的问题，也可以根据用户的需求推荐相关的旅游信息。"
            ),
            ("placeholder", "{messages}")
        ]
    )
    
    tools = [search_stay, handle_booking]
    
    assistant_runnable = primary_assistant_prompt | llm.bind_tools(tools)
    
    workflow = StateGraph(MessagesState)
    
    # 定义节点
    workflow.add_node("agent", Assistant(assistant_runnable))
    workflow.add_node("tools", create_tool_node_with_fallback(tools))
    # 定义边
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
    )
    workflow.add_edge("tools", "agent")
    
    # memory = SqliteSaver.from_conn_string(":memory:")
    memory = MemorySaver()
    graph = workflow.compile(checkpointer=memory)
    
    return graph


class DialogueAgent:
    def __init__(self, llm):
        self.graph = build_graph(llm)
    
    def run(self, inputs):
        final_state = self.graph.invoke(
            {"messages": [HumanMessage(content=inputs['input'])]},
            config={"configurable": {"thread_id": 42}}
        )
        return final_state["messages"][-1].content
    
    def set_style(self, style):
        pass

    def clear(self):
        pass
    
    def run_gr(self, state):
        text = state[-1][0]
        log.debug(
            f"\nProcessing run_gr, Input text: {text}\nCurrent state: {state}\n"
        )
        try:
            tic = time.time()
            response = self.run({"input": text.strip()})
            toc = time.time()
            log.debug(f"Time collapsed: {toc - tic:.2f}s")
        except Exception as e:
            print(e)
            log.debug(f"Here is the exception: {e}")
            response = "Something went wrong, please try again."
        state[-1][-1] = response
        return state, state
