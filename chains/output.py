import json
import pandas as pd

from typing import Union, List, Dict, Any

# from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI

from .nosql import create_nosql_query_chain
from .display import create_display_chain
from utilities.nosql_database import NoSQLDatabase
from utilities.json_util import nested_mongodb_to_dataframe
from config import MONGODB_URI, OPENAI_API_KEY, EXTERNAL_SCHEMA_API_ENDPOINT


def get_nosql_output(llm_output: str) -> Union[List[Any], Dict[str, Any]]:
    """
    Function to run the pymongo code in MongoDB
    """
    print("LLM OUTPUT", llm_output)

    def _convert_to_dict(string: str) -> dict:
        try:
            import datetime

            return eval(string)
        except Exception as e:
            print(f"Error while converting NoSQL LLM output: {e}. ")
            try:
                return json.loads(string)
            except Exception as e:
                print(f"Error with json.loads as well: {e}")

        return {}

    def _get_col_pipeline(llm_parsed_output: Union[Dict[str, str], str]) -> str:
        llm_json_output = _convert_to_dict(llm_parsed_output)
        if (
            isinstance(llm_json_output, dict)
            and (collection := llm_json_output.get("collection"))
            and (pipeline := llm_json_output.get("pipeline"))
        ):
            return (collection, pipeline)

        llm_parsed_output = (
            llm_parsed_output.replace("```python", "")
            .replace("```", "")
            .replace("\n", "")
            .strip()
        )
        llm_parsed_output = (
            llm_parsed_output.replace("PyMongoPipeline:", "")
            .replace("pipeline =", "")
            .strip()
        )

        collection = llm_parsed_output.split("MongoDBCollection: ")[-1]
        pipeline = _convert_to_dict(llm_parsed_output.split("MongoDBCollection: ")[0])
        if collection and pipeline:
            return (collection, pipeline)

    collection_name, pymongo_pipeline = _get_col_pipeline(llm_output)
    if not collection_name and not pymongo_pipeline:
        return pd.DataFrame()

    db = NoSQLDatabase.from_uri(MONGODB_URI)

    collection = db.get_collection(collection_name=collection_name)
    data = collection.aggregate(pipeline=pymongo_pipeline)

    df = nested_mongodb_to_dataframe(data)
    for col in df.columns:
        df.rename(columns={col: col.title().replace("_", " ")}, inplace=True)

    return df


def get_final_output(response: dict) -> str:

    def _tool_used(string: str) -> bool:
        try:
            string_json = json.loads(string)
            if (
                isinstance(string_json, dict)
                and string_json.get("tool_name") == "db_data"
            ):
                return True, string_json
        except:
            return False, {}

    output_format = response.get("display_format", {}).get("output_format")
    chain_output = response.get("output")

    tool_used, tool_data = _tool_used(chain_output)
    if tool_used:
        # chain to get the pymongo code to run in MongoDB
        llm = ChatOpenAI(
            model="gpt-4-turbo",
            temperature=0,
            openai_api_key=OPENAI_API_KEY,
        )
        db = NoSQLDatabase.from_uri(MONGODB_URI)
        nosql_query_chain = create_nosql_query_chain(llm, db)

        output_chain = nosql_query_chain | get_nosql_output
        output = output_chain.invoke(
            {
                "input": tool_data.get("user_message"),
                "use_external_uri": EXTERNAL_SCHEMA_API_ENDPOINT,
            }
        )

        if output_format == "table":
            return output
        elif output_format == "text":
            display_chain = create_display_chain()
            display_output = display_chain.invoke({"input": output})
            return display_output
        else:
            return output

    return response.get("output")  # .get("direct_response")
