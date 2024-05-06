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
            "Read data and return a sentence. For example for a prompt: 'how many tickets have negative sentiment?', if the data has only one entry then respond with: 'There is only 1 ticket with id: <ticket_id> which has negative sentiment.",
        ),
        ("user", "{input}"),
    ]
)
