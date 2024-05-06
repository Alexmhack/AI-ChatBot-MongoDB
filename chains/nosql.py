import os

from typing import Optional, Any, Dict
from datetime import datetime
from langchain_core.language_models import BaseLanguageModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import BasePromptTemplate
from langchain_core.runnables import Runnable, RunnablePassthrough

from utilities.nosql_database import NoSQLDatabase
from prompts.nosql import PROMPT, NOSQL_PROMPTS, COLLECTION_TO_USE_PROMPT


def create_nosql_query_chain(
    llm: BaseLanguageModel,
    db: NoSQLDatabase,
    prompt: Optional[BasePromptTemplate] = None,
    k: int = 5,
) -> Runnable[Dict[str, Any], str]:
    """Create a chain that generates NoSQL queries.

    *Security Note*: This chain generates NoSQL queries for the given database.

        The NoSQLDatabase class provides methods to retrieve information about
        the available collections and their structure.

        To mitigate risk of leaking sensitive data, limit permissions
        to read and scope to the collections that are needed.

        Control access to who can submit requests to this chain.

        See https://python.langchain.com/docs/security for more information.

    Args:
        llm: The language model to use.
        db: The NoSQLDatabase to generate the query for.
        prompt: The prompt to use. If none is provided, will choose one
            based on the database. Defaults to None. See Prompt section below for more.
        k: The number of results per query to return. Defaults to 5.

    Returns:
        A chain that takes in a question and generates a NoSQL query that answers
        that question.

    Example:

        .. code-block:: python

            # pip install -U langchain langchain-community langchain-openai
            from langchain_openai import ChatOpenAI
            from langchain.chains import create_nosql_query_chain
            from langchain_community.utilities import NoSQLDatabase

            db = NoSQLDatabase.from_uri("mongodb://localhost:27017/")
            llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
            chain = create_nosql_query_chain(llm, db)
            response = chain.invoke({"question": "Find all documents in the 'users' collection"})

    Prompt:
        If no prompt is provided, a default prompt is selected based on the NoSQLDatabase. If one is provided, it must support input variables:
            * input: The user question plus suffix "\nCommand: " is passed here.
            * top_k: The number of results per query (the `k` argument to
                this function) is passed in here.
            * collections_info: Collection definitions and sample documents are passed in here.

        Here's an example prompt:

        .. code-block:: python

            from langchain_core.prompts import PromptTemplate

            template = '''Given an input question, create a command to run, then look at the results of the command and return the answer.
            Use the following format:

            Question: "Question here"
            Command: "Command to run"
            Result: "Result of the Command"
            Answer: "Final answer here"

            Only use the following collections:

            {collections_info}.

            Question: {input}'''
            prompt = PromptTemplate.from_template(template)
    """  # noqa: E501

    def _strip(text: str) -> str:
        return text.strip()

    if prompt is not None:
        prompt_to_use = prompt
    elif db.dialect in NOSQL_PROMPTS:
        prompt_to_use = NOSQL_PROMPTS[db.dialect]
    else:
        prompt_to_use = PROMPT
    if {"input", "collection_info"}.difference(
        prompt_to_use.input_variables
    ):  # "top_k",
        raise ValueError(
            f"Prompt must have input variables: 'input', 'top_k', "
            f"'collection_info'. Received prompt with input variables: "
            f"{prompt_to_use.input_variables}. Full prompt:\n\n{prompt_to_use}"
        )

    # the acutal query chain which returns the query
    inputs = {
        "input": lambda x: f"{x['input']}\nNOTE: Include tickets collection data(subject, date, id, uuid) using aggregation only if tickets is related to the collection in use(otherwise strictly don't), include the rest of the collection info as well.",
        "collection_info": lambda x: db.get_collection_info(
            use_external_uri=x.get("use_external_uri", False),
        ),
    }
    return (
        RunnablePassthrough.assign(**inputs)
        | prompt_to_use.partial(current_date=datetime.now().strftime("%Y-%m-%d %H:%M"))
        | llm.bind(stop=["\nJSON object:"])
        | StrOutputParser()
        | _strip
    )


