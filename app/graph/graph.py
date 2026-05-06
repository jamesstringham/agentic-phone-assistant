from typing import Literal
from langgraph.graph import StateGraph, START, END

from app.graph import router_agent
from app.graph.state import CallState
from app.graph.specialists import business_info_specialist, schedule_specialist, confirmation_specialist, modify_specialist, cancel_specialist, lead_specialist, escalation_specialist
from app.graph.router_agent import RouterAgent

router_agent = RouterAgent()

def greet_and_route(state: CallState) -> CallState:
    print(f"[NODE] greet_and_route | user='{state.get('user_message')}'")

    user_message = state.get("user_message", "")
    decision = router_agent.route(user_message=user_message, state=state,)

    print(f"[ROUTER] route={decision['route']} | "
          f"name={decision.get('caller_name')} | "
          f"service={decision.get('requested_service')} | "
          f"date={decision.get('appointment_date')} | "
          f"time={decision.get('appointment_time')}")

    return {
        **state,
        "route": decision["route"],
        "caller_name": decision.get("caller_name") or state.get("caller_name"),
        "requested_service": decision.get("requested_service") or state.get("requested_service"),
        "appointment_date": decision.get("appointment_date") or state.get("appointment_date"),
        "appointment_time": decision.get("appointment_time") or state.get("appointment_time"),
    }


def business_info_agent(state: CallState) -> CallState:
    print("[NODE] business_info_agent")

    result = business_info_specialist.run(state)

    print(f"[AGENT] business_info → {result.get('assistant_message')}")

    return {
        **state,
        **result,
    }


def schedule_agent(state: CallState) -> CallState:
    print("[NODE] schedule_agent")

    result = schedule_specialist.run(state)


    print(f"[AGENT] schedule → {result.get('assistant_message')}")
    print(f"[STATE UPDATE] name={result.get('caller_name')} "
          f"service={result.get('requested_service')} "
          f"date={result.get('appointment_date')} "
          f"time={result.get('appointment_time')}")
    
    return {
        **state,
        **result,
    }


def modify_agent(state: CallState) -> CallState:
    print("[NODE] modify_agent")
    result = modify_specialist.run(state)
    print(f"[AGENT] modify → {result.get('assistant_message')}")
    return {
        **state,
        **result,
    }



def cancel_agent(state: CallState) -> CallState:
    print("[NODE] cancel_agent")
    result = cancel_specialist.run(state)
    print(f"[AGENT] cancel → {result.get('assistant_message')}")
    return {
        **state,
        **result,
    }


def lead_agent(state: CallState) -> CallState:
    print("[NODE] lead_agent")
    result = lead_specialist.run(state)
    print(f"[AGENT] lead → {result.get('assistant_message')}")
    return {
        **state,
        **result,
    }


def escalation_agent(state: CallState) -> CallState:
    print("[NODE] escalation_agent")
    result = escalation_specialist.run(state)
    print(f"[AGENT] escalation → {result.get('assistant_message')}")
    return {
        **state,
        **result,
    }


def confirmation_agent(state: CallState) -> CallState:
    print("[NODE] confirmation_agent")

    result = confirmation_specialist.run(state)

    print(f"[AGENT] confirmation → {result.get('assistant_message')}")
    print(f"[CONFIRMATION UPDATE] type={result.get('confirmation_type')} "
          f"needs_confirmation={result.get('needs_confirmation')}")

    return {
        **state,
        **result,
    }

def route_from_supervisor(state: CallState) -> Literal[
    "business_info_agent",
    "schedule_agent",
    "modify_agent",
    "cancel_agent",
    "lead_agent",
    "escalation_agent",
]:
    route = state.get("route", "business_info")

    mapping = {
        "business_info": "business_info_agent",
        "schedule": "schedule_agent",
        "modify": "modify_agent",
        "cancel": "cancel_agent",
        "lead": "lead_agent",
        "escalate": "escalation_agent",
        "confirmation": "confirmation_agent",
    }
    return mapping.get(route, "business_info_agent")


def should_go_to_confirmation(state: CallState) -> Literal["confirmation_agent", "write_memory"]:
    if state.get("needs_confirmation", False):
        return "confirmation_agent"
    return "write_memory"


def build_graph():
    graph = StateGraph(CallState)

    graph.add_node("greet_and_route", greet_and_route)
    graph.add_node("business_info_agent", business_info_agent)
    graph.add_node("schedule_agent", schedule_agent)
    graph.add_node("modify_agent", modify_agent)
    graph.add_node("cancel_agent", cancel_agent)
    graph.add_node("lead_agent", lead_agent)
    graph.add_node("escalation_agent", escalation_agent)
    graph.add_node("confirmation_agent", confirmation_agent)

    graph.add_edge(START, "greet_and_route")

    graph.add_conditional_edges(
        "greet_and_route",
        route_from_supervisor,
        {
            "business_info_agent": "business_info_agent",
            "schedule_agent": "schedule_agent",
            "modify_agent": "modify_agent",
            "cancel_agent": "cancel_agent",
            "lead_agent": "lead_agent",
            "escalation_agent": "escalation_agent",
            "confirmation_agent": "confirmation_agent",
        },
    )

    graph.add_conditional_edges(
        "business_info_agent",
        should_go_to_confirmation,
        {
            "confirmation_agent": "confirmation_agent",
            "__end__": END,
        },
    )

    graph.add_conditional_edges(
        "schedule_agent",
        should_go_to_confirmation,
        {
            "confirmation_agent": "confirmation_agent",
            "__end__": END,
        },
    )

    graph.add_conditional_edges(
        "modify_agent",
        should_go_to_confirmation,
        {
            "confirmation_agent": "confirmation_agent",
            "__end__": END,
        },
    )

    graph.add_conditional_edges(
        "cancel_agent",
        should_go_to_confirmation,
        {
            "confirmation_agent": "confirmation_agent",
            "__end__": END,
        },
    )

    graph.add_conditional_edges(
        "lead_agent",
        should_go_to_confirmation,
        {
            "confirmation_agent": "confirmation_agent",
            "__end__": END,
        },
    )

    graph.add_conditional_edges(
        "escalation_agent",
        should_go_to_confirmation,
        {
            "confirmation_agent": "confirmation_agent",
            "__end__": END,
        },
    )

    graph.add_edge("confirmation_agent", END)

    return graph.compile()