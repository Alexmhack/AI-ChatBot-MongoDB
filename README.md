# QuadzAIBot
AI Chatbot for the Quadz Customer Support Platform built using Streamlit, Langchain &amp; OpenAI

## Setup
*NOTE: Instructions for Ubuntu 22*

1. Install `poetry` globally using [`pipx`](https://github.com/pypa/pipx)
    `pipx install poetry`
2. Create *.env* file by taking reference from *.env.example* and based upon your Database usecase, following the below sections for updating your .env with DB credentials.

### NoSQL Database

1. For NoSQL Database, branch name is *main*(default branch)
2. Change your working directory to the root of this repo and run,
    `poetry install`
3. In your *.env*, add your MongoDB credentials.
4. simply comment out `MONDODB_REPLICA_SET_NAME` environment variable since it is not required for local or development run.


### SQL Database
1. For SQL Database, branch name is *sql* -> `git checkout sql`
2. Install and run the SQL Query API as well using,
    - [NLPReporting](https://github.com/ARThink-AI/NLPReporting/tree/dev) Repo and `dev` branch.
    - Follow the README available in *SQLQueryAPI* folder to run
    - API available at http://localhost:8000
3. In your *.env*, use `http://localhost:8000/SQL/query` as the value for `DB_TOOL_API` environment variable.
3. Change your working directory to the root of this repo and run,
    `poetry install`

## Run Locally

`make run-app`

**NOTE: For SQL Database usecase, make sure that SQL Query API is also running by following the above Setup Steps for SQL Database.**

There are few other useful commands that are listed in the *Makefile*.

1. `make run-app` for running the Chatbot App locally
2. `make build` for building the Docker Image
3. `make run-docker` for running the Docker Container. Access the Chatbot App at [http://localhost:8501](http://localhost:8501)

## Deployment

1. `make build` for building the Docker image
2. `make run-docker` for running the Docker container and map your Nginx/Apache to point at [http://localhost:8501](http://localhost:8501).

## Issues with SQL DB Usecase

OpenAI models used in [NLPReporting](https://github.com/ARThink-AI/NLPReporting/tree/dev) Repo for SQL Query API use the GPT Legacy APIs which allows max token length in context of around 4K tokens which can be an issue if your SQL Database schema text consumes more than this context length. Possible solutions,

1. Replace the Model used in NLPReporting -> *SQLQueryAPI* -> *src/services/sqllangchain_service.py* from default to the OpenAI Chat Completions Models(*gpt-3.5-turbo*, *gpt-4-turbo*) which have larger context length.
2. Change the prompt passed to these models to return only the SQL query and not the description too. Below is an example of MongoDB prompt to *gpt-4-turbo* model

    Main sentence in the prompt is **Do not include any explanations, only provide a JSON object following this format without deviation.**
    ```
    _mongod_prompt = """You are a MongoDB expert. Given an input question, first create a syntactically correct pymongo code to run, then look at the results of the query and return the answer to the input question.
    Unless the user specifies in the question a specific number of examples to obtain, include .limit(10) method in pymongo pipeline, if user says to get all data then don't use .limit. You can order the results to return the most informative data in the database.
    Never query for all columns from a collection. You must query only the columns that are needed to answer the question.
    Use pymongo aggregate etc helpful methods wherever needed.
    Pay attention to following points,
    - Use only the column names you can see in the collections below. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which collection.
    - Todays date & time is {current_date}. If user query involves date then always use python's datetime module. Don't use ISODate or any other MongoDB Date Operator.
    - Use $lookup when referencing other collections.
    - MongoDB Operators should be suffixed with $ strictly.
    - Do not include any explanations, only provide a JSON object following this format without deviation.

    {{"collection": value of MongoDBCollection to run pymongo pipeline, "pipeline": value of pymongo pipeline}}
    JSON object:
    """
    ```
