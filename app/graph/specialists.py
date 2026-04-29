from app.agents.agent import SpecialistAgent
from app.prompts.agent_prompts import BUSINESS_INFO_AGENT_PROMPT
from app.prompts.agent_prompts import SCHEDULE_AGENT_PROMPT

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
    "lookup_customer",
    "schedule_appointment",
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