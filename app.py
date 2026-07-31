#import libraries
import os
from dotenv import load_dotenv
from shiny import App, ui
from chatlas import ChatGroq
from faicons import icon_svg
from tools import get_eppo_names, get_scopus_string_and_count, get_wos_string_and_count

#load .env for future global variables
load_dotenv()

#welcome message
welcome = """
**Hello!** Do you need taxonomical or bibliometric information about a pest?

Here are a couple of suggestions:

* <span class="suggestion">Can you give me all the EPPO names of Coccus viridis?</span>
* <span class="suggestion submit">Can you give me the number of papers for Coccus viridis?</span>
"""

#UI logic
app_ui = ui.page_fillable(
    ui.div("Systematic Literature Review Research Assistant", style="text-align: center; font-size: 2rem;"),
    ui.chat_ui(
        "my_chat",
        messages=[welcome],
        icon_assistant=icon_svg("bug"),
    ),
    ui.input_password(
        "groq_key_input",
        "AI token",
        placeholder="Enter the key...",
    ),
    fillable_mobile=True,
)

#server logic
def server(input):
    chat = ui.Chat(id="my_chat")

    #api token
    @chat.on_user_submit
    async def handle_user_input(user_input: str):
        current_key = input.groq_key_input()
        if not current_key:
            await chat.append_message("Please enter your Groq API key first.")
            return

        #LLM setting
        chat_client = ChatGroq(
            api_key=current_key,
            model="qwen/qwen3.6-27b",
            system_prompt="""You are a research assistant.
                    - If the user asks for 'names' of an organism, use 'get_eppo_names' and stop. In this case don't exclude Non-Latin script synonyms.
                    - If the user asks for a 'search string' or 'number of papers' for Scopus, use get_scopus_string_and_count.
                    - If the user asks for a 'search string' or 'number of papers' for Web of Science (Wos), use get_wos_string_and_count.
                    - If not specified by the user search for both Scopus and Web of Science (Wos) results.
                    - Answer in the same language as the user."""
        )
        
        #LLM parameters and tools
        chat_client.set_model_params(temperature=0)
        chat_client.register_tool(get_scopus_string_and_count)
        chat_client.register_tool(get_wos_string_and_count)
        chat_client.register_tool(get_eppo_names)

        #stream the chat
        response = await chat_client.stream_async(user_input)
        await chat.append_message_stream(response)

#wrap the app
app = App(app_ui, server)