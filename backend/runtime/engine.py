from langchain_core.messages import HumanMessage
from sqlalchemy import select
from datetime import datetime

from backend.models.agent import Agent
from backend.models.workflow import Workflow
from backend.models.execution import Execution
from backend.models.message import Message
from backend.core.database import AsyncSessionLocal
from backend.core.websocket_manager import ws_manager
from backend.services.langfuse_service import get_langfuse
from .agent_builder import build_agent


async def run_workflow(execution_id: int, workflow: Workflow, input_text: str, _db=None):
    langfuse = get_langfuse()
    graph_json = workflow.graph_json
    nodes = {n["id"]: n for n in graph_json.get("nodes", [])}
    edges = graph_json.get("edges", [])
    order = _topological_sort(nodes, edges)

    trace_id = None
    current_text = input_text
    final_output = ""

    with langfuse.start_as_current_observation(
        as_type="span",
        name=f"workflow:{workflow.name}",
        metadata={"workflow_id": workflow.id, "execution_id": execution_id},
    ) as trace:
        trace_id = trace.trace_id

        for node_id in order:
            node = nodes[node_id]
            agent_id = node["agent_id"]

            # Fresh session per agent to avoid Neon idle timeout dropping the connection
            async with AsyncSessionLocal() as db:
                result_agent = await db.execute(select(Agent).where(Agent.id == agent_id))
                agent = result_agent.scalar_one_or_none()
                if not agent:
                    continue

                await ws_manager.broadcast("agent_start", {"agent": agent.name, "execution_id": execution_id})

                output = ""
                tokens = 0

                with langfuse.start_as_current_observation(
                    as_type="span",
                    name=f"agent:{agent.name}",
                    input=current_text,
                ) as span:
                    try:
                        graph = build_agent(agent)
                        config = {"configurable": {"thread_id": str(agent.id)}} if agent.memory_enabled else {}
                        result = await graph.ainvoke({"messages": [HumanMessage(content=current_text)]}, config=config)
                        output = result["messages"][-1].content
                        tokens = _extract_tokens(result)
                        span.update(output=output, usage={"total_tokens": tokens})
                    except Exception as e:
                        output = f"Agent error: {e}"
                        span.update(output=output)

                next_agent = _next_agent_name(node_id, edges, nodes)
                msg = Message(
                    execution_id=execution_id,
                    from_agent=agent.name,
                    to_agent=next_agent,
                    content=output,
                    tokens_used=tokens,
                )
                db.add(msg)
                await db.commit()

            await ws_manager.broadcast("agent_message", {
                "from": agent.name,
                "to": next_agent,
                "content": output,
                "tokens": tokens,
                "execution_id": execution_id,
            })

            current_text = output
            final_output = output

    # Final session to mark execution complete
    async with AsyncSessionLocal() as db:
        result_exec = await db.execute(select(Execution).where(Execution.id == execution_id))
        exec_row = result_exec.scalar_one()
        exec_row.status = "completed"
        exec_row.output_text = final_output
        exec_row.finished_at = datetime.utcnow()
        exec_row.langfuse_trace_id = trace_id
        await db.commit()

    langfuse.flush()
    await ws_manager.broadcast("execution_done", {"execution_id": execution_id, "output": final_output})
    return final_output


def _topological_sort(nodes: dict, edges: list) -> list:
    from collections import defaultdict, deque

    in_degree = {n: 0 for n in nodes}
    adj = defaultdict(list)

    for edge in edges:
        adj[edge["source"]].append(edge["target"])
        in_degree[edge["target"]] += 1

    queue = deque([n for n in nodes if in_degree[n] == 0])
    order = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for neighbor in adj[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    return order


def _extract_tokens(result: dict) -> int:
    try:
        usage = result.get("usage_metadata") or {}
        return usage.get("total_tokens", 0)
    except Exception:
        return 0


def _next_agent_name(node_id: str, edges: list, nodes: dict) -> str:
    for edge in edges:
        if edge["source"] == node_id:
            target = nodes.get(edge["target"], {})
            return str(target.get("agent_id", "output"))
    return "output"
