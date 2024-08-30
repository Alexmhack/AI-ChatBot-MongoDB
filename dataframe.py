import json
import streamlit as st
import pandas as pd

from dotenv import load_dotenv
from pymongo import MongoClient
from utilities.history import CustomStreamlitChatMessageHistory

load_dotenv()

client = MongoClient("mongodb://localhost:27017/quadzcstest")

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

# Set up memory
chat_conversation = CustomStreamlitChatMessageHistory(key="chat_conversation")

if len(chat_conversation.messages) == 0:
    chat_conversation.add_ai_message("How can I help you?")

for msg in chat_conversation.messages:
    if hasattr(msg, "type"):
        st.chat_message(msg.type).write(msg.content)
    elif isinstance(msg, (list, dict)):
        with st.chat_message("assistant"):
            st.dataframe(json.loads(msg.get("content")))

user_query = st.chat_input(placeholder="Your Quadz Personal Assistant!")

if st.sidebar.button("Clear Conversation"):
    print("BUTTON CLICKED....")


def flatten_dict(d, parent_key="", sep="_"):
    """
    Flatten a nested dictionary.

    Parameters:
    - d: Dictionary to be flattened.
    - parent_key: String representing the current parent key.
    - sep: Separator to use when creating keys for nested dictionaries.

    Returns:
    - Flattened dictionary.
    """
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + str(k) if parent_key else str(k)
        if isinstance(v, dict):
            items.extend(flatten_dict(v, str(new_key), sep=sep).items())
        elif isinstance(v, list):
            for i in v:
                if isinstance(i, dict):
                    items.extend(flatten_dict(i, str(new_key), sep=sep).items())
                elif "__v" in str(new_key):
                    continue
                else:
                    items.append((str(new_key), i))
        elif "__v" in str(new_key):
            continue
        else:
            items.append((str(new_key), v))
    return dict(items)


def nested_mongodb_to_dataframe(results):
    """
    Convert nested MongoDB results into a pandas DataFrame.

    Parameters:
    - results: List of MongoDB documents (dictionaries) with nested structures.

    Returns:
    - Pandas DataFrame containing flattened MongoDB documents.
    """
    flattened_results = [flatten_dict(doc) for doc in results]

    df = pd.DataFrame.from_dict(flattened_results, orient="columns")
    df.index += 1
    return df


if user_query:
    chat_conversation.add_user_message(user_query)
    st.chat_message("user").write(user_query)

    config = {"configurable": {"session_id": "any"}}
    db = client["quadzcstest"]
    tickets_data = db.tickets.aggregate(
        [
            {
                "$lookup": {
                    "from": "ticketstats",
                    "localField": "stats",
                    "foreignField": "_id",
                    "as": "ticketStats",
                }
            },
            {"$match": {"ticketStats.customerSentiment": {"$lt": 0}}},
            {"$project": {"_id": 1, "subject": 1, "date": 1, "ticketStats": 1}},
        ]
    )

    df = nested_mongodb_to_dataframe(tickets_data)
    st.dataframe(df)

    customers_data = db.accounts.find(
        {},
        {
            "username": 1,
            "fullname": 1,
            "email": 1,
            "phoneNumber": 1,
            "addressone": 1,
            "addresstwo": 1,
        },
    )
    df = nested_mongodb_to_dataframe(customers_data)
    st.dataframe(df)

    pipeline = [
        {
            "$lookup": {
                "from": "accounts",
                "localField": "owner",
                "foreignField": "_id",
                "as": "owner_info",
            }
        },
        {"$unwind": "$owner_info"},
        {
            "$lookup": {
                "from": "groups",
                "localField": "group",
                "foreignField": "_id",
                "as": "group_info",
            }
        },
        {"$unwind": "$group_info"},
        {
            "$lookup": {
                "from": "tickettypes",
                "localField": "type",
                "foreignField": "_id",
                "as": "type_info",
            }
        },
        {"$unwind": "$type_info"},
        {
            "$lookup": {
                "from": "statuses",
                "localField": "status",
                "foreignField": "_id",
                "as": "status_info",
            }
        },
        {"$unwind": "$status_info"},
        {
            "$project": {
                "subject": 1,
                "date": 1,
                "id": "$uid",
                "owner_info": {"fullname": 1, "email": 1},
                "group_info": {"name": 1},
                "type_info": {"name": 1},
                "status_info": {"name": 1},
            }
        },
    ]
    tickets_data = db.tickets.aggregate(pipeline)
    df = nested_mongodb_to_dataframe(tickets_data)

    for col in df.columns:
        df.rename(columns={col: col.title().replace("_", " ")}, inplace=True)

    st.dataframe(df)

    tickets_count = db.tickets.aggregate([{"$count": "total_tickets"}])
    df = nested_mongodb_to_dataframe(tickets_count)
    st.dataframe(df)

    pipeline = [
        {
            "$lookup": {
                "from": "ticketstats",
                "localField": "stats",
                "foreignField": "_id",
                "as": "stats",
            }
        },
        {"$match": {"stats.customerSentiment": {"$lt": 0}}},
        {"$project": {"subject": 1, "date": 1, "uid": 1, "stats": 1}},
        {"$limit": 5},
    ]
    data = db.tickets.aggregate(pipeline)
    df = nested_mongodb_to_dataframe(data)
    for col in df.columns:
        df.rename(columns={col: col.title().replace("_", " ")}, inplace=True)

    st.dataframe(df)

    st.chat_message("assistant").write("Final DF")

    pipeline = [
        {
            "$match": {
                "date": {
                    "$gte": {
                        "$dateSubtract": {
                            "startDate": "$$NOW",
                            "unit": "month",
                            "amount": 1,
                        }
                    }
                }
            }
        },
        {"$project": {"_id": 0, "uid": 1, "subject": 1, "date": 1}},
        {"$limit": 5},
    ]
    data = db.tickets.aggregate(pipeline)
    df = nested_mongodb_to_dataframe(data)
    for col in df.columns:
        df.rename(columns={col: col.title().replace("_", " ")}, inplace=True)

    st.dataframe(df)

    pipeline = [
        {"$match": {"stats.customerSentiment": {"$lt": 0}}},
        {"$project": {"subject": 1, "date": 1, "_id": 1, "uid": 1}},
        {"$limit": 10},
    ]
    data = db.tickets.aggregate(pipeline)
    df = nested_mongodb_to_dataframe(data)
    for col in df.columns:
        df.rename(columns={col: col.title().replace("_", " ")}, inplace=True)

    st.dataframe(df)