def create_collections_to_use_chain(
    llm: BaseLanguageModel,
    db: NoSQLDatabase,
    collections_to_use_prompt: Optional[BasePromptTemplate] = None,
    k: int = 5,
) -> Runnable[Dict[str, Any], str]:
    """Create a chain that generates NoSQL queries.

    *Security Note*: This chain generates NoSQL queries for the given database.

        The NoSQLDatabase class provides methods to retrieve information about
        the available collections and their structure.

        To mitigate risk of leaking sensitive data, limit permissions
        to read and scope to the collections that are needed.

        Control access to who can submit requests to this chain.

        See https://python.langchain.com/docs/security for more information.

    Args:
        llm: The language model to use.
        db: The NoSQLDatabase to generate the query for.
        prompt: The prompt to use. If none is provided, will choose one
            based on the database. Defaults to None. See Prompt section below for more.
        k: The number of results per query to return. Defaults to 5.

    Returns:
        A chain that takes in a question and generates a NoSQL query that answers
        that question.

    Example:

        .. code-block:: python

            # pip install -U langchain langchain-community langchain-openai
            from langchain_openai import ChatOpenAI
            from langchain.chains import create_nosql_query_chain
            from langchain_community.utilities import NoSQLDatabase

            db = NoSQLDatabase.from_uri("mongodb://localhost:27017/")
            llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
            chain = create_nosql_query_chain(llm, db)
            response = chain.invoke({"question": "Find all documents in the 'users' collection"})

    Prompt:
        If no prompt is provided, a default prompt is selected based on the NoSQLDatabase. If one is provided, it must support input variables:
            * input: The user question plus suffix "\nCommand: " is passed here.
            * top_k: The number of results per query (the `k` argument to
                this function) is passed in here.
            * collections_info: Collection definitions and sample documents are passed in here.

        Here's an example prompt:

        .. code-block:: python

            from langchain_core.prompts import PromptTemplate

            template = '''Given an input question, create a command to run, then look at the results of the command and return the answer.
            Use the following format:

            Question: "Question here"
            Command: "Command to run"
            Result: "Result of the Command"
            Answer: "Final answer here"

            Only use the following collections:

            {collections_info}.

            Question: {input}'''
            prompt = PromptTemplate.from_template(template)
    """  # noqa: E501

    def _strip(text: str) -> str:
        return text.strip()

    if collections_to_use_prompt is not None:
        collections_to_use_prompt = collections_to_use_prompt
    else:
        collections_to_use_prompt = COLLECTION_TO_USE_PROMPT
    if {"input", "top_k", "collection_schema"}.difference(
        collections_to_use_prompt.input_variables
    ):
        raise ValueError(
            f"Prompt must have input variables: 'input', 'top_k', "
            f"'collection_schema'. Received prompt with input variables: "
            f"{collections_to_use_prompt.input_variables}. Full prompt:\n\n{collections_to_use_prompt}"
        )

    # the acutal query chain which returns the query
    CUSTOM_INPUT_SUFFIX = "show tickets with negative sentiment are there? NOTE: Include tickets data using aggregation wherever possible like ticket's subject, date, id including the rest of the collection info"
    inputs = {
        "input": lambda x: x["input"] + CUSTOM_INPUT_SUFFIX + "\nCommand: ",
        "collection_schema": lambda x: db.get_external_mongoose_schema(
            os.getenv("EXTERNAL_SCHEMA_API_ENDPOINT")
        ),
    }
    return (
        RunnablePassthrough.assign(**inputs)
        | collections_to_use_prompt.partial(top_k=str(k))
        | llm.bind(stop=["\nAnswer:"])
        | StrOutputParser()
        | _strip
    )
