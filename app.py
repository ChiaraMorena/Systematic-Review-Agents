import os
from dotenv import load_dotenv
from shiny import App, ui
from chatlas import ChatGroq
from faicons import icon_svg

from tools import get_eppo_names, get_scopus_string_and_count, get_wos_string_and_count

# carica il file .env
load_dotenv()

# carica variabili globali
groq_key = os.getenv('GROQ_API_KEY')

welcome = """
**Hello!** Do you need bibliometric information about a pest?

Here are a couple suggestions:

* <span class="suggestion">Can you give me all the EPPO names of Coccus viridis?</span>
* <span class="suggestion submit">Can you give me the number of papers for Coccus viridis?</span>
"""

# UI dell'app: qui va definito il layout con il componente chat
app_ui = ui.page_fillable(
    ui.div("Systematic Literature Review Research Assistant", style="text-align: center; font-size: 2rem"),
    ui.chat_ui(
        "my_chat",
        messages=[welcome],
        icon_assistant=icon_svg("bug"),
    ),
    fillable_mobile=True,
)


# logica server: qui va creato il client e la logica della chat
def server(input):
    chat_client = ChatGroq(
        api_key=groq_key,
        model="qwen/qwen3.6-27b",
        system_prompt="""You are a research assistant.
                    - If the user asks for 'names' of an organism, use 'get_eppo_names' and stop. In this case don't exclude Non-Latin script synonyms.
                    - If the user asks for a 'search string' or 'number of papers' for Scopus, use get_scopus_string_and_count.
                    - If the user asks for a 'search string' or 'number of papers' for Web of Science (Wos), use get_wos_string_and_count.
                    - If not specified by the user search for both Scopus and Web of Science (Wos) results.
                    - Answer in the same language as the user."""
    )
    chat_client.set_model_params(temperature=0)

    chat_client.register_tool(get_scopus_string_and_count)
    chat_client.register_tool(get_wos_string_and_count)
    chat_client.register_tool(get_eppo_names)

    chat = ui.Chat(id="my_chat")

    @chat.on_user_submit
    async def handle_user_input(user_input: str):
        response = await chat_client.stream_async(user_input)
        await chat.append_message_stream(response)

# App finale: obbligatoria, senza questa riga l'app non parte
app = App(app_ui, server)