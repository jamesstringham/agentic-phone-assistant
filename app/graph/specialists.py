from app.agents.agent import SpecialistAgent
from app.prompts.agent_prompts import BUSINESS_INFO_AGENT_PROMPT
from app.prompts.agent_prompts import SCHEDULE_AGENT_PROMPT
from app.prompts.agent_prompts import CONFIRMATION_AGENT_PROMPT
from app.prompts.agent_prompts import MODIFY_AGENT_PROMPT
from app.prompts.agent_prompts import CANCEL_AGENT_PROMPT
from app.prompts.agent_prompts import LEAD_AGENT_PROMPT
from app.prompts.agent_prompts import ESCALATION_AGENT_PROMPT

from app.tools.tool_schemas import TOOLS
from app.tools.dummy_tools import TOOL_MAP


def select_tools(*names: str) -> tuple[list[dict], dict]:
    selected_schema = []
    selected_map = {}

    for tool in TOOLS:
        fn_name = tool["function"]["name"]
        if fn_name in names:
            selected_schema.append(tool)
            if fn_name in TOOL_MAP:
                selected_map[fn_name] = TOOL_MAP[fn_name]

    return selected_schema, selected_map


business_info_schema, business_info_tool_map = select_tools(
    "search_knowledge_base"
)

schedule_schema, schedule_tool_map = select_tools(
    "schedule_appointment",
)

confirmation_schema, confirmation_tool_map = select_tools(
    "send_confirmation",
)

modify_schema, modify_tool_map = select_tools(
    "search_appointments",
    "reschedule_appointment",
)

cancel_schema, cancel_tool_map = select_tools(
    "search_appointments",
    "cancel_appointment",
)

lead_schema, lead_tool_map = select_tools(
    "create_lead",
    "create_callback_request",
)

escalation_schema, escalation_tool_map = select_tools(
    "create_callback_request",
)

business_info_specialist = SpecialistAgent(
    name="business_info",
    system_prompt=BUSINESS_INFO_AGENT_PROMPT,
    tools_schema=business_info_schema,
    tool_map=business_info_tool_map,
)

schedule_specialist = SpecialistAgent(
    name="schedule",
    system_prompt=SCHEDULE_AGENT_PROMPT,
    tools_schema=schedule_schema,
    tool_map=schedule_tool_map,
)

confirmation_specialist = SpecialistAgent(
    name="confirmation",
    system_prompt=CONFIRMATION_AGENT_PROMPT,
    tools_schema=confirmation_schema,
    tool_map=confirmation_tool_map,
)

modify_specialist = SpecialistAgent(
    name="modify",
    system_prompt=MODIFY_AGENT_PROMPT,
    tools_schema=modify_schema,
    tool_map=modify_tool_map,
)

cancel_specialist = SpecialistAgent(
    name="cancel",
    system_prompt=CANCEL_AGENT_PROMPT,
    tools_schema=cancel_schema,
    tool_map=cancel_tool_map,
)

lead_specialist = SpecialistAgent(
    name="lead",
    system_prompt=LEAD_AGENT_PROMPT,
    tools_schema=lead_schema,
    tool_map=lead_tool_map,
)

escalation_specialist = SpecialistAgent(
    name="escalation",
    system_prompt=ESCALATION_AGENT_PROMPT,
    tools_schema=escalation_schema,
    tool_map=escalation_tool_map,
)