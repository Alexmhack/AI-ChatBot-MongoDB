import inspect
from typing import List, Dict, Any, Sequence

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage

from utilities import create_id


class CustomStreamlitChatMessageHistory(BaseChatMessageHistory):
    """
    Chat message history that stores messages in Streamlit session state.

    Args:
        key: The key to use in Streamlit session state for storing messages.
    """

    def __init__(
        self, key: str = "langchain_messages", json_key: str = "jsons_messages"
    ):
        try:
            import streamlit as st
        except ImportError as e:
            raise ImportError(
                "Unable to import streamlit, please run `pip install streamlit`."
            ) from e

        if key not in st.session_state:
            st.session_state[key] = []
        if json_key not in st.session_state:
            st.session_state[json_key] = {}

        self._messages = st.session_state[key]
        self._json_messages: Dict[str, Any] = st.session_state[json_key]

        self._json_key = json_key
        self._key = key

    @property
    def json_messages(self) -> List[BaseMessage]:
        """Retrieve the current list of JSON messages"""
        return self._json_messages

    @property
    def messages(self) -> List[BaseMessage]:
        """Retrieve the current list of messages"""
        return self._messages

    @messages.setter
    def messages(self, value: List[BaseMessage]) -> None:
        """Set the messages list with a new value"""
        import streamlit as st

        st.session_state[self._key] = value
        self._messages = list(
            filter(
                lambda msg: True if hasattr(msg, "type") else False,
                st.session_state[self._key],
            ),
        )

    @json_messages.setter
    def json_messages(self, value: List[BaseMessage]) -> None:
        """Set the json messages list with a new value"""
        import streamlit as st

        st.session_state[self._json_key] = value
        self._json_messages = st.session_state[self._json_key]

    def add_messages(self, messages: Sequence[BaseMessage]) -> None:
        """Add messages to the session memory"""
        all_messages = list(self.messages)  # Existing messages
        for message in messages:
            if not hasattr(message, "type"):
                _json_message_id = create_id()
                self._json_messages.setdefault(_json_message_id, {})
                self._json_messages[_json_message_id] = message
                all_messages.append({"role": "assistant", "content": _json_message_id})
            else:
                all_messages.append(message)

        self.messages = all_messages

    def clear(self) -> None:
        """Clear session memory"""
        self.messages.clear()
        self._json_messages.clear()
