from langchain_core.output_parsers import (
    StrOutputParser,
)
from langchain_openai import ChatOpenAI

from prompts.display import DISPLAY_PROMPT
from config import OPENAI_API_KEY


def create_display_chain():
    llm = ChatOpenAI(
        model="gpt-4-turbo",
        openai_api_key=OPENAI_API_KEY,
        temperature=0,
        streaming=True,
    )

    display_chain = DISPLAY_PROMPT | llm | StrOutputParser()
    return display_chain
