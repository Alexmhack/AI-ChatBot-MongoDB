import streamlit as st

from typing import TYPE_CHECKING

from .generic import create_st_session_id
from config import SESSIONS_DIR

if TYPE_CHECKING:
    from pathlib import Path


def get_current_session_dir(session_id: str) -> "Path":
    """
    Creates current session dir if not exists and returns it
    """
    CURRENT_SESSION_DIR = SESSIONS_DIR / session_id
    CURRENT_SESSION_DIR.mkdir(parents=True, exist_ok=True)
    return CURRENT_SESSION_DIR


def get_current_session_id() -> str:
    """
    Fetch or create current session id using file storage and returns the session id
    """
    if "session_id" not in st.session_state:
        session_id: str = st.query_params.get("session_id", create_st_session_id())
        st.session_state["session_id"] = session_id
    else:
        session_id = st.session_state["session_id"]

    # Create dir for current session, for storing message history and feedbacks
    get_current_session_dir(session_id)

    return session_id
