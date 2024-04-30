import os
import json
import streamlit as st
import requests

from typing import List
from dotenv import load_dotenv

from langchain.tools.render import render_text_description
from langchain_openai import ChatOpenAI, OpenAI
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.exceptions import OutputParserException
from langchain_core.output_parsers import (
    BaseGenerationOutputParser,
    JsonOutputParser,
    StrOutputParser,
)
from langchain_core.outputs import ChatGeneration, Generation
from langchain_core.runnables import (
    RunnableParallel,
)
from langchain_core.runnables.history import RunnableWithMessageHistory

from history import CustomStreamlitChatMessageHistory

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(
    page_title="Quadz AI Bot",
    page_icon="🦜",
    layout="wide",
    menu_items={
        "Get Help": "https://quadz.arthink.ai",
        "Report a bug": "https://quadz.arthink.ai",
        "About": "Quadz AI Agent [BETA]",
    },
)
st.title("Quadz AI Bot")

# Setup agents
llm = ChatOpenAI(
    model="gpt-4-turbo",
    openai_api_key=openai_api_key,
    temperature=0,
    streaming=True,
)
llm_2 = OpenAI(
    openai_api_key=openai_api_key,
    temperature=0,
    streaming=True,
)


class CustomOutputParser(BaseGenerationOutputParser[str]):
    """An example parser that inverts the case of the characters in the message.

    This is an example parse shown just for demonstration purposes and to keep
    the example as simple as possible.
    """

    def parse_result(self, result: List[Generation], *, partial: bool = False) -> str:
        """Parse a list of model Generations into a specific format.

        Args:
            result: A list of Generations to be parsed. The Generations are assumed
                to be different candidate outputs for a single model input.
                Many parsers assume that only a single generation is passed it in.
                We will assert for that
            partial: Whether to allow partial results. This is used for parsers
                     that support streaming
        """
        if len(result) != 1:
            raise NotImplementedError(
                "This output parser can only be used with a single generation."
            )
        generation = result[0]
        if isinstance(generation, ChatGeneration):
            return generation.message.content
        if isinstance(generation, dict):
            return generation
        else:
            raise OutputParserException(
                "This output parser can only be used with a chat generation."
            )


@tool
def db_data(input_query: str) -> list:
    """Returns DB data by taking whole chat message without modification"""
    # try to convert to JSON for passing payload to API
    user_message = None
    try:
        tool_input = json.loads(input_query)
        if tool_input.get("tool_name") == "db_data":
            user_message = tool_input.get("user_message")
    except Exception:
        pass

    if user_message:
        url = os.getenv("DB_TOOL_API")

        payload = json.dumps({"chatQuery": user_message})
        headers = {"Content-Type": "application/json"}

        response = requests.request("POST", url, headers=headers, data=payload)
        if response.status_code == 200:
            return response.json() | {"tool_used": True}

    return {"direct_response": input_query, "tool_used": False}


display_format_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Just detect whether user wants information in text or table and return JSON blob as 'output_format': 'text' or 'table'. For Example: 'give me tickets count' is text as output_format. 'give me tickets information' is table as output_format",
        ),
        ("user", "{input}"),
    ]
)
display_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Read data and return a sentence",
        ),
        ("user", "{input}"),
    ]
)
display_chain = display_prompt | llm | StrOutputParser()


def show_output(response):
    output_format = response.get("display_format", {}).get("output_format")
    output = response.get("output", {})
    tool_used = output.get("tool_used")
    if tool_used:
        if output_format == "table":
            return response.get("output")
        elif output_format == "text" and (output_data := output.get("data")):
            output = display_chain.invoke({"input": output_data})
            return output
        else:
            return output.get("data")
    return response.get("output").get("direct_response")


rendered_tools = render_text_description([db_data])
system_prompt = f"""You are a helpful Assistant for Customer Support Platform - `Quadz`. You may not need to use tools for every query - the user may just want to chat!. Here are the names and descriptions for each tool:

{rendered_tools}

Given the user input, return the name and user's message without modification for tool to use as a JSON blob with 'tool_name' and 'user_message' keys."""

output_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="history"),
        ("user", "{input}"),
    ]
)
tools = [db_data]

# Set up memory
chat_conversation = CustomStreamlitChatMessageHistory(key="chat_conversation")

output_chain = output_prompt | llm | CustomOutputParser() | db_data
output_chain_with_memory = RunnableWithMessageHistory(
    output_chain,
    lambda session_id: chat_conversation,
    input_messages_key="input",
    history_messages_key="history",
)
display_format_chain = display_format_prompt | llm | JsonOutputParser()
final_chain = (
    RunnableParallel(
        output=output_chain_with_memory, display_format=display_format_chain
    )
    | show_output
)


if len(chat_conversation.messages) == 0:
    chat_conversation.add_ai_message("How can I help you?")

for msg in chat_conversation.messages:
    if hasattr(msg, "type"):
        st.chat_message(msg.type).write(msg.content)
    elif isinstance(msg, (list, dict)):
        with st.chat_message("assistant"):
            st.dataframe(json.loads(msg.get("content")))

user_query = st.chat_input(placeholder="Your Quadz Personal Assistant!")

if user_query:
    chat_conversation.add_user_message(user_query)
    st.chat_message("user").write(user_query)

    config = {"configurable": {"session_id": "any"}}
    response = final_chain.invoke({"input": user_query}, config)
    if isinstance(response, str):
        chat_conversation.add_ai_message(response)
        st.chat_message("assistant").write(response)
    elif isinstance(response, (list, dict)):
        chat_conversation.add_message(response.get("data").get("df"))
        with st.chat_message("assistant"):
            st.dataframe(response.get("data").get("df"))
