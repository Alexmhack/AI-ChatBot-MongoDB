from typing import Dict, Any, Optional

from langchain_openai import ChatOpenAI
from langchain_core.runnables import Runnable
from langchain_core.output_parsers import (
    JsonOutputParser,
)
from langchain_core.runnables import (
    RunnableParallel,
)
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory

from .output import get_final_output
from prompts.display import DISPLAY_FORMAT_PROMPT
from prompts.chat import CHAT_PROMPT
from utilities.parser import CustomOutputParser
from config import OPENAI_API_KEY


def create_st_nosql_query_chain(
    chat_conversation: BaseChatMessageHistory,
    model_name: Optional[str] = "gpt-4-turbo",
) -> Runnable[Dict[str, Any], str]:
    llm = ChatOpenAI(
        model=model_name,
        temperature=0,
        openai_api_key=OPENAI_API_KEY,
    )

    # chain to get the results from MongoDB
    chat_chain = CHAT_PROMPT | llm | CustomOutputParser()
    chat_chain_with_memory = RunnableWithMessageHistory(
        chat_chain,
        lambda session_id: chat_conversation,
        input_messages_key="input",
        history_messages_key="history",
    )

    # chain to get the display format according to the user's message
    display_format_chain = DISPLAY_FORMAT_PROMPT | llm | JsonOutputParser()
    final_chain = (
        RunnableParallel(
            output=chat_chain_with_memory, display_format=display_format_chain
        )
        | get_final_output
    )

    return final_chain
