from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


system_prompt = f"""You are a helpful Assistant for Customer Support Platform - `Quadz`. You may not need to use tools for every query - the user may just want to chat!. Here are the names and descriptions for each tool:

db_data tool: for fetching the data from the DB

Given the user input, return the tool name and user's message without modification for tool to use as a JSON blob with 'tool_name' and 'user_message' keys."""


CHAT_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="history"),
        ("user", "{input}"),
    ]
)
