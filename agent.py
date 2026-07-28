from tools import get_eppo_names, get_scopus_string_and_count, get_wos_string_and_count

SYSTEM_PROMPT = """You are a research assistant.
- If the user asks for 'names' of an organism, use 'get_eppo_names' and stop. Include non-Latin script synonyms too.
- If the user asks for a 'search string' or 'number of papers' for Scopus, use get_scopus_string_and_count.
- If the user asks for a 'search string' or 'number of papers' for Web of Science (WoS), use get_wos_string_and_count.
- If not specified by the user, search for both Scopus and Web of Science (WoS) results.
- Answer in the same language as the user."""


def build_agent(model: str = "llama-3.3-70b-versatile", temperature: float = 0):
    llm = ChatGroq(model=model, temperature=temperature)
    return create_agent(
        llm,
        tools=[get_eppo_names, get_scopus_string_and_count, get_wos_string_and_count],
        system_prompt=SYSTEM_PROMPT
    )


def run_agent(agent, user_message: str) -> str:
    result = agent.invoke({"messages": [("user", user_message)]})
    return result["messages"][-1].content
