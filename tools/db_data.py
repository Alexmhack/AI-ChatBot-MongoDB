import json
import requests

from langchain_core.tools import tool

from config import DB_TOOL_API


@tool
def db_data(input_query: str) -> list:
    """Returns DB data by taking whole chat message without modification"""
    # try to convert to JSON for passing payload to API
    user_message = None
    try:
        tool_input = json.loads(input_query)
        if tool_input.get("tool_name") == "db_data":
            user_message = tool_input.get("user_message")
    except Exception:
        pass

    if user_message:
        url = DB_TOOL_API
        payload = json.dumps({"chatQuery": user_message})
        headers = {"Content-Type": "application/json"}

        response = requests.request("POST", url, headers=headers, data=payload)
        if response.status_code == 200:
            return response.json() | {"tool_used": True}

    return {"direct_response": input_query, "tool_used": False}
