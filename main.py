import streamlit as st
import pandas as pd

from streamlit_feedback import streamlit_feedback

from chains.st import create_st_nosql_query_chain
from utilities import create_id, submit_feedback, CustomStreamlitChatMessageHistory
from config import EXTERNAL_SCHEMA_API_ENDPOINT


## Setup current streamlit session
if "session_id" not in st.session_state:
    session_id = create_id()
    st.session_state["session_id"] = session_id
else:
    session_id = st.session_state["session_id"]


## Setting the page config for streamlit UI
st.set_page_config(
    page_title="Quadz AI Bot",
    page_icon="🦜",
    layout="wide",
    menu_items={
        "Get Help": "https://quadz.arthink.ai",
        "Report a bug": "https://quadz.arthink.ai",
        "About": "Quadz AI Agent [BETA]",
    },
    initial_sidebar_state="collapsed",
)
st.title("Quadz AI Bot")

## Set up memory
chat_conversation = CustomStreamlitChatMessageHistory(key="chat_conversation")

## Setup LLM chain
chain = create_st_nosql_query_chain(chat_conversation=chat_conversation)

## Clear conversation history button
if st.sidebar.button("Clear Conversation"):
    chat_conversation.clear()
    st.success("Conversation Cleared!")

# Add first message when page loads
if len(chat_conversation.messages) == 0:
    chat_conversation.add_ai_message("How can I help you?")


for n, msg in enumerate(chat_conversation.messages):
    type_message = hasattr(msg, "type")
    json_message = isinstance(msg, (list, dict))

    if type_message:
        st.chat_message(msg.type).write(msg.content)
    elif json_message:
        with st.chat_message("assistant"):
            st.dataframe(chat_conversation.json_messages.get(msg.get("content")))

    # Feedback thumbs for AI Message
    if ((type_message and msg.type == "ai") or (json_message)) and n > 0:
        feedback_key = f"feedback_{int(n/2)}"

        if feedback_key not in st.session_state:
            st.session_state[feedback_key] = None

        feedback_kwargs = {
            "feedback_type": "thumbs",
            "optional_text_label": "(Optional) Please provide extra information",
            "on_submit": submit_feedback,
            "args": ["✅"],
            "kwargs": (
                {
                    "feedback_key": feedback_key,
                    "session_id": session_id,
                    "ai_message": (
                        msg.content
                        if type_message
                        else (
                            chat_conversation.json_messages.get(msg.get("content"))
                            if json_message
                            else None
                        )
                    ),
                }
            ),
        }
        disable_with_score = (
            st.session_state[feedback_key].get("score")
            if st.session_state[feedback_key]
            else None
        )
        streamlit_feedback(
            **feedback_kwargs,
            key=feedback_key,
            disable_with_score=disable_with_score,
        )

## chat input
user_query = st.chat_input(placeholder="Your Quadz Personal Assistant!")

if user_query:
    chat_conversation.add_user_message(user_query)
    st.chat_message("user").write(user_query)

    config = {"configurable": {"session_id": session_id}}
    # actual LLM usage
    response = chain.invoke(
        {"input": user_query, "use_external_uri": EXTERNAL_SCHEMA_API_ENDPOINT},
        config,
    )

    if isinstance(response, str):
        chat_conversation.add_ai_message(response)
        st.chat_message("assistant").write(response)
    elif isinstance(response, (list, dict, pd.DataFrame)):
        chat_conversation.add_message(response)
        with st.chat_message("assistant"):
            st.dataframe(response)
    st.rerun()  # for showing the feedback thumbs after AI message
