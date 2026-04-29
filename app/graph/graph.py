from typing import Literal
from langgraph.graph import StateGraph, START, END

from app.graph import router_agent
from app.graph.state import CallState
from app.graph.specialists import business_info_specialist, schedule_specialist
from app.graph.router_agent import RouterAgent

router_agent = RouterAgent()

def load_caller_context(state: CallState) -> CallState:
    return {
        **state,
        "known_customer": state.get("known_customer", False),
    }


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

    answer = "I can help reschedule your appointment. What date or time would you like to change it to?"
    return {
        **state,
        "assistant_message": answer,
        "needs_confirmation": False,
    }


def cancel_agent(state: CallState) -> CallState:
    print("[NODE] cancel_agent")
    answer = "I can help cancel that appointment. Can you confirm the appointment date or the name on the booking?"
    return {
        **state,
        "assistant_message": answer,
        "needs_confirmation": False,
    }


def lead_agent(state: CallState) -> CallState:
    print("[NODE] lead_agent")
    answer = "I'd be happy to help with that. Can I get your name and the reason you're reaching out today?"
    return {
        **state,
        "assistant_message": answer,
        "needs_confirmation": False,
    }


def escalation_agent(state: CallState) -> CallState:
    print("[NODE] escalation_agent")
    answer = "I can arrange a callback from a member of the team. What is the best number to reach you, and what is this regarding?"
    return {
        **state,
        "assistant_message": answer,
        "needs_confirmation": False,
    }


def confirmation_agent(state: CallState) -> CallState:
    print("[NODE] confirmation_agent")
    confirmation_type = state.get("confirmation_type", "sms")

    if confirmation_type == "sms":
        answer = "I've sent a confirmation by text message."
    else:
        answer = "Your confirmation has been recorded."

    return {
        **state,
        "assistant_message": answer,
    }


def write_memory(state: CallState) -> CallState:
    summary = (
        f"Caller={state.get('caller_name', 'unknown')}; "
        f"route={state.get('route', 'unknown')}; "
        f"service={state.get('requested_service', '')}; "
        f"appointment_date={state.get('appointment_date', '')}; "
        f"appointment_time={state.get('appointment_time', '')}"
    )

    # later:
    # store_call_summary(phone=state["caller_phone"], summary=summary)

    return {
        **state,
        "memory_summary": summary,
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
    }
    return mapping.get(route, "business_info_agent")


def should_go_to_confirmation(state: CallState) -> Literal["confirmation_agent", "write_memory"]:
    if state.get("needs_confirmation", False):
        return "confirmation_agent"
    return "write_memory"


def build_graph():
    graph = StateGraph(CallState)

    graph.add_node("load_caller_context", load_caller_context)
    graph.add_node("greet_and_route", greet_and_route)
    graph.add_node("business_info_agent", business_info_agent)
    graph.add_node("schedule_agent", schedule_agent)
    graph.add_node("modify_agent", modify_agent)
    graph.add_node("cancel_agent", cancel_agent)
    graph.add_node("lead_agent", lead_agent)
    graph.add_node("escalation_agent", escalation_agent)
    graph.add_node("confirmation_agent", confirmation_agent)
    graph.add_node("write_memory", write_memory)

    graph.add_edge(START, "load_caller_context")
    graph.add_edge("load_caller_context", "greet_and_route")

    graph.add_conditional_edges(
        "greet_and_route",
        route_from_supervisor,
    )

    graph.add_conditional_edges("business_info_agent", should_go_to_confirmation)
    graph.add_conditional_edges("schedule_agent", should_go_to_confirmation)
    graph.add_conditional_edges("modify_agent", should_go_to_confirmation)
    graph.add_conditional_edges("cancel_agent", should_go_to_confirmation)
    graph.add_conditional_edges("lead_agent", should_go_to_confirmation)
    graph.add_conditional_edges("escalation_agent", should_go_to_confirmation)

    graph.add_edge("confirmation_agent", "write_memory")
    graph.add_edge("write_memory", END)

    return graph.compile()