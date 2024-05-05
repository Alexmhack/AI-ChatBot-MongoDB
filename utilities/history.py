import json
import pandas as pd

from typing import List, Dict, Any, Sequence, Union
from pathlib import Path

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import (
    BaseMessage,
    AIMessage,
    HumanMessage,
    _message_from_dict,
)

from .generic import create_id
from .session import get_current_session_dir


def __message_from_dict(message: dict) -> BaseMessage:
    _message_data = message["data"]
    if isinstance(_message_data, dict) and _message_data.get("message_type") == "json":
        return {"content": _message_data["content"], "role": "assistant"}

    return _message_from_dict(message)


def messages_from_dict(messages: Sequence[dict]) -> List[BaseMessage]:
    """Convert a sequence of messages from dicts to Message objects.

    Args:
        messages: Sequence of messages (as dicts) to convert.

    Returns:
        List of messages (BaseMessages).
    """
    return [__message_from_dict(m) for m in messages]


def message_to_dict(message: BaseMessage) -> dict:
    """Convert a Message to a dictionary.

    Args:
        message: Message to convert.

    Returns:
        Message as a dict.
    """
    if hasattr(message, "type"):
        return {"type": message.type, "data": message.dict()}
    else:
        message.update({"message_type": "json"})
        return {"type": "ai", "data": message}


def messages_to_dict(messages: Sequence[BaseMessage]) -> List[dict]:
    """Convert a sequence of Messages to a list of dictionaries.

    Args:
        messages: Sequence of messages (as BaseMessages) to convert.

    Returns:
        List of messages as dicts.
    """
    return [message_to_dict(m) for m in messages]


# NOT IN USE
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


# IN USE
class FileChatMessageHistory(BaseChatMessageHistory):
    CURRENT_SESSION_DIR: Path
    CURRENT_SESSION_HISTORY: Path
    CURRENT_SESSION_JSON_HISTORY: Path

    session_id: str

    def __init__(self, session_id: str) -> None:
        super().__init__()

        self.session_id = session_id

        # Create current session dir and history file if not exists
        CURRENT_SESSION_DIR: Path = get_current_session_dir(session_id)

        self.CURRENT_SESSION_DIR = CURRENT_SESSION_DIR
        self.CURRENT_SESSION_HISTORY = CURRENT_SESSION_DIR / "history.json"
        self.CURRENT_SESSION_JSON_HISTORY = CURRENT_SESSION_DIR / "json_history.json"

    @property
    def messages(self):
        messages = []
        if self.CURRENT_SESSION_HISTORY.exists():
            with open(self.CURRENT_SESSION_HISTORY) as f:
                try:
                    messages = json.load(f)
                except Exception as e:
                    print(
                        "Error loading message history for session",
                        self.session_id,
                        "Error:",
                        e,
                    )

        return messages_from_dict(messages)

    @property
    def json_messages(self) -> List[BaseMessage]:
        """Retrieve the current list of JSON messages"""
        json_messages = {}
        if self.CURRENT_SESSION_JSON_HISTORY.exists():
            with open(self.CURRENT_SESSION_JSON_HISTORY) as f:
                try:
                    json_messages = json.load(f)
                    for _json_id, _json in json_messages.items():
                        if isinstance(_json, (list, dict)):
                            json_messages[_json_id] = _json
                        else:
                            json_messages[_json_id] = json.loads(_json)

                except Exception as e:
                    print(
                        "Error loading message history for session",
                        self.session_id,
                        "Error:",
                        e,
                    )
        return json_messages

    def add_messages(self, messages: Sequence[BaseMessage]) -> None:
        all_messages = self.messages  # Existing text messages
        _json_messages = self.json_messages  # Existing json messages

        ## Separate text & json messages
        message: Union[AIMessage, HumanMessage, pd.DataFrame]
        for message in messages:
            if isinstance(message, pd.DataFrame):
                _json_message_id = create_id()
                _json_messages.setdefault(_json_message_id, {})
                _json_messages[_json_message_id] = message.to_json(
                    orient="records", default_handler=str, date_format="iso"
                )  # assume message is pd.DataFrame
                all_messages.append(
                    {
                        "role": "assistant",
                        "message_type": "json",
                        "content": _json_message_id,
                    }
                )
            # NOTE: hack to find the tool call from LLM
            # TODO: fix inside runnable with history
            elif "tool_name" in message.content and "db_data" in message.content:
                continue
            else:
                all_messages.append(message)

        serialized = messages_to_dict(all_messages)

        ## Store text messages in file
        # TODO: Further optimized by only writing new messages using append mode.
        with open(self.CURRENT_SESSION_HISTORY, "w") as f:
            json.dump(serialized, f)

        ## Store json messages in file
        with open(self.CURRENT_SESSION_JSON_HISTORY, "w") as f:
            json.dump(_json_messages, f)

    def clear(self):
        with open(self.CURRENT_SESSION_HISTORY, "w") as f:
            json.dump([], f)
        with open(self.CURRENT_SESSION_JSON_HISTORY, "w") as f:
            json.dump({}, f)


def get_session_history_by_id(
    session_id: str,
) -> Union[FileChatMessageHistory, CustomStreamlitChatMessageHistory]:
    """Returns the message history class in use considering the session id"""
    return FileChatMessageHistory(session_id)
