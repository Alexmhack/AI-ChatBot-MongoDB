from langchain_core.prompts import ChatPromptTemplate


DISPLAY_FORMAT_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Just detect whether user wants information in text or table and return JSON blob as 'output_format': 'text' or 'table'. For Example: 'give me tickets count' is text as output_format. 'give me tickets information' is table as output_format",
        ),
        ("user", "{input}"),
    ]
)

DISPLAY_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Read data and return a sentence",
        ),
        ("user", "{input}"),
    ]
)
