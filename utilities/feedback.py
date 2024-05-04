from typing import Union

import json
import streamlit as st
import pandas as pd

from config import SESSIONS_DIR


def submit_feedback(user_response, emoji=None, **kwargs):
    """
    Called when streamlit feedback component is submitted.
    Stores feedback in a JSON file for now
    TODO: Store feedbacks in DB / Langsmith
    """
    session_id = kwargs.get("session_id")

    ai_message: Union[str, dict, pd.DataFrame] = kwargs.pop("ai_message")
    if isinstance(ai_message, pd.DataFrame):
        ai_message = ai_message.to_string()

    feedback_dump = {**kwargs, "user_feedback": user_response, "ai_message": ai_message}

    CURRENT_SESSION_DIR = SESSIONS_DIR / session_id
    CURRENT_SESSION_DIR.mkdir(parents=True, exist_ok=True)
    # store feedbacks
    FEEDBACK_FILE = CURRENT_SESSION_DIR / "feedback.json"

    # read existing feedbacks if any for current session
    if FEEDBACK_FILE.is_file():
        with open(FEEDBACK_FILE) as f:
            existing_feedbacks = json.load(f)
        # add new feedback
        with open(FEEDBACK_FILE, "w") as f:
            existing_feedbacks.append(feedback_dump)
            json.dump(existing_feedbacks, f)
    # else write the first feedback for current session
    else:
        with open(FEEDBACK_FILE, "w") as f:
            json.dump([feedback_dump], f)

    st.toast(f"Feedback submitted", icon=emoji)
    return user_response.update({"some metadata": 123})
