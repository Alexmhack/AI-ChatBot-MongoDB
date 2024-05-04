# flake8: noqa
from langchain_core.prompts.prompt import PromptTemplate


PROMPT_SUFFIX = """Only use the following collections:
{collection_info}

Question: {input}"""

_DEFAULT_TEMPLATE = """Given an input question, first create a syntactically correct {dialect} query to run, then look at the results of the query and return the answer. Unless the user specifies in his question a specific number of examples he wishes to obtain, always limit your query to at most {top_k} results. You can order the results by a relevant column to return the most interesting examples in the database.

Never query for all the columns from a specific collection, only ask for a the few relevant columns given the question.

Pay attention to use only the column names that you can see in the schema description. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which collection.

Use the following format:

Question: Question here
NoSQLFilter: NoSQL Filter to run using pymongo
NoSQLResult: Result of the NoSQLCommand
Answer: Final answer here

"""

# default prompt to use for reference(but not required since mongodb prompt is only used)
PROMPT = PromptTemplate(
    input_variables=["input", "collection_info", "dialect", "top_k"],
    template=_DEFAULT_TEMPLATE + PROMPT_SUFFIX,
)

_mongod_prompt = """You are a MongoDB expert. Given an input question, first create a syntactically correct pymongo code to run, then look at the results of the query and return the answer to the input question.
Unless the user specifies in the question a specific number of examples to obtain, include .limit(10) method in pymongo pipeline, if user says to get all data then don't use .limit. You can order the results to return the most informative data in the database.
Never query for all columns from a collection. You must query only the columns that are needed to answer the question.
Use pymongo aggregate etc helpful methods wherever needed.
Pay attention to use only the column names you can see in the collections below. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which collection.
Pay attention to use $currentDate operator to get the current date, if the question involves "today".
Pay attention to use $dateSubtract etc operators to query with dates, don't use python code at all!.
Do not include any explanations, only provide a JSON object following this format without deviation.

{{"collection": value of MongoDBCollection to run pymongo pipeline, "pipeline": value of pymongo pipeline}}
JSON object:
"""

"""
PyMongoPipeline: pymongo pipeline to run
MongoDBCollection: MongoDB collection to run PyMongoPipeline
NoSQLResult: Result of the PyMongoPipeline
"""

MONGODB_PROMPT = PromptTemplate(
    input_variables=["input", "collection_info"],  # , "top_k" -> not needed
    template=_mongod_prompt + PROMPT_SUFFIX,
)

NOSQL_PROMPTS = {
    "mongodb": MONGODB_PROMPT,
}

COLLECTION_TO_USE_PROMPT_SUFFIX = """Here is the collections schema:
{collection_schema}

Question: {input}"""

_mongod_collection_to_use_prompt = """You are a MongoDB expert. Given an input question, first figure out the syntactically correct collections to use, then look at the collections schema of the query and return the answer to the input question.
Unless the user specifies in the question a specific collection to use, find the collections to use at most {top_k} results. You can check the collections schema to return the most accurate collection names from the database.
Never return all the collection names from a database. You must return only the collections that are needed to answer the question. Wrap each collection name in double quotes (") to denote them as delimited identifiers.
Pay attention to use only the collection names you can see in the collections schema. Be careful to not return any collections that do not exist.
Pay attention to use multiple collections names, if the question is complex.

Use the following format:

Question: Question here
MongoDBCollections: MongoDB Collections to use with pymongo.

"""

COLLECTION_TO_USE_PROMPT = PromptTemplate(
    input_variables=["input", "top_k", "collection_schema"],
    template=_mongod_collection_to_use_prompt + COLLECTION_TO_USE_PROMPT_SUFFIX,
)

QUERY_CHECKER = """
{query}
Double check the query above for common mistakes in MongoDB operations, including:
- Properly constructing the query document
- Correctly using operators like $gt, $lt, $gte, $lte, etc.
- Using appropriate indexes for query optimization
- Ensuring consistency in field names and values
- Avoiding common pitfalls like using $in with large arrays
- Properly handling null values or missing fields
- Ensuring efficient aggregation pipeline stages, if applicable

If there are any mistakes or optimizations needed, revise the query. If the query is correct, reproduce it.

MongoDB Query: """

QUERY_CHECKER_PROMPT = PromptTemplate(
    input_variables=["query"],
    template=QUERY_CHECKER,
)
