from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage
from .tools import get_tools
from backend.models.agent import Agent
from backend.core.config import get_settings

# One MemorySaver per agent_id so memory is isolated between agents
_memory_store: dict[int, MemorySaver] = {}


def build_agent(agent: Agent):
    settings = get_settings()
    llm = ChatOpenAI(model=agent.model, temperature=0, api_key=settings.openai_api_key)
    tools = get_tools(agent.tools or [])
    system_message = SystemMessage(content=agent.system_prompt)

    checkpointer = None
    if agent.memory_enabled:
        if agent.id not in _memory_store:
            _memory_store[agent.id] = MemorySaver()
        checkpointer = _memory_store[agent.id]

    graph = create_react_agent(
        model=llm,
        tools=tools,
        prompt=system_message,
        checkpointer=checkpointer,
    )
    return graph
